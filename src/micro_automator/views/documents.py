import os
import json
import io
import logging
import google.generativeai as genai
from flask import Blueprint, request, jsonify
from PIL import Image
import pytesseract
import fitz  # PyMuPDF

from ..app import db
from ..models.document import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key: raise ValueError("GOOGLE_API_KEY not set.")
    genai.configure(api_key=api_key)
    logger.info("Gemini API configured successfully.")
except Exception as e:
    logger.error(f"Failed to configure Gemini API: {e}")

documents_bp = Blueprint('documents', __name__)

# --- Helper Functions for Text Extraction ---
def extract_text_from_pdf(pdf_stream):
    # ... (code remains the same)
def extract_text_from_image(image_stream):
    # ... (code remains the same)

# --- NEW: API to fetch all processed documents ---
@documents_bp.route('/', methods=['GET'])
def get_all_documents():
    try:
        documents = Document.query.order_by(Document.upload_date.desc()).all()
        return jsonify([doc.to_dict() for doc in documents])
    except Exception as e:
        logger.error(f"Error fetching documents: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Could not retrieve documents."}), 500

# --- UPGRADED: API to process a new document ---
@documents_bp.route('/process', methods=['POST'])
def process_document():
    if 'document' not in request.files:
        return jsonify({"status": "error", "message": "No document file part"}), 400

    file = request.files['document']
    logger.info(f"Received file: {file.filename}")

    try:
        # --- Stage 1: Text Extraction ---
        extracted_text = ""
        file_stream = io.BytesIO(file.read())
        if file.content_type == 'application/pdf':
            extracted_text = extract_text_from_pdf(file_stream)
        elif file.content_type.startswith('image/'):
            extracted_text = extract_text_from_image(file_stream)
        else:
            return jsonify({"status": "error", "message": f"Unsupported file type"}), 415
        
        if not extracted_text.strip():
            return jsonify({"status": "error", "message": "Could not extract text."}), 400

        # --- Stage 2: Advanced Gemini Analysis ---
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        # This is our new, more powerful prompt!
        prompt = f"""
        Act as an expert insurance agent's assistant. Analyze the text from this document and perform the following tasks:
        1.  Extract key information: Policy Number, Customer Full Name, Premium Amount, and Policy End Date.
        2.  Provide a concise, one-sentence summary of the document's purpose.
        3.  Categorize the document into ONE of the following: "New Policy", "Claim Form", "Renewal Notice", "General Inquiry".
        4.  Determine the sentiment of the document: "Positive", "Neutral", "Negative", or "Urgent".
        5.  Generate a list of 2-3 short, actionable items for the agent.

        Return the result ONLY as a valid JSON object with the following structure:
        {{
          "extracted_data": {{
            "policy_number": "...",
            "customer_name": "...",
            "premium_amount": ...,
            "policy_end_date": "..."
          }},
          "summary": "...",
          "category": "...",
          "sentiment": "...",
          "action_items": ["Action 1", "Action 2"]
        }}

        Here is the extracted text:
        ---
        {extracted_text[:15000]} 
        ---
        """
        
        response = model.generate_content(prompt)
        json_response_text = response.text.strip().replace("```json", "").replace("```", "")
        ai_data = json.loads(json_response_text)
        logger.info("Successfully received and parsed advanced analysis from Gemini.")

        # --- Stage 3: Save to Database ---
        new_document = Document(
            filename=file.filename,
            extracted_data=ai_data.get("extracted_data"),
            ai_summary=ai_data.get("summary"),
            ai_category=ai_data.get("category"),
            ai_sentiment=ai_data.get("sentiment"),
            ai_action_items=ai_data.get("action_items")
        )
        db.session.add(new_document)
        db.session.commit()
        logger.info(f"Successfully saved document {new_document.id} to the database.")
        
        return jsonify({
            "status": "success",
            "message": "Document processed and saved.",
            "data": new_document.to_dict()
        })

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500
