import os
import json
import io
import logging
import google.generativeai as genai
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from PIL import Image
from datetime import datetime
import pytesseract
import fitz  # PyMuPDF

from ..extensions import db
from ..models.document import Document
from ..models.client import Client
from ..services import schedule_renewal_reminder

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

        # --- Stage 2: The Final, Definitive Gemini Prompt ---
        model = genai.GenerativeModel('gemini-2.5-pro')  # Using the powerful model as you specified
        prompt = f"""
        Act as an expert data extraction AI for an insurance agent. Your task is to analyze the text from a customer's insurance document (like a Welcome Kit, Policy Schedule, or Proposal Form) and convert it into a perfectly structured JSON object.

        **Instructions:**
        1.  **Analyze the Text:** Carefully read the entire provided document text. The text is from a PDF and may contain formatting artifacts.
        2.  **Comprehensive Extraction:** Identify and extract the values for all fields listed in the JSON schema below. Pay close attention to labels like "Policy ID / Number", "Date of Birth (DOB)", etc.
        3.  **Strict JSON Output:** Your entire response MUST be a single, valid JSON object and nothing else. Do not include any explanatory text, greetings, or markdown formatting like ```json.
        4.  **Handle Missing Data:** If a value for any field is not found in the document, you MUST use the JSON value `null`. Do not make up or infer data.
        5.  **Data Formatting:**
            -   Dates must be in `YYYY-MM-DD` format.
            -   `premiumAmount` must be a number (float or integer), without any currency symbols or commas.
            -   `aadhaarNumber` and `panNumber` should be extracted as strings.

        **JSON Schema to Follow:**
        {{
          "extraction": {{
            "name": "Full Name of the primary person",
            "dob": "Date of Birth in YYYY-MM-DD format",
            "aadhaarNumber": "The 12-digit Aadhaar number",
            "panNumber": "The 10-character PAN number",
            "policyId": "The Policy Number or Proposal Number (e.g., TRTL-LIFE-6969)",
            "policyType": "The name or type of the insurance policy (e.g., SecureLife Term Plan)",
            "premiumAmount": 22222.00,
            "premiumFrequency": "The frequency of payment (e.g., 'Yearly', 'Monthly')",
            "expirationDate": "The policy expiry or end date in YYYY-MM-DD format"
          }},
          "analysis": {{
            "summary": "A single, informative sentence describing the document.",
            "category": "Classify as: 'New Policy Document', 'Policy Renewal', 'KYC Document', or 'Other'."
          }}
        }}

        **Document Text for Analysis:**
        ---
        {extracted_text[:15000]}
        ---
        """
        
        response = model.generate_content(prompt)
        
        # --- Handle JSON Parsing ---
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

        new_document = Document(
            filename=file.filename,
            extracted_data=extraction_data,
            ai_summary=analysis_data.get("summary"),
            ai_category=analysis_data.get("category"),
        )
        db.session.add(new_document)
        
        customer_name = extraction_data.get("name")
        if customer_name and customer_name.strip() != "":
            client = Client.query.filter_by(name=customer_name).first()
            if not client:
                client = Client(name=customer_name)
                logger.info(f"Created new client: {customer_name}")
            
            # Update client with all new details from the document
            client.dob = extraction_data.get("dob")
            client.gender = extraction_data.get("gender")
            client.address = extraction_data.get("address")
            client.aadhaar_number = extraction_data.get("aadhaarNumber")
            client.pan_number = extraction_data.get("panNumber")
            client.photo_url = photo_url
            client.status = "Active"  # Mark as Active since we have their ID

            expiration_date_str = extraction_data.get("expirationDate")
            if expiration_date_str:
                try:
                    client.expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    client.expiration_date = None
            
            db.session.add(client)
            
            # --- Definitive Fix: Commit client to ensure it has an ID ---
            db.session.commit()
            
            # Now that the client is saved and has an ID, schedule the reminder
            if client.expiration_date:
                schedule_renewal_reminder(client)
                # Commit again to save the reminder
                db.session.commit()

        else:
            # If there's no customer name, commit the document only
            db.session.commit()

        return jsonify({"status": "success", "data": new_document.to_dict()})

    except Exception as e:
        db.session.rollback()
        logger.error(f"An error occurred during document processing: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500