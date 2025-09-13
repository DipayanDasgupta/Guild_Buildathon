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

        # --- Stage 2: The Ultimate Gemini Prompt ---
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
        Act as an AI assistant for an insurance agent, specializing in KYC (Know Your Customer) data extraction from Indian identity documents.
        
        TASKS:
        1.  **Detailed Extraction:** From the text below, extract every possible piece of identity information. The text is from an OCR scan and may contain errors.
            -   `name`: The full name of the person.
            -   `dob`: The Date of Birth in YYYY-MM-DD format.
            -   `gender`: The gender (Male, Female, or Other).
            -   `aadhaar_number`: The 12-digit Aadhaar number. Format it as XXXX XXXX XXXX.
            -   `pan_number`: The 10-character PAN number.
            -   `address`: The full, complete address as a single string.
        
        2.  **Analysis:** Provide a concise analysis of the document.
            -   `summary`: A single sentence identifying the document type and owner (e.g., "This is the Aadhaar card for Sameer Kumar.").
            -   `category`: Classify the document as "Aadhaar Card", "PAN Card", "Policy Document", or "Other".

        OUTPUT FORMATTING:
        -   Return the result ONLY as a single, valid JSON object.
        -   Do not include any explanatory text, greetings, or markdown formatting.
        -   For any field in the 'extraction' block that is NOT PRESENT in the text, you MUST use the JSON value `null`.

        DOCUMENT TEXT TO ANALYZE:
        ---
        {extracted_text[:15000]}
        ---
        """
        
        response = model.generate_content(prompt)
        ai_data = json.loads(response.text)  # Simplified parsing for now
        
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
            
            # Update client with all new details from the document
            client.dob = extraction_data.get("dob")
            client.gender = extraction_data.get("gender")
            client.address = extraction_data.get("address")
            client.aadhaar_number = extraction_data.get("aadhaar_number")
            client.pan_number = extraction_data.get("pan_number")
            client.photo_url = photo_url
            client.status = "Active"  # Mark as Active since we have their ID
            db.session.add(client)

        db.session.commit()
        return jsonify({"status": "success", "data": new_document.to_dict()})

    except Exception as e:
        db.session.rollback()
        logger.error(f"An error occurred: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "An unexpected server error occurred."}), 500