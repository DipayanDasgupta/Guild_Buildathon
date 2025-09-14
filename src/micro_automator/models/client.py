from ..extensions import db
import datetime

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), default='Prospective')  # Prospective, Engaged, Active
    policy_type = db.Column(db.String(100), nullable=True)
    policy_id = db.Column(db.String(100), nullable=True)
    premium_amount = db.Column(db.Float, nullable=True)
    expiration_date = db.Column(db.Date, nullable=True)
    last_contact = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    follow_ups = db.relationship('FollowUp', backref='client', lazy=True, cascade="all, delete-orphan")
    forms = db.relationship('Form', backref='client', lazy=True, cascade="all, delete-orphan")

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
            'expirationDate': self.expiration_date.isoformat() if self.expiration_date else None,
            'lastContact': self.last_contact.isoformat(),
            'nextFollowUp': self.get_next_follow_up_date(),
            'forms_status': self.get_forms_status()
        }

    def get_next_follow_up_date(self):
        next_follow_up = FollowUp.query.filter_by(client_id=self.id, completed=False).order_by(FollowUp.due_date.asc()).first()
        return next_follow_up.due_date.isoformat() if next_follow_up else None

    def get_forms_status(self):
        # A helper to quickly see the documentation stage
        required = ['Aadhaar', 'PAN', 'Proposal Form']
        uploaded = [form.form_type for form in self.forms]
        if all(r in uploaded for r in required):
            return "Complete"
        elif any(r in uploaded for r in required):
            return "Partial"
        else:
            return "Pending"

class FollowUp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'Call' or 'Text'
    notes = db.Column(db.Text, nullable=True)
    completed = db.Column(db.Boolean, default=False)

class Form(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    form_type = db.Column(db.String(100), nullable=False)  # e.g., Aadhaar, PAN, Proposal Form
    status = db.Column(db.String(50), default='Uploaded')
    file_url = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)