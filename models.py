from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Relationship with scan results
    scan_results = db.relationship('ScanResult', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username
        }

class ScanResult(db.Model):
    __tablename__ = 'scan_results'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    scan_time = db.Column(db.DateTime, server_default=db.func.now())
    vulnerabilities = db.Column(db.JSON)
    pods = db.Column(db.JSON)
    cves = db.Column(db.JSON)
    summary = db.Column(db.JSON)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'scan_time': self.scan_time.isoformat() if self.scan_time else None,
            'vulnerabilities': self.vulnerabilities,
            'pods': self.pods,
            'cves': self.cves,
            'summary': self.summary
        }
