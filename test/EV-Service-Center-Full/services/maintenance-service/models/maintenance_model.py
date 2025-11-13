# File: services/maintenance-service/models/maintenance_model.py
from app import db 
from sqlalchemy import func

# Định nghĩa các trạng thái của Công việc bảo trì
TASK_STATUSES = db.Enum(
    "pending", "in_progress", "completed", "failed", 
    name="maintenance_task_statuses"
)

class MaintenanceTask(db.Model):
    __tablename__ = "maintenance_tasks"

    id = db.Column(db.Integer, primary_key=True, index=True)
    # Booking ID là external key, mỗi booking chỉ có thể có 1 task
    booking_id = db.Column(db.Integer, unique=True, nullable=False, index=True) 
    # User ID để dễ tra cứu
    user_id = db.Column(db.Integer, nullable=False, index=True) 
    # Thông tin xe (VIN) lấy từ Booking/User Profile
    vehicle_vin = db.Column(db.String(100), nullable=False)
    
    # Mô tả công việc (Lấy từ Booking service_type)
    description = db.Column(db.String(255), nullable=False)
    # Kỹ thuật viên phụ trách
    technician_id = db.Column(db.Integer, nullable=False) 
    
    # Trạng thái công việc
    status = db.Column(
        TASK_STATUSES,
        nullable=False,
        default="pending"
    )

    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Chuyển đổi đối tượng sang dictionary để trả về API"""
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "user_id": self.user_id,
            "vehicle_vin": self.vehicle_vin,
            "description": self.description,
            "technician_id": self.technician_id,
            "status": str(self.status),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }