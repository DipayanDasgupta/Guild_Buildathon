import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration settings."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a-very-secret-key')
    # Add other configurations like database URI etc. here
