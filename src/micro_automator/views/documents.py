# src/micro_automator/views/documents.py
from flask import Blueprint, request, jsonify
import os
import google.generativeai as genai
import json

# Configure the Gemini API client from the environment variable
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

documents_bp = Blueprint('documents', __name__)

@documents_bp.route('/process', methods=['POST'])
def process_document():
    if 'document' not in request.files:
        return jsonify({"status": "error", "message": "No document file part"}), 400

    file = request.files['document']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400

    try:
        # Prepare the image for the Gemini API
        image_parts = [{"mime_type": file.content_type, "data": file.read()}]
        
        # The AI model and the prompt
        model = genai.GenerativeModel('gemini-2.5-pro')
        prompt = """
        You are an expert insurance document processor. Analyze this image of a policy document and extract the following information precisely:
        - Policy Number
        - Customer Full Name
        - Premium Amount
        - Policy End Date
        Return the result ONLY as a valid JSON object. For example:
        {
          "policy_number": "POL123456",
          "customer_name": "John Doe",
          "premium_amount": 500.00,
          "policy_end_date": "2026-12-31"
        }
        """
        
        # Make the API call
        response = model.generate_content([prompt, *image_parts])
        
        # Clean up the response to ensure it's valid JSON
        json_response_text = response.text.strip().replace("```json", "").replace("```", "")
        
        return jsonify({
            "status": "success",
            "message": "Document processed by Gemini.",
            "data": json.loads(json_response_text)
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500