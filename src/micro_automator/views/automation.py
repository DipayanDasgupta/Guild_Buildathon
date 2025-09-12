from flask import Blueprint, request, jsonify

automation_bp = Blueprint('automation', __name__)

@automation_bp.route('/send_reminder', methods=['POST'])
def send_reminder():
    """
    API endpoint for Automated Communication.
    Receives customer info and sends a templated reminder.
    """
    data = request.get_json()
    if not data or 'email' not in data or 'name' not in data:
        return jsonify({"status": "error", "message": "Missing 'email' or 'name' in request body"}), 400

    # --- COMMUNICATION API INTEGRATION POINT ---
    # Here you would integrate with an email service like SendGrid, Mailgun, or AWS SES.
    # You can create dynamic email templates for different scenarios (payment due, renewal, etc.).
    print(f"SIMULATING: Sending reminder to {data['name']} at {data['email']} for policy {data.get('policy_id')}")

    return jsonify({
        "status": "success",
        "message": f"Reminder successfully queued for sending to {data['email']}."
    })
