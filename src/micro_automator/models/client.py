from ..extensions import db
import datetime

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='Prospective')
    
    # Policy Specific Details
    policy_type = db.Column(db.String(100), nullable=True)
    policy_id = db.Column(db.String(100), nullable=True)
    premium_amount = db.Column(db.Float, nullable=True)
    premium_frequency = db.Column(db.String(50), nullable=True)
    expiration_date = db.Column(db.Date, nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    
    # KYC Details
    dob = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(50), nullable=True)
    aadhaar_number = db.Column(db.String(20), nullable=True, unique=True)
    pan_number = db.Column(db.String(20), nullable=True, unique=True)
    photo_url = db.Column(db.String(512), nullable=True)
    
    last_contact = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'status': self.status,
            'policyType': self.policy_type,
            'policyId': self.policy_id,
            'premiumAmount': self.premium_amount,
            'premiumFrequency': self.premium_frequency,
            'expirationDate': self.expiration_date.isoformat() if self.expiration_date else None,
            'dueDate': self.due_date.isoformat() if self.due_date else None,
            'dob': self.dob.isoformat() if self.dob else None,
            'gender': self.gender,
            'aadhaarNumber': self.aadhaar_number,
            'panNumber': self.pan_number,
            'photoUrl': self.photo_url,
            'lastContact': self.last_contact.isoformat(),
        }