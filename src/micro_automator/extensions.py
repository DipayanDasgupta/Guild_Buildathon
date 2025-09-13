from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# This is the single, shared database object.
db = SQLAlchemy()

# This is the single, shared migration object.
migrate = Migrate()