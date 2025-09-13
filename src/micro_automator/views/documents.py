import os, json, io, logging
import google.generativeai as genai
from flask import Blueprint, request, jsonify
from PIL import Image
import pytesseract
import fitz
from ..extensions import db
from ..models.document import Document
from ..models.client import Client

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
    text = ""
    with fitz.open(stream=pdf_stream, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    logger.info(f"Extracted {len(text)} characters from PDF.")
    return text

def extract_text_from_image(image_stream):
    image = Image.open(image_stream)
    text = pytesseract.image_to_string(image)
    logger.info(f"Extracted {len(text)} characters from Image using OCR.")
    return text

@documents_bp.route('/', methods=['GET'])
def get_all_documents():
    documents = Document.query.order_by(Document.upload_date.desc()).all()
    return jsonify([doc.to_dict() for doc in documents])

@documents_bp.route('/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    document = Document.query.get_or_404(doc_id)
    db.session.delete(document)
    db.session.commit()
    return jsonify({'message': 'Document deleted successfully'})

@documents_bp.route('/process', methods=['POST'])
def process_document():
    if 'document' not in request.files: return jsonify({"status": "error", "message": "No document file part"}), 400
    file = request.files['document']
    file.seek(0)
    file_stream = io.BytesIO(file.read())
    try:
        extracted_text = ""
        if file.content_type == 'application/pdf': extracted_text = extract_text_from_pdf(file_stream)
        elif file.content_type.startswith('image/'): extracted_text = extract_text_from_image(file_stream)
        else: return jsonify({"status": "error", "message": "Unsupported file type"}), 415
        if not extracted_text.strip(): return jsonify({"status": "error", "message": "Could not extract text."}), 400
        
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        prompt = f"""Act as an AI assistant for an insurance agent. Analyze the text from this document and perform a comprehensive analysis.
        TASKS:
        1.  **Detailed Extraction:** Extract every possible piece of information that could be relevant. This includes, but is not limited to: Customer Full Name, Policy Number, Policy Type, Premium Amount, Start Date, End Date, Address, Vehicle Details (if any), Claim Details (if any).
        2.  **Analysis:** Based on the entire document, provide a concise analysis by determining the following: `summary`, `category`, `sentiment`, `urgency_score` (1-10), and a JSON array of `suggested_actions`.
        OUTPUT FORMATTING:
        -   Return the result ONLY as a single, valid JSON object.
        -   For any field in the 'extraction' block that is not found, you MUST use the JSON value `null`.
        EXAMPLE JSON STRUCTURE:
        {{"extraction": {{"customer_name": "John Doe", "policy_number": "XYZ-12345"}}, "analysis": {{"summary": "...", "category": "Policy Renewal Notice", "sentiment": "Urgent", "urgency_score": 9, "suggested_actions": ["Action 1"]}}}}
        DOCUMENT TEXT TO ANALYZE: --- {extracted_text[:15000]} ---"""
        
        response = model.generate_content(prompt)
        ai_data = json.loads(response.text)
        
        new_document = Document(filename=file.filename, extracted_data=ai_data.get("extraction"), ai_summary=ai_data.get("analysis", {}).get("summary"), ai_category=ai_data.get("analysis", {}).get("category"), ai_sentiment=ai_data.get("analysis", {}).get("sentiment"), ai_action_items=ai_data.get("analysis", {}).get("suggested_actions"))
        db.session.add(new_document)
        
        customer_name = ai_data.get("extraction", {}).get("customer_name")
        if customer_name and customer_name.strip() != "":
            client = Client.query.filter_by(name=customer_name).first()
            if not client: client = Client(name=customer_name)
            client.email = ai_data.get("extraction", {}).get("customer_email", client.email)
            client.phone = ai_data.get("extraction", {}).get("customer_phone", client.phone)
            client.policy_type = ai_data.get("extraction", {}).get("policy_type", client.policy_type)
            client.status = "Active"
            db.session.add(client)

        db.session.commit()
        return jsonify({ "status": "success", "data": new_document.to_dict() })
    except Exception as e:
        db.session.rollback()
        logger.error(f"An error occurred: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500
