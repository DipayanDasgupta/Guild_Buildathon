from ..extensions import db
import datetime

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), default='Pending')
    policy_type = db.Column(db.String(100), nullable=True)
    last_contact = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'policyType': self.policy_type,
            'status': self.status,
            'lastContact': self.last_contact.isoformat(),
        }
