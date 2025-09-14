from ..extensions import db
import datetime

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    due_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default='pending') # pending, sent, failed
    
    client = db.relationship('Client', backref=db.backref('reminders', lazy=True, cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            'id': self.id,
            'clientId': self.client_id,
            'message': self.message,
            'dueAt': self.due_at.isoformat(),
            'status': self.status,
        }

class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(100), nullable=False)
    details = db.Column(db.JSON, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)