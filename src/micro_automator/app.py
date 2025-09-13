import os
from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import text
from flask_migrate import Migrate

from .extensions import db
from .config import Config
# Correctly import all your blueprints
from .views.documents import documents_bp
from .views.automation import automation_bp
from .views.clients import clients_bp
from .views.dashboard import dashboard_bp
from . import models

# Initialize extensions in the global scope
migrate = Migrate()

def create_app(config_class=Config):
    """The application factory."""
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.from_object(config_class)
    
    # Configure the database URI correctly
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url

    # Initialize extensions with the app instance
    db.init_app(app)
    migrate.init_app(app, db) # Initialize Flask-Migrate
    CORS(app)

    # --- THIS IS THE KEY FIX ---
    # Register all API Blueprints with the app
    app.register_blueprint(documents_bp, url_prefix='/api/documents')
    app.register_blueprint(automation_bp, url_prefix='/api/automation')
    app.register_blueprint(clients_bp, url_prefix='/api/clients')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

    # --- Health Check Routes ---
    @app.route('/')
    def api_root_health():
        return jsonify({"status": "healthy", "message": "Micro-Automator API is running!"})

    @app.route('/api/db-health-check')
    def database_health_check():
        try:
            with app.app_context():
                db.session.execute(text('SELECT 1'))
            return jsonify({"status": "ok", "database": "connected"}), 200
        except Exception as e:
            return jsonify({"status": "error", "database": "disconnected", "details": str(e)}), 500

    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()

    return app

# This instance is used by Gunicorn
app = create_app()
