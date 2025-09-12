from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def index():
    return "Flask Backend is Running!"

# --- API Endpoints for Core Features ---

@app.route('/api/process_document', methods=['POST'])
def process_document():
    # Placeholder for Intelligent Document Processing
    # In a real app, you'd receive a file, process it with OCR, and extract data
    file = request.files.get('document')
    # For now, we'll simulate a response
    if file:
        return jsonify({
            "status": "success",
            "extracted_data": {
                "policy_number": "POL12345",
                "customer_name": "John Doe",
                "premium_amount": 500.00
            }
        })
    return jsonify({"status": "error", "message": "No document provided"}), 400

@app.route('/api/send_reminder', methods=['POST'])
def send_reminder():
    # Placeholder for Automated Communication
    data = request.get_json()
    customer_email = data.get('email')
    # Simulate sending a reminder
    if customer_email:
        print(f"Sending reminder to {customer_email}")
        return jsonify({"status": "success", "message": f"Reminder sent to {customer_email}"})
    return jsonify({"status": "error", "message": "Email not provided"}), 400

@app.route('/api/process_payment', methods=['POST'])
def process_payment():
    # Placeholder for Payment Automation
    data = request.get_json()
    # In a real app, you would integrate with a payment gateway like Stripe or Razorpay
    return jsonify({
        "status": "success",
        "transaction_id": "TXN98765",
        "amount_processed": data.get('amount')
    })

@app.route('/api/workflow_update', methods=['POST'])
def workflow_update():
    # Placeholder for Workflow Management
    data = request.get_json()
    return jsonify({
        "status": "success",
        "workflow_status": f"Policy {data.get('policy_id')} updated to {data.get('new_status')}"
    })

if __name__ == '__main__':
    app.run(debug=True)
