from flask import Blueprint, jsonify
from ..models.client import Client, FollowUp
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    """Provides dashboard statistics including conversions, follow-ups, and renewals."""
    try:
        # Conversions (Active clients created this month)
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        conversions = Client.query.filter(
            Client.status == 'Active',
            Client.last_contact >= start_of_month
        ).count()

        # Upcoming Follow-ups (due today)
        today = datetime.utcnow().date()
        tomorrow = today + timedelta(days=1)
        upcoming_follow_ups = FollowUp.query.filter(
            FollowUp.due_date >= today,
            FollowUp.due_date < tomorrow,
            FollowUp.completed == False
        ).count()

        # Policies nearing renewal (expiring in the next 30 days)
        renewal_window = today + timedelta(days=30)
        renewals_due = Client.query.filter(
            Client.expiration_date >= today,
            Client.expiration_date <= renewal_window
        ).count()

        return jsonify({
            "conversions": conversions,
            "monthlyTarget": 50,  # Mock target
            "followUpsToday": upcoming_follow_ups,
            "renewalsDue": renewals_due,
            "claimsNeedDocs": 3  # Mock data
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@dashboard_bp.route('/recent-clients', methods=['GET'])
def get_recent_clients():
    """Provides the 5 most recently added clients for the dashboard."""
    try:
        # Query the database for the last 5 clients, ordered by ID descending
        recent_clients = Client.query.order_by(Client.id.desc()).limit(5).all()
        return jsonify([client.to_dict() for client in recent_clients])
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500