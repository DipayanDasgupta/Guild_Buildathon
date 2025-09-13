from flask import Blueprint, jsonify, request
from ..extensions import db
from ..models.client import Client
clients_bp = Blueprint('clients', __name__)
@clients_bp.route('/', methods=['GET'])
def get_clients():
    clients = Client.query.order_by(Client.name).all()
    return jsonify([client.to_dict() for client in clients])
@clients_bp.route('/', methods=['POST'])
def add_client():
    data = request.get_json()
    if not data or not data.get('name'): return jsonify({"message": "Client name is required"}), 400
    new_client = Client(name=data['name'], email=data.get('email'), phone=data.get('phone'), policy_type=data.get('policyType'), status=data.get('status', 'Pending'))
    db.session.add(new_client)
    db.session.commit()
    return jsonify(new_client.to_dict()), 201
@clients_bp.route('/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    client = Client.query.get_or_404(client_id)
    data = request.get_json()
    client.name = data.get('name', client.name)
    client.email = data.get('email', client.email)
    client.phone = data.get('phone', client.phone)
    client.policy_type = data.get('policyType', client.policy_type)
    client.status = data.get('status', client.status)
    db.session.commit()
    return jsonify(client.to_dict())
@clients_bp.route('/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    db.session.delete(client)
    db.session.commit()
    return jsonify({'message': 'Client deleted successfully'})
