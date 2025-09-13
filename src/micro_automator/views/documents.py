import os
import json
import io
import logging
import google.generativeai as genai
from flask import Blueprint, request, jsonify
from PIL import Image
import pytesseract
import fitz

from ..extensions import db
from ..models.document import Document
from ..models.client import Client

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configure API ---
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
except Exception as e:
    logger.error(f"Failed to configure Gemini API: {e}")

# --- Blueprint ---
documents_bp = Blueprint('documents', __name__)

# --- Helper Functions for Text Extraction ---

def extract_text_from_pdf(pdf_stream):
    """Extracts text from a PDF file stream."""
    text = ""
    with fitz.open(stream=pdf_stream, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    logger.info(f"Extracted {len(text)} characters from PDF.")
    return text

def extract_text_from_image(image_stream):
    """Extracts text from an image file stream using OCR."""
    image = Image.open(image_stream)
    text = pytesseract.image_to_string(image)
    logger.info(f"Extracted {len(text)} characters from Image using OCR.")
    return text

# --- API Endpoints ---

@documents_bp.route('/', methods=['GET'])
def get_all_documents():
    """Fetches all processed documents from the database."""
    try:
        documents = Document.query.order_by(Document.upload_date.desc()).all()
        return jsonify([doc.to_dict() for doc in documents])
    except Exception as e:
        logger.error(f"Error fetching documents: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Could not retrieve documents."}), 500

@documents_bp.route('/process', methods=['POST'])
def process_document():
    """Handles file upload, AI analysis, and saving to the database."""
    if 'document' not in request.files:
        return jsonify({"status": "error", "message": "No document file part"}), 400

    file = request.files['document']
    logger.info(f"Received file: {file.filename}")
    
    # Reset file stream position
    file.seek(0)
    file_stream = io.BytesIO(file.read())
    file.seek(0) # Reset again for saving if needed

    try:
        # --- Stage 1: Text Extraction ---
        extracted_text = ""
        if file.content_type == 'application/pdf':
            extracted_text = extract_text_from_pdf(file_stream)
        elif file.content_type.startswith('image/'):
            extracted_text = extract_text_from_image(file_stream)
        else:
            return jsonify({"status": "error", "message": f"Unsupported file type"}), 415
        
        if not extracted_text.strip():
            return jsonify({"status": "error", "message": "Could not extract text."}), 400

        # --- Stage 2: Advanced Gemini Analysis ---
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        prompt = f"""
        Act as an expert insurance agent's assistant. Analyze the text from this document and perform the following tasks:
        1. Extract key information: Policy Number, Customer Full Name, Premium Amount, and Policy End Date.
        2. Provide a concise, one-sentence summary of the document's purpose.
        3. Categorize the document into ONE of the following: "New Policy", "Claim Form", "Renewal Notice", "General Inquiry".
        4. Determine the sentiment of the document: "Positive", "Neutral", "Negative", or "Urgent".
        5. Generate a list of 2-3 short, actionable items for the agent.

        Return the result ONLY as a valid JSON object with the following structure:
        {{
          "extracted_data": {{"policy_number": "...", "customer_name": "...", "premium_amount": ..., "policy_end_date": "..."}},
          "summary": "...", "category": "...", "sentiment": "...", "action_items": ["Action 1", "Action 2"]
        }}

        TEXT: --- {extracted_text[:15000]} ---
        """
        
        response = model.generate_content(prompt)
        json_response_text = response.text.strip().replace("```json", "").replace("```", "")
        ai_data = json.loads(json_response_text)
        logger.info("Successfully received and parsed advanced analysis from Gemini.")

        # --- Stage 3: Save to Database AND Create/Update Client ---
        new_document = Document(
            filename=file.filename,
            extracted_data=ai_data.get("extracted_data"),
            ai_summary=ai_data.get("summary"),
            ai_category=ai_data.get("category"),
            ai_sentiment=ai_data.get("sentiment"),
            ai_action_items=ai_data.get("action_items")
        )
        db.session.add(new_document)
        
        customer_name = ai_data.get("extracted_data", {}).get("customer_name")
        if customer_name and customer_name.strip() != "":
            client = Client.query.filter_by(name=customer_name).first()
            if not client:
                client = Client(name=customer_name)
                logger.info(f"Creating new client: {customer_name}")
            
            client.policy_type = ai_data.get("extracted_data", {}).get("policy_type", client.policy_type)
            client.premium = ai_data.get("extracted_data", {}).get("premium_amount", client.premium)
            client.status = "Active"
            db.session.add(client)

        db.session.commit()
        logger.info(f"Successfully saved document {new_document.id} and updated client data.")
        
        return jsonify({ "status": "success", "message": "Document processed and saved.", "data": new_document.to_dict() })

    except Exception as e:
        db.session.rollback()
        logger.error(f"An error occurred: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500
