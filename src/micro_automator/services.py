import re
from datetime import datetime, timedelta
from .extensions import db
from .models import AuditLog, Reminder

RE_EMAIL = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
RE_AADHAAR = re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")
RE_PAN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b")

def redact_pii(text: str) -> str:
    """Finds and redacts common PII from a block of text."""
    text = RE_EMAIL.sub("[REDACTED_EMAIL]", text)
    text = RE_AADHAAR.sub("[REDACTED_AADHAAR]", text)
    text = RE_PAN.sub("[REDACTED_PAN]", text)
    return text

def log_audit_event(event_type: str, details: dict = None):
    """Creates a new audit log entry."""
    audit_log = AuditLog(event_type=event_type, details=details)
    db.session.add(audit_log)
    # The calling function is responsible for the db.session.commit()

def schedule_renewal_reminder(client, days_before=15):
    """
    Creates a policy renewal reminder for a client.
    This function now correctly handles the datetime.date object.
    """
    if not client or not client.expiration_date:
        return None
    
    # client.expiration_date is now a proper date object, so datetime.combine works perfectly.
    due_at = datetime.combine(client.expiration_date, datetime.min.time()) - timedelta(days=days_before)
    
    reminder_message = f"Policy {client.policy_id or 'N/A'} for {client.name} is due for renewal on {client.expiration_date.strftime('%Y-%m-%d')}."
    
    # Check if a similar reminder already exists to avoid duplicates
    existing_reminder = Reminder.query.filter_by(client_id=client.id, message=reminder_message).first()
    if existing_reminder:
        return None # Don't create a duplicate reminder

    reminder = Reminder(
        client_id=client.id,
        message=reminder_message,
        due_at=due_at
    )
    db.session.add(reminder)
    log_audit_event("renewal_reminder_scheduled", {"client_id": client.id, "due_at": due_at.isoformat()})
    return reminder