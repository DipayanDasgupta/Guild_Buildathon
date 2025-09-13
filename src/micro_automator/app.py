import os
from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import text
from .extensions import db
from .config import Config
from .views.documents import documents_bp
from .views.automation import automation_bp
from .views.clients import clients_bp
from .views.dashboard import dashboard_bp
from . import models

def create_app(config_class=Config):
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.from_object(config_class)
    
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url

    db.init_app(app)
    CORS(app)

    app.register_blueprint(documents_bp, url_prefix='/api/documents')
    app.register_blueprint(automation_bp, url_prefix='/api/automation')
    app.register_blueprint(clients_bp, url_prefix='/api/clients')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

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

    with app.app_context():
        db.create_all()

    return app

app = create_app()
