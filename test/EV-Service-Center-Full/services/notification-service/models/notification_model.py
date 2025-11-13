
from datetime import datetime
from app import db
from sqlalchemy import func

class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    
    notification_type = db.Column(
        db.Enum("booking_status", "inventory_alert", "payment", "reminder", "system", 
                name="notification_types"),
        nullable=False,
        default="system"
    )
    
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    channel = db.Column(
        db.Enum("in_app", "email", "sms", "push", name="notification_channels"),
        nullable=False,
        default="in_app"
    )
    
    status = db.Column(
        db.Enum("pending", "sent", "failed", "read", name="notification_statuses"),
        nullable=False,
        default="pending"
    )
    
    priority = db.Column(
        db.Enum("low", "medium", "high", "urgent", name="notification_priorities"),
        nullable=False,
        default="medium"
    )
    
    related_entity_type = db.Column(db.String(50), nullable=True)
    related_entity_id = db.Column(db.Integer, nullable=True)
    meta_data = db.Column("metadata", db.Text, nullable=True)
    
    scheduled_at = db.Column(db.DateTime, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    read_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, nullable=False, default=func.now())
    updated_at = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "notification_type": str(self.notification_type),
            "title": self.title,
            "message": self.message,
            "channel": str(self.channel),
            "status": str(self.status),
            "priority": str(self.priority),
            "related_entity_type": self.related_entity_type,
            "related_entity_id": self.related_entity_id,
            "metadata": self.metadata,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }