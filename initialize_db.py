from app import app
from models import db, User, Plate

with app.app_context():
    print("🔁 Dropping all tables...")
    db.drop_all()  # Drop all tables to reset the schema
    print("✅ Tables dropped.")

    print("🎉 Creating tables...")
    db.create_all()  # Recreate tables based on the updated models
    print("🧪 Plate columns:", [c.name for c in Plate.__table__.columns])  # Confirm schema
    print("✅ All tables created.")
