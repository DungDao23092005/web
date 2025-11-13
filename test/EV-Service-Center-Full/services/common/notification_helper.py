import requests
import os
from typing import Optional, Dict, Any
from flask import current_app

class NotificationHelper:
    """Helper class để gửi notifications từ các services"""
    
    NOTIFICATION_SERVICE_URL = "http://notification-service:8005"
    
    @staticmethod
    def send_notification(
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        channel: str = "in_app",
        priority: str = "medium",
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send notification to user
        
        Args:
            user_id: User ID to send notification to
            notification_type: booking_status, inventory_alert, payment, reminder, system
            title: Notification title
            message: Notification message
            channel: in_app, email, sms, push
            priority: low, medium, high, urgent
            related_entity_type: booking, invoice, inventory, etc.
            related_entity_id: ID of related entity
            metadata: Additional data as dict
        """
        try:
            url = f"{NotificationHelper.NOTIFICATION_SERVICE_URL}/internal/notifications/create"
            headers = {
                "X-Internal-Token": os.getenv("INTERNAL_SERVICE_TOKEN"),
                "Content-Type": "application/json"
            }
            data = {
                "user_id": user_id,
                "notification_type": notification_type,
                "title": title,
                "message": message,
                "channel": channel,
                "priority": priority,
                "related_entity_type": related_entity_type,
                "related_entity_id": related_entity_id,
                "metadata": metadata
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=5)
            
            if response.status_code == 201:
                current_app.logger.info(f"Notification sent to user {user_id}: {title}")
                return True
            else:
                current_app.logger.warning(f"Failed to send notification: {response.text}")
                return False
                
        except Exception as e:
            current_app.logger.error(f"Error sending notification: {str(e)}")
            return False
    
    @staticmethod
    def send_to_multiple_users(
        user_ids: list,
        notification_type: str,
        title: str,
        message: str,
        **kwargs
    ) -> Dict[str, int]:
        """Send notification to multiple users"""
        success = 0
        failed = 0
        
        for user_id in user_ids:
            if NotificationHelper.send_notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                **kwargs
            ):
                success += 1
            else:
                failed += 1
        
        return {"success": success, "failed": failed}