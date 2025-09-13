from flask import Blueprint, jsonify
from ..models.client import Client # Import the client model

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/recent-clients', methods=['GET'])
def get_recent_clients():
    """Provides the 5 most recently added clients for the dashboard."""
    try:
        # Query the database for the last 5 clients, ordered by ID descending
        recent_clients = Client.query.order_by(Client.id.desc()).limit(5).all()
        return jsonify([client.to_dict() for client in recent_clients])
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
