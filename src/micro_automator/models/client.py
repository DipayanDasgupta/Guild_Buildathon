from ..extensions import db

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    policy_type = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), default='Pending')
    premium = db.Column(db.Float, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'policyType': self.policy_type,
            'status': self.status,
            'premium': self.premium,
        }
