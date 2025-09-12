import anvil.server
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
ANVIL_UPLINK_KEY = os.getenv("ANVIL_UPLINK_KEY")
if not ANVIL_UPLINK_KEY:
    raise ValueError("ANVIL_UPLINK_KEY not found in .env file. Please add it.")

# When running locally, backend is on localhost. The deployed uplink will use the production URL.
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:5000")

# --- Anvil Server Connection ---
print(f"Connecting to Anvil server... (Using Backend URL: {BACKEND_URL})")
anvil.server.connect(ANVIL_UPLINK_KEY)
print("✅ Successfully connected to Anvil server.")

# --- Callable Functions (The Bridge between Anvil and Flask) ---

@anvil.server.callable
def process_document_in_backend(file):
    """
    Receives a file (Anvil Media object) from the Anvil frontend,
    sends it to our Flask backend's API for processing.
    """
    print(f"Received file '{file.name}' from Anvil, forwarding to Flask backend...")
    api_endpoint = f"{BACKEND_URL}/api/documents/process"
    
    # Prepare the file for a multipart/form-data request
    files = {'document': (file.name, file.get_bytes(), file.content_type)}
    
    try:
        response = requests.post(api_endpoint, files=files)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        print("✅ Successfully got response from Flask.")
        return response.json()
    except requests.exceptions.RequestException as e:
        error_message = f"Error calling Flask backend: {e}"
        print(f"❌ {error_message}")
        return {"status": "error", "message": "Could not connect to the document processing service."}

# --- Keep the script running ---
print("Anvil Uplink is running and waiting for calls from the frontend.")
anvil.server.wait_forever()
