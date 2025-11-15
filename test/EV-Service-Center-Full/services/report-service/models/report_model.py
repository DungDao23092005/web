# File: services/report-service/models/report_model.py
from app import db 
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB

# Định nghĩa các trạng thái của Báo cáo
REPORT_STATUSES = db.Enum(
    "pending", "processing", "completed", "failed", 
    name="report_statuses"
)

# Định nghĩa các loại Báo cáo
REPORT_TYPES = db.Enum(
    "sales_summary", "user_activity", "inventory_levels", 
    name="report_types"
)

class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True, index=True)
    
    # Người yêu cầu (Admin)
    requested_by_id = db.Column(db.Integer, nullable=False, index=True) 
    
    report_type = db.Column(REPORT_TYPES, nullable=False, default="sales_summary")
    
    status = db.Column(REPORT_STATUSES, nullable=False, default="pending")
    
    # Lưu kết quả báo cáo dưới dạng JSON
    report_data = db.Column(JSONB, nullable=True)
    
    error_message = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    generated_at = db.Column(db.DateTime, nullable=True) # Khi hoàn thành

    def to_dict(self):
        """Chuyển đổi đối tượng sang dictionary để trả về API"""
        return {
            "id": self.id,
            "requested_by_id": self.requested_by_id,
            "report_type": str(self.report_type),
            "status": str(self.status),
            "report_data": self.report_data,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None
        }