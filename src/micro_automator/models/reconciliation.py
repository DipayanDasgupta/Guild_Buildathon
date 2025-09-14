from ..extensions import db
import datetime

class ReconciliationBatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.String(50), default='Completed')
    transactions = db.relationship('Transaction', backref='batch', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('reconciliation_batch.id'), nullable=False)
    source = db.Column(db.String(50), nullable=False) # 'bank_statement' or 'policy_log'
    transaction_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    reference_id = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='unmatched') # unmatched, matched, reconciled
    match_id = db.Column(db.Integer, nullable=True) # To link matched pairs

    def to_dict(self):
        return {
            'id': self.id,
            'source': self.source,
            'date': self.transaction_date.isoformat(),
            'amount': self.amount,
            'referenceId': self.reference_id,
            'description': self.description,
            'status': self.status,
            'matchId': self.match_id
        }