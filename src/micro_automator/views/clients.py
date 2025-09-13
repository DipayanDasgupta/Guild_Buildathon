from flask import Blueprint, jsonify

clients_bp = Blueprint('clients', __name__)

# In a real app, this data would come from your PostgreSQL database.
# For the buildathon, we'll use mock data to demonstrate the API connection.
mock_clients_data = [
    {"id": "1", "name": "John Smith", "policyType": "Auto Insurance", "status": "Active", "premium": 1200},
    {"id": "2", "name": "Sarah Johnson", "policyType": "Home Insurance", "status": "Pending", "premium": 2400},
    {"id": "3", "name": "Michael Brown", "policyType": "Life Insurance", "status": "Active", "premium": 3600},
]

@clients_bp.route('/', methods=['GET'])
def get_clients():
    """Provides a list of clients for the dashboard table."""
    # In the future, you would query your database here:
    # clients = ClientModel.query.all()
    # return jsonify([client.to_dict() for client in clients])
    return jsonify(mock_clients_data)
