import os
import json
import io
import logging
import time
from flask import Blueprint, request, jsonify
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from google.api_core.retry import Retry

# --- Setup robust logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure the Gemini API client from the environment variable
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
    logger.info("Gemini API configured successfully.")
except Exception as e:
    logger.error(f"Failed to configure Gemini API: {e}")
    raise  # Re-raise to prevent the app from starting without a valid API key

documents_bp = Blueprint('documents', __name__)

def extract_text_from_pdf(pdf_stream):
    text = ""
    try:
        with fitz.open(stream=pdf_stream, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        logger.info(f"Extracted {len(text)} characters from PDF.")
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise
    return text

def extract_text_from_image(image_stream):
    try:
        image = Image.open(image_stream)
        text = pytesseract.image_to_string(image)
        logger.info(f"Extracted {len(text)} characters from Image using OCR.")
        return text
    except Exception as e:
        logger.error(f"Error extracting text from image: {e}")
        raise

@documents_bp.route('/process', methods=['POST'])
def process_document():
    if 'document' not in request.files:
        return jsonify({"status": "error", "message": "No document file part"}), 400

    file = request.files['document']
    logger.info(f"Received file: {file.filename}, Content-Type: {file.content_type}")
    
    try:
        extracted_text = ""
        file_stream = io.BytesIO(file.read())

        if file.content_type == 'application/pdf':
            extracted_text = extract_text_from_pdf(file_stream)
        elif file.content_type.startswith('image/'):
            extracted_text = extract_text_from_image(file_stream)
        else:
            return jsonify({"status": "error", "message": f"Unsupported file type: {file.content_type}"}), 415
        
        if not extracted_text.strip():
            logger.warning("No text could be extracted from the document.")
            return jsonify({"status": "error", "message": "Could not extract any text from the document."}), 400

        # --- Explicitly use the 'gemini-2.5-flash' model ---
        logger.info("Initializing Gemini model: gemini-2.5-pro")
        model = genai.GenerativeModel('gemini-2.5-pro')

        # Define retry policy for 429 errors
        retry_policy = Retry(
            predicate=lambda exc: isinstance(exc, ResourceExhausted),
            initial=5.0,  # Initial delay in seconds
            maximum=60.0,  # Max delay
            multiplier=2.0,  # Exponential backoff
            deadline=300.0  # Total timeout for retries (5 minutes)
        )

        prompt = f"""
        Analyze the following text from an insurance document and extract these fields: Policy Number, Customer Full Name, Premium Amount (numbers only), and Policy End Date (in YYYY-MM-DD format).
        Return the result ONLY as a valid JSON object. If a field is not found, use a null value.

        TEXT:
        ---
        {extracted_text[:10000]} 
        ---
        """  # Truncate text to avoid token limits
        
        logger.info("Sending request to Gemini API...")

        # Wrap the API call with retry logic
        def make_api_call():
            return model.generate_content(prompt, request_options={"timeout": 60})  # 60-second timeout

        try:
            response = retry_policy(make_api_call)()
            json_response_text = response.text.strip().replace("```json", "").replace("```", "")
            logger.info("Successfully received and parsed response from Gemini.")
            
            return jsonify({
                "status": "success",
                "message": "Document processed by Gemini.",
                "data": json.loads(json_response_text)
            })

        except ResourceExhausted as re:
            logger.error(f"Quota exceeded for Gemini API: {re}")
            return jsonify({
                "status": "error",
                "message": "API quota exceeded. Please check your plan and billing details at https://ai.google.dev/gemini-api/docs/rate-limits or try again later."
            }), 429

    except Exception as e:
        logger.error(f"An error occurred during document processing: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "An unexpected error occurred on the server."}), 500