# src/micro_automator/app.py

from flask import Flask, jsonify, render_template
from flask_cors import CORS  # <-- 1. IMPORT THIS
from .config import Config
from .views.documents import documents_bp
from .views.automation import automation_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)  # <-- 2. INITIALIZE CORS

    # Register API Blueprints
    app.register_blueprint(documents_bp, url_prefix='/api/documents')
    app.register_blueprint(automation_bp, url_prefix='/api/automation')

    # This route is no longer needed as Vercel will handle the frontend
    # @app.route('/')
    # def index():
    #     """Serves the main HTML page that contains our frontend."""
    #     return render_template('index.html')

    @app.route('/')
    def api_health_check():
         """Provides a simple health check for the API."""
         return jsonify({"status": "healthy", "message": "Micro-Automator API is running!"})


    return app

# This instance is used by Gunicorn in production and 'flask run'
app = create_app()