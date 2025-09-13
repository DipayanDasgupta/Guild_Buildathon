# src/micro_automator/views/documents.py

import os
import json
import io
import google.generativeai as genai
from flask import Blueprint, request, jsonify
from PIL import Image
import pytesseract
import fitz  # PyMuPDF

# Configure the Gemini API client from the environment variable
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

documents_bp = Blueprint('documents', __name__)

def extract_text_from_pdf(pdf_stream):
    """Extracts text from a PDF file stream."""
    text = ""
    with fitz.open(stream=pdf_stream, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_from_image(image_stream):
    """Extracts text from an image file stream using OCR."""
    image = Image.open(image_stream)
    text = pytesseract.image_to_string(image)
    return text

@documents_bp.route('/process', methods=['POST'])
def process_document():
    if 'document' not in request.files:
        return jsonify({"status": "error", "message": "No document file part"}), 400

    file = request.files['document']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400

    try:
        extracted_text = ""
        file_stream = io.BytesIO(file.read())

        # Stage 1: Intelligent Text Extraction
        if file.content_type == 'application/pdf':
            extracted_text = extract_text_from_pdf(file_stream)
        elif file.content_type.startswith('image/'):
            extracted_text = extract_text_from_image(file_stream)
        else:
            return jsonify({"status": "error", "message": f"Unsupported file type: {file.content_type}"}), 415
        
        if not extracted_text.strip():
            return jsonify({"status": "error", "message": "Could not extract any text from the document."}), 400

        # Stage 2: Gemini Text Analysis
        # Use a text-only model like gemini-1.5-flash, which is fast and efficient
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        prompt = f"""
        You are an expert insurance document processor. Below is the raw text extracted from a policy document. Analyze this text and extract the following information precisely:
        - Policy Number
        - Customer Full Name
        - Premium Amount (numbers only)
        - Policy End Date (in YYYY-MM-DD format)
        
        Return the result ONLY as a valid JSON object. If a field cannot be found, use null as its value. For example:
        {{
          "policy_number": "POL123456",
          "customer_name": "John Doe",
          "premium_amount": 500.00,
          "policy_end_date": "2026-12-31"
        }}

        Here is the extracted text:
        ---
        {extracted_text}
        ---
        """
        
        response = model.generate_content(prompt)
        
        # Clean up the response to ensure it's valid JSON
        json_response_text = response.text.strip().replace("```json", "").replace("```", "")
        
        return jsonify({
            "status": "success",
            "message": "Document processed by Gemini.",
            "data": json.loads(json_response_text)
        })

    except Exception as e:
        # Provide a more specific error message for debugging
        error_message = f"An unexpected error occurred: {str(e)}"
        return jsonify({"status": "error", "message": error_message}), 500