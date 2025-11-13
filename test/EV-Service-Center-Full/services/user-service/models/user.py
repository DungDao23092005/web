# File: services/user-service/models/user.py

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db  # ✅ Import từ app


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(
        db.Enum("user", "admin", name="user_roles"),
        nullable=False,
        default="user"
    )
    status = db.Column(
        db.Enum("active", "locked", name="user_statuses"),
        nullable=False,
        default="active"
    )

    # Relationship to Profile (one-to-one)
    profile = db.relationship(
        "Profile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)