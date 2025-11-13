# File: services/user-service/models/profile.py

from datetime import datetime
from app import db  # ✅ Import từ app


class Profile(db.Model):
    __tablename__ = "profiles"

    profile_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False, unique=True)

    full_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    avatar_url = db.Column(db.String(255))
    address = db.Column(db.Text)
    bio = db.Column(db.Text)
    vehicle_model = db.Column(db.String(100))
    vin_number = db.Column(db.String(100))

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="profile")