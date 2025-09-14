from flask import Blueprint, jsonify
from ..extensions import db
from ..models.shared import AuditLog

audits_bp = Blueprint('audits', __name__)

@audits_bp.route('/', methods=['GET'])
def get_all_audit_logs():
    """Fetches all audit log events from the database, most recent first."""
    try:
        logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
        
        # Manually serialize the data to send back as JSON
        logs_list = [
            {
                "id": log.id,
                "eventType": log.event_type,
                "details": log.details,
                "timestamp": log.timestamp.isoformat()
            } for log in logs
        ]
        
        return jsonify(logs_list)
    except Exception as e:
        # It's good practice to log the error on the server
        current_app.logger.error(f"Error fetching audit logs: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Could not retrieve audit logs."}), 500