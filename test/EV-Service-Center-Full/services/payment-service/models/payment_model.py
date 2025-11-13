# File: services/payment-service/models/payment_model.py
from app import db 
from sqlalchemy import func

# Định nghĩa các trạng thái của Giao dịch thanh toán
PAYMENT_STATUSES = db.Enum(
    "pending", "success", "failed", "expired", 
    name="payment_transaction_statuses"
)

# Định nghĩa các Phương thức thanh toán
PAYMENT_METHODS = db.Enum(
    "bank_transfer", "momo_qr", 
    name="payment_methods"
)

class PaymentTransaction(db.Model):
    __tablename__ = "payment_transactions"

    id = db.Column(db.Integer, primary_key=True, index=True)
    # External Key đến Finance Service Invoice
    invoice_id = db.Column(db.Integer, nullable=False, index=True) 
    # User ID để dễ tra cứu lịch sử
    user_id = db.Column(db.Integer, nullable=False, index=True)
    
    amount = db.Column(db.Float, nullable=False)
    
    method = db.Column(
        PAYMENT_METHODS,
        nullable=False
    )
    
    # ID giao dịch từ Cổng Thanh toán (dùng để tra cứu)
    pg_transaction_id = db.Column(db.String(255), nullable=True, unique=True)
    
    status = db.Column(
        PAYMENT_STATUSES,
        nullable=False,
        default="pending"
    )

    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Mô tả dữ liệu cần thiết cho FE (QR data, Bank info,...)
    payment_data_json = db.Column(db.Text, nullable=True) 

    def to_dict(self):
        """Chuyển đổi đối tượng sang dictionary để trả về API"""
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "method": str(self.method),
            "pg_transaction_id": self.pg_transaction_id,
            "status": str(self.status),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "payment_data": self.payment_data_json # Frontend sẽ parse chuỗi JSON này
        }