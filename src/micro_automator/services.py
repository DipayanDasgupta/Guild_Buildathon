import re
from .extensions import db
from .models import AuditLog, Reminder
from datetime import datetime, timedelta

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
    # Note: The calling function is responsible for the db.session.commit()

def schedule_renewal_reminder(client, days_before=15):
    """Creates a policy renewal reminder for a client."""
    if not client or not client.expiration_date:
        return None
    
    due_at = datetime.combine(client.expiration_date, datetime.min.time()) - timedelta(days=days_before)
    reminder = Reminder(
        client_id=client.id,
        message=f"Policy {client.policy_id} for {client.name} is due for renewal on {client.expiration_date.strftime('%Y-%m-%d')}.",
        due_at=due_at
    )
    db.session.add(reminder)
    log_audit_event("renewal_reminder_scheduled", {"client_id": client.id, "due_at": due_at.isoformat()})
    return reminder