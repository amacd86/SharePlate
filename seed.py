print("👋 seed.py started running...")

from app import app, db
from models import User, Plate
from werkzeug.security import generate_password_hash
from datetime import datetime

with app.app_context():
    print("🔄 Dropping and recreating all tables...")
    db.drop_all()
    db.create_all()
    print("✅ Tables created")

    print("➕ Creating Gus...")
    gus = User(
        name="Gus",
        email="gus@example.com",
        password=generate_password_hash("password123"),
        group="Aldrich Group",
        avatar="gus.jpg"
    )

    print("🍽️ Adding a test plate...")
    plate1 = Plate(
        user=gus,
        title="Leftover Chili",
        description="Spicy, vegetarian chili with black beans and corn.",
        timestamp=datetime.now(),
        interested=2
    )

    db.session.add_all([gus, plate1])
    db.session.commit()

    print("✅ Seeded database with Gus and one plate.")
    print("🧪 Columns in User table:", [col.name for col in User.__table__.columns])
