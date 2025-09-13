from ..extensions import db
import datetime

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), default='Prospective') # New statuses
    policy_type = db.Column(db.String(100), nullable=True)
    policy_id = db.Column(db.String(100), nullable=True)
    premium_amount = db.Column(db.Float, nullable=True)
    premium_frequency = db.Column(db.String(50), nullable=True)
    expiration_date = db.Column(db.Date, nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    last_contact = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'status': self.status,
            'policyType': self.policy_type,
            'policyId': self.policy_id,
            'premiumAmount': self.premium_amount,
            'premiumFrequency': self.premium_frequency,
            'expirationDate': self.expiration_date.isoformat() if self.expiration_date else None,
            'dueDate': self.due_date.isoformat() if self.due_date else None,
            'lastContact': self.last_contact.isoformat(),
        }
