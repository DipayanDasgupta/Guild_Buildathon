# This must be the very first thing to run
from dotenv import load_dotenv
load_dotenv()

import os
from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import text
from flask_migrate import Migrate

from .extensions import db
from .config import Config
from .views.documents import documents_bp
from .views.automation import automation_bp
from .views.clients import clients_bp
from .views.dashboard import dashboard_bp
from . import models

migrate = Migrate()

def create_app(config_class=Config):
    """The application factory."""
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.from_object(config_class)
    
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # ... (the rest of your app routes remain the same) ...

    with app.app_context():
        db.create_all()

    return app

app = create_app()
