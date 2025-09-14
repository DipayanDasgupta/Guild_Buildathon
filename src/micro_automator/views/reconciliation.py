import os, json, io, logging
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
    Extracts tabular data from a PDF and converts it into a list of dictionaries.
    This is a smart parser that looks for tables and assumes a 'Date', 'Description'/'ReferenceID', and 'Amount' structure.
    """
    transactions = []
    try:
        doc = fitz.open(stream=file_stream, filetype="pdf")
        for page in doc:
            # Find all tables on the page
            tables = page.find_tables()
            if not tables:
                logger.warning(f"No tables found on a page of {source_name}")
                continue
            
            for table in tables:
                # Extract data as a list of lists
                data = table.extract()
                if not data or len(data) < 2:  # Must have a header and at least one row
                    continue

                header = [str(h).lower() for h in data[0]]  # Get header, normalize to lower case
                
                # Try to find the required column indices
                try:
                    date_idx = header.index('date')
                    amount_idx = header.index('amount')
                    # Description can have multiple names
                    desc_idx = -1
                    if 'description' in header: 
                        desc_idx = header.index('description')
                    elif 'referenceid' in header: 
                        desc_idx = header.index('referenceid')
                    
                except ValueError:
                    logger.warning(f"Skipping table in {source_name} due to missing required columns (Date, Amount, Description/ReferenceID)")
                    continue

                # Process each row in the table
                for row in data[1:]:  # Skip header row
                    try:
                        transactions.append({
                            'source': source_name,
                            'transaction_date': datetime.strptime(row[date_idx], '%Y-%m-%d').date(),
                            'amount': float(row[amount_idx]),
                            'reference_id': row[desc_idx] if desc_idx != -1 else None,
                            'description': row[desc_idx] if desc_idx != -1 else None,
                        })
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Skipping malformed row in {source_name} PDF: {row} - Error: {e}")
                        continue
    except Exception as e:
        logger.error(f"Failed to parse PDF for {source_name}: {e}")

    return transactions

@reconciliation_bp.route('/run', methods=['POST'])
def run_reconciliation():
    if 'bank_statement' not in request.files or 'policy_log' not in request.files:
        return jsonify({"message": "Both bank_statement and policy_log files are required."}), 400

    bank_file = request.files['bank_statement']
    policy_file = request.files['policy_log']

    try:
        # Parse PDF files instead of CSV
        bank_trans = parse_pdf_statement(bank_file.stream, 'bank_statement')
        policy_trans = parse_pdf_statement(policy_file.stream, 'policy_log')

        if not bank_trans or not policy_trans:
            return jsonify({"message": "Could not extract any valid transaction data from one or both PDFs."}), 400

        # 1. Create a new batch and save all transactions
        batch = ReconciliationBatch()
        db.session.add(batch)
        db.session.flush()  # Get the batch ID

        all_transactions = [Transaction(batch_id=batch.id, **t) for t in bank_trans + policy_trans]
        db.session.bulk_save_objects(all_transactions)
        db.session.commit()

        # 2. Rules Engine: Deterministic Matching
        logger.info("Running deterministic matching rules...")
        unmatched_bank = {t.id: t for t in all_transactions if t.source == 'bank_statement'}
        unmatched_policy = {t.id: t for t in all_transactions if t.source == 'policy_log'}
        
        # Simple match on ReferenceID and Amount
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
            ai_results = json.loads(response.text)
            
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
    batch = ReconciliationBatch.query.get_or_404(batch_id)
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