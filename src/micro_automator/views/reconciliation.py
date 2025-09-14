import os
import json
import io
import logging
from datetime import datetime
import google.generativeai as genai
from flask import Blueprint, request, jsonify
import fitz  # PyMuPDF for PDF parsing

from ..extensions import db
from ..models.reconciliation import ReconciliationBatch, Transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

reconciliation_bp = Blueprint('reconciliation', __name__)

def parse_pdf_statement(file_stream, source_name):
    """
    Extracts transaction data from a PDF using PyMuPDF for text extraction and Gemini AI for data structuring.
    This is a more robust method that does not rely on perfect table structures in the PDF.
    """
    try:
        # Read the entire file stream into bytes to make it reusable
        file_bytes = file_stream.read()
        
        # Step 1: Extract all raw text from the PDF using PyMuPDF
        raw_text = ""
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                raw_text += page.get_text()

        if not raw_text.strip():
            logger.warning(f"No text could be extracted from the {source_name} PDF.")
            return []

        # Step 2: Send the raw text to Gemini AI for intelligent data extraction
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        Act as an expert data entry clerk specializing in financial documents.
        Analyze the following raw text extracted from a '{source_name}' and identify all financial transaction entries.

        For each transaction, extract the following fields:
        1.  `transaction_date`: The date of the transaction. You MUST format it as YYYY-MM-DD.
        2.  `amount`: The numerical value of the transaction.
        3.  `reference_id`: Any unique identifier, policy number, or reference code. If none is found, use null.
        4.  `description`: A brief description of the transaction.

        Return your findings ONLY as a single, valid JSON array of objects. Each object represents one transaction.
        If no transactions are found in the text, return an empty array `[]`. Do not add any commentary or explanations.

        EXAMPLE RESPONSE:
        [
          {{
            "transaction_date": "2024-08-15",
            "amount": 5250.00,
            "reference_id": "POL-987654",
            "description": "Premium Payment - A. Kumar"
          }}
        ]

        Here is the raw text to analyze:
        ---
        {raw_text[:15000]}
        ---
        """
        
        response = model.generate_content(prompt)
        # Clean up potential markdown formatting from the AI response
        cleaned_response_text = response.text.strip().replace('```json', '').replace('```', '').strip()
        
        extracted_transactions = json.loads(cleaned_response_text)
        logger.info(f"Successfully extracted {len(extracted_transactions)} transactions from {source_name} using AI.")

        # Step 3: Validate and format the data
        validated_transactions = []
        for t in extracted_transactions:
            try:
                validated_transactions.append({
                    'source': source_name,
                    'transaction_date': datetime.strptime(t['transaction_date'], '%Y-%m-%d').date(),
                    'amount': float(t['amount']),
                    'reference_id': t.get('reference_id'),
                    'description': t.get('description')
                })
            except (ValueError, KeyError, TypeError) as e:
                logger.warning(f"Skipping malformed transaction object from AI for {source_name}: {t} - Error: {e}")
                continue
        
        return validated_transactions

    except Exception as e:
        logger.error(f"A critical error occurred in parse_pdf_statement for {source_name}: {e}", exc_info=True)
        return []

# The rest of your routes (@reconciliation_bp.route('/run'), etc.) remain unchanged as their logic
# is sound and they correctly consume the output of the parser.

@reconciliation_bp.route('/run', methods=['POST'])
def run_reconciliation():
    if 'bank_statement' not in request.files or 'policy_log' not in request.files:
        return jsonify({"message": "Both bank_statement and policy_log files are required."}), 400

    bank_file = request.files['bank_statement']
    policy_file = request.files['policy_log']

    try:
        # Parse PDF files using the updated AI-powered function
        bank_trans = parse_pdf_statement(bank_file.stream, 'bank_statement')
        policy_trans = parse_pdf_statement(policy_file.stream, 'policy_log')

        if not bank_trans or not policy_trans:
            return jsonify({"message": "Could not extract any valid transaction data from one or both PDFs."}), 400

        # 1. Create a new batch and save all transactions
        batch = ReconciliationBatch()
        db.session.add(batch)
        db.session.flush()

        all_db_transactions = []
        for t in bank_trans + policy_trans:
            all_db_transactions.append(Transaction(batch_id=batch.id, **t))
        
        db.session.bulk_save_objects(all_db_transactions)
        db.session.commit()
        
        # We need to re-fetch the transactions to get their generated IDs
        all_transactions_with_ids = Transaction.query.filter_by(batch_id=batch.id).all()

        # 2. Rules Engine: Deterministic Matching
        logger.info("Running deterministic matching rules...")
        unmatched_bank = {t.id: t for t in all_transactions_with_ids if t.source == 'bank_statement'}
        unmatched_policy = {t.id: t for t in all_transactions_with_ids if t.source == 'policy_log'}
        
        matched_ids = set()
        for bank_id, bank_t in list(unmatched_bank.items()):
            for policy_id, policy_t in list(unmatched_policy.items()):
                if bank_t.reference_id and bank_t.reference_id == policy_t.reference_id and bank_t.amount == policy_t.amount:
                    bank_t.status = 'matched'
                    policy_t.status = 'matched'
                    bank_t.match_id = policy_t.id
                    policy_t.match_id = bank_t.id
                    matched_ids.add(bank_id)
                    matched_ids.add(policy_id)
                    del unmatched_bank[bank_id]
                    del unmatched_policy[policy_id]
                    break
        db.session.commit()
        logger.info(f"Matched {len(matched_ids) // 2} pairs deterministically.")

        # 3. AI Fuzzy Matching with Gemini
        if unmatched_bank and unmatched_policy:
            logger.info("Running AI fuzzy matching on remaining transactions...")
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = f"""
            Act as an expert financial analyst. Your task is to reconcile two lists of unmatched transactions: one from a bank statement and one from an internal policy log.
            
            Find the most likely pairs based on fuzzy matching criteria like similar (but not exact) amounts, close dates, and descriptions that might refer to the same entity (e.g., "UPI/P-SHARMA" vs "Payment from Priya Sharma").
            
            - Bank Transactions (unmatched): {json.dumps([t.to_dict() for t in unmatched_bank.values()], indent=2)}
            - Policy Log Transactions (unmatched): {json.dumps([t.to_dict() for t in unmatched_policy.values()], indent=2)}

            Return your findings ONLY as a single, valid JSON object containing a list of matched pairs.
            - The key should be "matched_pairs".
            - Each item in the list should be an object with "bank_transaction_id" and "policy_transaction_id".
            - Only include pairs you are highly confident about. Do not include a pair if you are unsure.

            EXAMPLE RESPONSE:
            {{
              "matched_pairs": [
                {{ "bank_transaction_id": 15, "policy_transaction_id": 102 }},
                {{ "bank_transaction_id": 18, "policy_transaction_id": 105 }}
              ]
            }}
            """
            response = model.generate_content(prompt)
            cleaned_response_text = response.text.strip().replace('```json', '').replace('```', '').strip()
            ai_results = json.loads(cleaned_response_text)
            
            for pair in ai_results.get("matched_pairs", []):
                bank_t = db.session.get(Transaction, pair['bank_transaction_id'])
                policy_t = db.session.get(Transaction, pair['policy_transaction_id'])
                if bank_t and policy_t and bank_t.status == 'unmatched' and policy_t.status == 'unmatched':
                    bank_t.status = 'matched'
                    policy_t.status = 'matched'
                    bank_t.match_id = policy_t.id
                    policy_t.match_id = bank_t.id
            db.session.commit()
            logger.info(f"AI matched an additional {len(ai_results.get('matched_pairs', []))} pairs.")

        return jsonify({"message": "Reconciliation process completed.", "batchId": batch.id}), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Reconciliation failed: {e}", exc_info=True)
        return jsonify({"message": "An unexpected error occurred."}), 500

@reconciliation_bp.route('/batches/<int:batch_id>', methods=['GET'])
def get_batch_details(batch_id):
    """Returns all transactions for a specific batch, separating exceptions."""
    batch = db.session.get(ReconciliationBatch, batch_id)
    if not batch:
        return jsonify({"message": "Batch not found."}), 404
        
    transactions = batch.transactions
    
    unmatched_bank = [t.to_dict() for t in transactions if t.source == 'bank_statement' and t.status == 'unmatched']
    unmatched_policy = [t.to_dict() for t in transactions if t.source == 'policy_log' and t.status == 'unmatched']
    matched_count = sum(1 for t in transactions if t.status == 'matched') // 2
    
    return jsonify({
        "batchId": batch.id,
        "timestamp": batch.timestamp.isoformat(),
        "status": batch.status,
        "matchedCount": matched_count,
        "exceptions": {
            "bank": unmatched_bank,
            "policy": unmatched_policy
        }
    })