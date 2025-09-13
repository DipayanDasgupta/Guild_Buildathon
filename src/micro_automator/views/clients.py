from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models.client import Client

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/', methods=['GET'])
def get_clients():
    """Fetches all clients from the database, ordered by name."""
    try:
        clients = Client.query.order_by(Client.name).all()
        return jsonify([client.to_dict() for client in clients])
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@clients_bp.route('/', methods=['POST'])
def add_client():
    """Adds a new client to the database from a JSON payload."""
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"status": "error", "message": "Client name is required"}), 400
    
    try:
        # Create a new Client instance from the provided data
        new_client = Client(
            name=data.get('name'),
            policy_type=data.get('policyType'), # Note the camelCase from frontend
            status=data.get('status', 'Pending'),
            premium=data.get('premium')
        )
        db.session.add(new_client)
        db.session.commit()
        # Return the newly created client's data with a 201 Created status
        return jsonify(new_client.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
