# File: services/finance-service/models/finance_model.py
from app import db
from sqlalchemy import func
from sqlalchemy.orm import relationship

# Định nghĩa các trạng thái của Hóa đơn
INVOICE_STATUSES = db.Enum(
    "pending", "issued", "paid", "canceled", 
    name="invoice_statuses"
)
# Định nghĩa loại mặt hàng
ITEM_TYPES = db.Enum(
    "service", "part",
    name="invoice_item_types"
)

class Invoice(db.Model):
    __tablename__ = "invoices"
    id = db.Column(db.Integer, primary_key=True, index=True)
    # Không dùng ForeignKey cứng vì là Microservices, nhưng vẫn đảm bảo unique
    booking_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(
        INVOICE_STATUSES,
        nullable=False,
        default="issued"
    )
    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())
    items = db.relationship(
        "InvoiceItem", 
        back_populates="invoice", 
        lazy="dynamic", 
        cascade="all, delete-orphan"
    )
    def to_dict(self):
        """Chuyển đổi Invoice sang dictionary để trả về API"""
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "user_id": self.user_id,
            "total_amount": self.total_amount,
            "status": str(self.status),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class InvoiceItem(db.Model):
    __tablename__ = "invoice_items"
    id = db.Column(db.Integer, primary_key=True, index=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=False, index=True)
    item_type = db.Column(ITEM_TYPES, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    sub_total = db.Column(db.Float, nullable=False) 
    invoice = db.relationship("Invoice", back_populates="items")
    
    def to_dict(self):
        """Chuyển đổi InvoiceItem sang dictionary"""
        return {
            "id": self.id,
            "description": self.description,
            "item_type": str(self.item_type),
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "sub_total": self.sub_total
        }