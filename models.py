from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    group = db.Column(db.String(50), nullable=False)
    avatar = db.Column(db.String(120), default="default.jpg")
    feed_visibility = db.Column(db.String(20), default=None)  # 'public' or 'friends'

    plates = db.relationship("Plate", backref="user", lazy=True)

class Plate(db.Model):
    __table_args__ = {'extend_existing': True}  # Allow extending the existing table
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime)
    interested = db.Column(db.Integer, default=0)
    image = db.Column(db.String(200))  # ✅ new column
