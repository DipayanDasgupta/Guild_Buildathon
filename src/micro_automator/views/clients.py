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
        status_filter = request.args.get('status')
        search_term = request.args.get('search')

        if status_filter and status_filter != 'All':
            query = query.filter(Client.status == status_filter)
        
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(or_(Client.name.ilike(search_pattern), Client.policy_id.ilike(search_pattern)))

        clients = query.order_by(Client.name).all()
        return jsonify([client.to_dict() for client in clients])
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@clients_bp.route('/', methods=['POST'])
def add_client():
    """Adds a new client to the database from a JSON payload."""
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"message": "Client name is required"}), 400
    
    # Check if a client with this name already exists
    if Client.query.filter_by(name=data['name']).first():
        return jsonify({"message": "A client with this name already exists."}), 409

    new_client = Client(
        name=data['name'],
        email=data.get('email'),
        phone=data.get('phone'),
        status=data.get('status', 'Prospective')
    )
    db.session.add(new_client)
    db.session.commit()
    return jsonify(new_client.to_dict()), 201

@clients_bp.route('/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    """Deletes a client from the database."""
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    return jsonify({'message': 'Client deleted successfully'})