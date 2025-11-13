import json
from datetime import datetime
from flask import current_app

from app import db
from models.notification_model import Notification

class NotificationService:
    """Service to handle notification business logic"""
    
    @staticmethod
    def create_notification(data):
        """Create a new notification"""
        required_fields = ["user_id", "title", "message"]
        if not all(k in data for k in required_fields):
            return None, "Missing required fields: user_id, title, message"
        
        try:
            notification = Notification(
                user_id=data["user_id"],
                notification_type=data.get("notification_type", "system"),
                title=data["title"],
                message=data["message"],
                channel=data.get("channel", "in_app"),
                priority=data.get("priority", "medium"),
                related_entity_type=data.get("related_entity_type"),
                related_entity_id=data.get("related_entity_id"),
                metadata=json.dumps(data.get("metadata")) if data.get("metadata") else None,
                scheduled_at=datetime.fromisoformat(data["scheduled_at"]) if data.get("scheduled_at") else None
            )
            
            db.session.add(notification)
            db.session.commit()
            
            # Auto-send if not scheduled
            if not notification.scheduled_at:
                NotificationService._send_notification(notification)
            
            return notification, None
        except Exception as e:
            db.session.rollback()
            return None, f"Error creating notification: {str(e)}"
    
    @staticmethod
    def _send_notification(notification):
        """Internal method to send notification"""
        try:
            # Mark as sent (actual sending logic can be added here)
            notification.status = "sent"
            notification.sent_at = datetime.now()
            db.session.commit()
        except Exception as e:
            notification.status = "failed"
            db.session.commit()
            current_app.logger.error(f"Failed to send notification: {str(e)}")
    
    @staticmethod
    def get_user_notifications(user_id, unread_only=False):
        """Get all notifications for a user"""
        query = Notification.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter(Notification.status != "read")
        
        return query.order_by(Notification.created_at.desc()).all()
    
    @staticmethod
    def mark_as_read(notification_id, user_id):
        """Mark notification as read"""
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        
        if not notification:
            return None, "Notification not found"
        
        try:
            notification.status = "read"
            notification.read_at = datetime.now()
            db.session.commit()
            return notification, None
        except Exception as e:
            db.session.rollback()
            return None, f"Error marking as read: {str(e)}"
    
    @staticmethod
    def mark_all_as_read(user_id):
        """Mark all user notifications as read"""
        try:
            Notification.query.filter_by(user_id=user_id).filter(
                Notification.status != "read"
            ).update({
                "status": "read",
                "read_at": datetime.now()
            })
            db.session.commit()
            return True, "All notifications marked as read"
        except Exception as e:
            db.session.rollback()
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def delete_notification(notification_id, user_id):
        """Delete a notification"""
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        
        if not notification:
            return False, "Notification not found"
        
        try:
            db.session.delete(notification)
            db.session.commit()
            return True, "Notification deleted successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def get_all_notifications():
        """Admin: Get all notifications"""
        return Notification.query.order_by(Notification.created_at.desc()).all()
    
    @staticmethod
    def get_notification_stats(user_id):
        """Get notification statistics for a user"""
        total = Notification.query.filter_by(user_id=user_id).count()
        unread = Notification.query.filter_by(user_id=user_id).filter(
            Notification.status != "read"
        ).count()
        
        return {
            "total": total,
            "unread": unread,
            "read": total - unread
        }