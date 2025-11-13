# File: services/booking-service/models/booking_model.py
from datetime import datetime
from app import db 
from sqlalchemy import func

class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True, index=True)
    # user_id lưu trữ ID từ User Service (External Key)
    user_id = db.Column(db.Integer, nullable=False, index=True) 
    
    customer_name = db.Column(db.String(100), nullable=False)
    service_type = db.Column(db.String(100), nullable=False)
    
    # Giả định Kỹ thuật viên và Trạm được quản lý ở đây
    technician_id = db.Column(db.Integer, nullable=False)
    station_id = db.Column(db.Integer, nullable=False)
    
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    
    status = db.Column(
        db.Enum("pending", "confirmed", "canceled", "completed", name="booking_statuses"),
        nullable=False,
        default="pending"
    )

    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Chuyển đổi đối tượng Booking thành dictionary để trả về API"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "customer_name": self.customer_name,
            "service_type": self.service_type,
            "technician_id": self.technician_id,
            "station_id": self.station_id,
            # Chuyển đổi datetime sang chuỗi ISO 8601
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            # ✅ Đảm bảo Enum được convert thành string
            "status": str(self.status), 
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }