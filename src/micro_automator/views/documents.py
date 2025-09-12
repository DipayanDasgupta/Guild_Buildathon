from flask import Blueprint, request, jsonify

documents_bp = Blueprint('documents', __name__)

@documents_bp.route('/process', methods=['POST'])
def process_document():
    """
    API endpoint for Intelligent Document Processing.
    Receives a file, processes it with AI/ML, and returns structured data.
    """
    if 'document' not in request.files:
        return jsonify({"status": "error", "message": "No 'document' file part in the request"}), 400

    file = request.files['document']
    
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400

    # --- AI/ML INNOVATION POINT ---
    # Here you would integrate your innovative features:
    # 1. OCR: Use pytesseract or a cloud API (Google Vision, AWS Textract) to get raw text.
    # 2. NLP/Entity Recognition: Use libraries like spaCy or models from Hugging Face
    #    to identify and extract key fields (name, policy no, amounts, dates).
    # 3. Validation: Check if extracted data makes sense (e.g., valid date formats).
    print(f"Processing document: {file.filename}")

    # For the buildathon, we simulate a successful AI extraction
    simulated_extracted_data = {
        "policy_number": "POL-AI-98765",
        "customer_name": "AI Extracted Name",
        "premium_amount": 1250.00,
        "due_date": "2025-10-01",
        "confidence_score": 0.95
    }

    return jsonify({
        "status": "success",
        "message": "Document processed successfully.",
        "data": simulated_extracted_data
    })
