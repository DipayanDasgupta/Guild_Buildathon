from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models.client import Client

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/', methods=['GET'])
def get_clients():
    """Fetches all clients from the database."""
    clients = Client.query.order_by(Client.name).all()
    return jsonify([client.to_dict() for client in clients])

@clients_bp.route('/', methods=['POST'])
def add_client():
    """Adds a new client to the database."""
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"status": "error", "message": "Client name is required"}), 400
    
    new_client = Client(name=data.get('name'), status='Pending')
    db.session.add(new_client)
    db.session.commit()
    return jsonify(new_client.to_dict()), 201

@clients_bp.route('/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    """Deletes a client from the database."""
    client = Client.query.get(client_id)
    if client is None:
        return jsonify({"status": "error", "message": "Client not found"}), 404
    
    db.session.delete(client)
    db.session.commit()
    return jsonify({"status": "success", "message": "Client deleted successfully"}), 200
