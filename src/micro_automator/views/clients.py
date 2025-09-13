from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models.client import Client
from sqlalchemy import or_

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/', methods=['GET'])
def get_clients():
    """Fetches clients with optional filtering by status and searching by name."""
    try:
        query = Client.query
        
        # Get query parameters from the request URL
        status_filter = request.args.get('status')
        search_term = request.args.get('search')

        if status_filter and status_filter != 'All':
            query = query.filter(Client.status == status_filter)
        
        if search_term:
            # Case-insensitive search across name and policy ID
            search_pattern = f"%{search_term}%"
            query = query.filter(or_(Client.name.ilike(search_pattern), Client.policy_id.ilike(search_pattern)))

        clients = query.order_by(Client.name).all()
        return jsonify([client.to_dict() for client in clients])
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@clients_bp.route('/', methods=['POST'])
def add_client():
    data = request.get_json()
    if not data or not data.get('name'): return jsonify({"message": "Client name is required"}), 400
    new_client = Client(
        name=data['name'], email=data.get('email'), phone=data.get('phone'),
        policy_type=data.get('policyType'), status=data.get('status', 'Prospective')
    )
    db.session.add(new_client)
    db.session.commit()
    return jsonify(new_client.to_dict()), 201

# Add other CRUD endpoints (PUT, DELETE) here if needed
