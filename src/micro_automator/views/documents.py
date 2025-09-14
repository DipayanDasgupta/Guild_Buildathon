import os
import json
import io
import logging
import google.generativeai as genai
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract
import fitz  # PyMuPDF

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
        raise ValueError("GOOGLE_API_KEY not set.")
    genai.configure(api_key=api_key)
except Exception as e:
    logger.error(f"Failed to configure Gemini API: {e}")

# --- Blueprint ---
documents_bp = Blueprint('documents', __name__)

# --- Helper Functions for Text Extraction ---
def extract_and_save_image_from_pdf(pdf_stream, original_filename):
    """Finds the largest image in a PDF, saves it, and returns its public URL."""
    try:
        doc = fitz.open(stream=pdf_stream, filetype="pdf")
        max_area = 0
        best_image = None
        for page in doc:
            for img in page.get_images(full=True):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image = Image.open(io.BytesIO(image_bytes))
                area = image.width * image.height
                if area > max_area:
                    max_area = area
                    best_image = image_bytes

        if best_image:
            filename = f"photo_{secure_filename(original_filename)}.png"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            with open(filepath, "wb") as f:
                f.write(best_image)
            
            # This assumes your app is hosted at the root. Adjust if needed.
            photo_url = f"{request.host_url}uploads/{filename}"
            logger.info(f"Extracted and saved photo to {photo_url}")
            return photo_url
    except Exception as e:
        logger.error(f"Could not extract image from PDF: {e}")
    return None

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

# --- API Endpoints ---
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
    if 'document' not in request.files:
        return jsonify({"status": "error", "message": "No document file part"}), 400
    file = request.files['document']
    
    file.seek(0)
    file_bytes = file.read()
    file_stream = io.BytesIO(file_bytes)
    
    try:
        # --- Stage 1: Parallel Extraction ---
        extracted_text = ""
        photo_url = None
        
        if file.content_type == 'application/pdf':
            extracted_text = extract_text_from_pdf(io.BytesIO(file_bytes))
            photo_url = extract_and_save_image_from_pdf(io.BytesIO(file_bytes), file.filename)
        elif file.content_type.startswith('image/'):
            extracted_text = extract_text_from_image(io.BytesIO(file_bytes))
            # If the upload is an image, we can treat the whole thing as the photo
            filename = f"photo_{secure_filename(file.filename)}.png"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            with open(filepath, "wb") as f:
                f.write(file_bytes)
            photo_url = f"{request.host_url}uploads/{filename}"
        else:
            return jsonify({"status": "error", "message": "Unsupported file type"}), 415
        
        if not extracted_text.strip():
            return jsonify({"status": "error", "message": "Could not extract text."}), 400

        # --- Stage 2: The Smart Form Filler Prompt ---
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        Act as a Smart AI Form Filler for an insurance agent. Your primary goal is to ingest the text from a user-uploaded document, identify the document type, extract all relevant data, and determine what documents are still missing for a complete insurance application.

        **Instructions:**
        1.  **Analyze and Identify:** Read the text and identify the document type. Is it an Aadhaar Card, a PAN Card, a Proposal Form, a Bank Statement, etc.?
        2.  **Detailed Extraction:** Extract all personal and policy information into a structured `extraction` object.
        3.  **Missing Document Detection:** Based on the document type you identified, determine what other documents are typically required for a full application (e.g., if it's a Proposal Form, Aadhaar and PAN are likely needed). List these in a `missing_documents` array. If all documents seem to be present, return an empty array.
        4.  **Strict JSON Output:** Your entire response MUST be a single, valid JSON object and nothing else.

        **JSON Schema to Follow:**
        {{
          "extraction": {{
            "name": "...", "dob": "...", "panNumber": "...", "aadhaarNumber": "...", "email": "...", "phone": "...", "address": "...", "policyType": "..."
          }},
          "analysis": {{
            "identified_document_type": "e.g., Aadhaar Card",
            "missing_documents": ["e.g., PAN Card", "e.g., Proposal Form"]
          }}
        }}

        **Document Text for Analysis:**
        ---
        {extracted_text[:15000]}
        ---
        """
        
        response = model.generate_content(prompt)
        
        # --- JSON Parsing and Error Handling ---
        cleaned_text = response.text.strip()
        ai_data = None
        try:
            # First, try to load the text directly.
            ai_data = json.loads(cleaned_text)
        except json.JSONDecodeError:
            logger.warning("Initial JSON parsing failed. Searching for a markdown JSON block.")
            # If it fails, it's likely wrapped in ```json ... ```. We'll find it.
            start_index = cleaned_text.find('{')
            end_index = cleaned_text.rfind('}') + 1
            if start_index != -1 and end_index != -1:
                json_str = cleaned_text[start_index:end_index]
                try:
                    ai_data = json.loads(json_str)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse extracted JSON block: {json_str}. Error: {e}")
                    raise ValueError("Could not find or parse a valid JSON object in the AI response.")
            else:
                raise ValueError(f"No JSON object found in the AI response: {cleaned_text}")
        
        logger.info("Successfully received and parsed advanced analysis from Gemini.")

        # --- Stage 3: Save to Database ---
        extraction_data = ai_data.get("extraction", {})
        analysis_data = ai_data.get("analysis", {})
        
        customer_name = extraction_data.get("name")
        if customer_name and customer_name.strip() != "":
            # Find or create the client
            client = Client.query.filter_by(name=customer_name).first()
            if not client:
                client = Client(name=customer_name, status='Engaged')
            
            # Update client with any new info from the document
            client.dob = extraction_data.get("dob")
            client.pan_number = extraction_data.get("panNumber")
            client.aadhaar_number = extraction_data.get("aadhaarNumber")
            client.email = extraction_data.get("email")
            client.phone = extraction_data.get("phone")
            client.address = extraction_data.get("address")
            client.policy_type = extraction_data.get("policyType")
            client.photo_url = photo_url
            db.session.add(client)
            
            # Create a new Form record for the uploaded document
            new_form = Form(
                client_id=client.id,
                form_type=analysis_data.get("identified_document_type", "Unknown Document")
            )
            db.session.add(new_form)

            # Save document to Document table
            new_document = Document(
                filename=file.filename,
                extracted_data=extraction_data,
                ai_summary=f"This is the {analysis_data.get('identified_document_type', 'Unknown Document')} for {customer_name}.",
                ai_category=analysis_data.get("identified_document_type", "Unknown Document"),
            )
            db.session.add(new_document)
            
            db.session.commit()
            
            # Return both the extracted data and the missing documents list
            return jsonify({ 
                "status": "success", 
                "extracted_data": extraction_data,
                "missing_documents": analysis_data.get("missing_documents", [])
            })
        else:
            return jsonify({"status": "error", "message": "Could not identify a customer name in the document."}), 400

    except Exception as e:
        db.session.rollback()
        logger.error(f"An error occurred during document processing: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500