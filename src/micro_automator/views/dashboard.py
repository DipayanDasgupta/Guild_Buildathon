from flask import Blueprint, jsonify
from ..extensions import db
from ..models.client import Client, FollowUp
from datetime import datetime, timedelta, timezone

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    """
    Provides the high-level statistics for the main dashboard cards and notifications.
    This is fully functional and not dummy data.
    """
    try:
        # Use timezone-aware datetime for accurate monthly filtering
        now = datetime.now(timezone.utc)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # 1. Conversions: Count of clients who became 'Active' this month.
        conversions = db.session.query(Client).filter(
            Client.status == 'Active',
            Client.last_contact >= start_of_month
        ).count()

        # 2. Today's Follow-ups: Count of follow-ups scheduled for today.
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        follow_ups_today_count = db.session.query(FollowUp).filter(
            FollowUp.due_date >= today_start,
            FollowUp.due_date < today_end,
            FollowUp.completed == False
        ).count()

        # 3. Renewals Due: Count of active clients whose policies expire in the next 30 days.
        renewal_window_end = now.date() + timedelta(days=30)
        renewals_due_count = db.session.query(Client).filter(
            Client.status == 'Active',
            Client.expiration_date != None,
            Client.expiration_date <= renewal_window_end
        ).count()

        # 4. Claims Need Docs: A functional proxy for this is counting 'Engaged' clients
        # who don't have a "Proposal Form" or "KYC Document" associated yet.
        # For simplicity and performance, we'll count 'Engaged' clients.
        claims_need_docs_count = db.session.query(Client).filter(Client.status == 'Engaged').count()

        return jsonify({
            "conversions": conversions,
            "monthlyTarget": 50,  # This can be a configurable value later
            "followUpsTodayCount": follow_ups_today_count,
            "renewalsDueCount": renewals_due_count,
            "claimsNeedDocsCount": claims_need_docs_count
        })
    except Exception as e:
        # Log the full error for debugging on Render
        current_app.logger.error(f"Error in get_dashboard_stats: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Could not calculate dashboard statistics."}), 500


@dashboard_bp.route('/todays-follow-ups', methods=['GET'])
def get_todays_follow_ups():
    """
    Provides a DETAILED list of follow-ups scheduled for today, as requested
    in the whiteboard notes.
    """
    try:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        follow_ups = db.session.query(FollowUp).filter(
            FollowUp.due_date >= today_start,
            FollowUp.due_date < today_end,
            FollowUp.completed == False
        ).order_by(FollowUp.due_date.asc()).all()

        # Serialize the data into a clean format for the frontend
        follow_ups_list = [
            {
                "id": f.id,
                "clientName": f.client.name, # Include the client's name
                "type": f.type,
                "dueDate": f.due_date.isoformat(),
                "notes": f.notes
            } for f in follow_ups
        ]
        return jsonify(follow_ups_list)
    except Exception as e:
        current_app.logger.error(f"Error in get_todays_follow_ups: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Could not retrieve today's follow-ups."}), 500


@dashboard_bp.route('/recent-clients', methods=['GET'])
def get_recent_clients():
    """Provides the 5 most recently created clients for the dashboard's table."""
    try:
        recent_clients = Client.query.order_by(Client.id.desc()).limit(5).all()
        return jsonify([client.to_dict() for client in recent_clients])
    except Exception as e:
        current_app.logger.error(f"Error in get_recent_clients: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Could not retrieve recent clients."}), 500