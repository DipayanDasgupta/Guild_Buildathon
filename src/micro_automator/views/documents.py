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
from ..models.client import Client # Import the Client model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key: raise ValueError("GOOGLE_API_KEY not set.")
    genai.configure(api_key=api_key)
except Exception as e:
    logger.error(f"Failed to configure Gemini API: {e}")

documents_bp = Blueprint('documents', __name__)

def extract_text_from_pdf(pdf_stream):
    # ... code remains the same
def extract_text_from_image(image_stream):
    # ... code remains the same

@documents_bp.route('/', methods=['GET'])
def get_all_documents():
    # ... code remains the same

@documents_bp.route('/process', methods=['POST'])
def process_document():
    # ... code up to Gemini Analysis remains the same ...
    # After Gemini analysis, we add the new logic:
    try:
        # ... (Stage 1 & 2: Text Extraction & Gemini Analysis code here) ...
        # (Assuming 'ai_data' is the JSON object returned from Gemini)
        
        # --- Stage 3: Save to Database AND Create/Update Client ---
        
        # Save the document first
        new_document = Document(
            filename=file.filename,
            extracted_data=ai_data.get("extracted_data"),
            ai_summary=ai_data.get("summary"),
            ai_category=ai_data.get("category"),
            ai_sentiment=ai_data.get("sentiment"),
            ai_action_items=ai_data.get("action_items")
        )
        db.session.add(new_document)
        
        # Now, create a client from the document data
        customer_name = ai_data.get("extracted_data", {}).get("customer_name")
        if customer_name:
            # Check if client already exists
            client = Client.query.filter_by(name=customer_name).first()
            if not client:
                client = Client(name=customer_name)
                logger.info(f"Creating new client: {customer_name}")
            
            # Update client details from the document
            client.policy_type = ai_data.get("extracted_data", {}).get("policy_type", client.policy_type)
            client.premium = ai_data.get("extracted_data", {}).get("premium_amount", client.premium)
            client.status = "Active" # Or derive from document category/sentiment
            db.session.add(client)

        db.session.commit()
        logger.info(f"Successfully saved document {new_document.id} and updated client data.")
        
        return jsonify({ "status": "success", "message": "Document processed and saved.", "data": new_document.to_dict() })

    except Exception as e:
        db.session.rollback() # Rollback DB changes on error
        logger.error(f"An error occurred: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500
