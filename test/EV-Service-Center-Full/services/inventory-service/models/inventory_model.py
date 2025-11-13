# File: services/inventory-service/models/inventory_model.py
from datetime import datetime
from app import db # Dùng db từ app.py
from sqlalchemy import func

class Inventory(db.Model):
    __tablename__ = "inventory"

    id = db.Column(db.Integer, primary_key=True, index=True)
    part_number = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    min_quantity = db.Column(db.Integer, nullable=False, default=10)
    price = db.Column(db.Float, nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Chuyển đổi đối tượng Inventory thành dictionary để trả về API"""
        return {
            "id": self.id,
            "name": self.name,
            "part_number": self.part_number,
            "quantity": self.quantity,
            "min_quantity": self.min_quantity,
            "price": self.price,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }