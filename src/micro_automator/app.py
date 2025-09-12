from flask import Flask, jsonify
from .config import Config
from .views.documents import documents_bp
from .views.automation import automation_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register Blueprints for modular API routes
    app.register_blueprint(documents_bp, url_prefix='/api/documents')
    app.register_blueprint(automation_bp, url_prefix='/api/automation')

    @app.route('/')
    def index():
        """Health check endpoint."""
        return jsonify({"status": "healthy", "message": "Micro-Automator Backend is running!"})

    return app

# This instance is used by Gunicorn in production
app = create_app()
