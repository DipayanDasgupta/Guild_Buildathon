from ..extensions import db
import datetime
class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    extracted_data = db.Column(db.JSON, nullable=True)
    ai_summary = db.Column(db.Text, nullable=True)
    ai_category = db.Column(db.String(100), nullable=True)
    ai_sentiment = db.Column(db.String(50), nullable=True)
    ai_action_items = db.Column(db.JSON, nullable=True)
    def to_dict(self):
        return { 'id': self.id, 'filename': self.filename, 'upload_date': self.upload_date.isoformat(), 'extracted_data': self.extracted_data, 'ai_summary': self.ai_summary, 'ai_category': self.ai_category, 'ai_sentiment': self.ai_sentiment, 'ai_action_items': self.ai_action_items }
