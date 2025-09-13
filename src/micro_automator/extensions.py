from flask_sqlalchemy import SQLAlchemy

# This is the single, shared database object.
# It is initialized here but configured in the app factory.
db = SQLAlchemy()
