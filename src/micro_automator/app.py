# src/micro_automator/app.py

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

from .config import Config
from .views.documents import documents_bp
from .views.automation import automation_bp
from .views.dashboard import dashboard_bp
from .views.clients import clients_bp

# 1. Initialize extensions in the global scope
# This prevents circular imports and makes the 'db' object available to other files (like models)
db = SQLAlchemy()

def create_app(config_class=Config):
    """The application factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 2. Configure the database URI from the environment variable
    # Important: The 'postgresql://' part in the Render URL needs to be changed for SQLAlchemy
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url

    # 3. Associate the extensions with the app instance
    db.init_app(app)
    CORS(app)

    # Register API Blueprints
    app.register_blueprint(documents_bp, url_prefix='/api/documents')
    app.register_blueprint(automation_bp, url_prefix='/api/automation')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(clients_bp, url_prefix='/api/clients')

    # --- Health Check Routes ---

    @app.route('/')
    def api_root_health():
        """Provides a simple health check for the API itself."""
        return jsonify({"status": "healthy", "message": "Micro-Automator API is running!"})

    @app.route('/api/db-health-check')
    def database_health_check():
        """Provides a health check for the database connection."""
        try:
            # Make a simple query to the database to check the connection
            db.session.execute(text('SELECT 1'))
            return jsonify({"status": "ok", "database": "connected"}), 200
        except Exception as e:
            # Return a server error if the connection fails
            return jsonify({"status": "error", "database": "disconnected", "details": str(e)}), 500

    return app

# This instance is used by Gunicorn in production
app = create_app()