# File: services/inventory-service/services/inventory_service.py
import requests
import os
from app import db
from models.inventory_model import Inventory # Giả định import model từ thư mục models
class InventoryService:
    """Service xử lý logic nghiệp vụ liên quan đến Inventory"""

    @staticmethod
    def get_item_by_id(item_id):
        """Lấy vật tư theo ID"""
        #
        return Inventory.query.get(item_id)

    @staticmethod
    def get_item_by_part_number(part_number):
        """Lấy vật tư theo Part Number (Mã phụ tùng)"""
        #
        return Inventory.query.filter_by(part_number=part_number).first()

    @staticmethod
    def get_all_items():
        """Lấy tất cả vật tư"""
        #
        return Inventory.query.all()

    @staticmethod
    def get_low_stock_items(min_quantity=10):
        """Lấy các vật tư có tồn kho thấp hơn mức tối thiểu"""
        #
        return Inventory.query.filter(Inventory.quantity <= Inventory.min_quantity).all()

    @staticmethod
    def create_item(data):
        """Tạo vật tư mới"""
        #
        part_number = data.get("part_number")
        if InventoryService.get_item_by_part_number(part_number):
            return None, f"Part number '{part_number}' already exists"

        new_item = Inventory(
            part_number=part_number,
            name=data.get("name"),
            quantity=data.get("quantity", 0),
            min_quantity=data.get("min_quantity", 10),
            price=data.get("price")
        )

        try:
            db.session.add(new_item)
            db.session.commit()
            return new_item, None
        except Exception as e:
            db.session.rollback()
            return None, f"Error creating item: {str(e)}"

    @staticmethod
    def update_item(item_id, data):
        """Cập nhật vật tư"""
        #
        item = InventoryService.get_item_by_id(item_id)
        if not item:
            return None, "Item not found"

        try:
            for field, value in data.items():
                if hasattr(item, field):
                    setattr(item, field, value)

            db.session.commit()
            return item, None
        except Exception as e:
            db.session.rollback()
            return None, f"Error updating item: {str(e)}"

    @staticmethod
    def delete_item(item_id):
        """Xóa vật tư"""
        #
        item = InventoryService.get_item_by_id(item_id)
        if not item:
            return False, "Item not found"

        try:
            db.session.delete(item)
            db.session.commit()
            return True, "Item deleted successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Error deleting item: {str(e)}"
    @staticmethod
    def _send_low_stock_alert(item):
        """Send alert when stock is low"""
        try:
            # Get admin users (you might need to call User Service)
            # For now, hardcode admin_id or get from config
            admin_id = 1  # Replace with actual admin user_id
            
            url = "http://notification-service:8005/internal/notifications/create"
            headers = {
                "X-Internal-Token": os.getenv("INTERNAL_SERVICE_TOKEN"),
                "Content-Type": "application/json"
            }
            data = {
                "user_id": admin_id,
                "notification_type": "inventory_alert",
                "title": "⚠️ Cảnh báo tồn kho thấp",
                "message": f"Phụ tùng '{item.name}' chỉ còn {item.quantity} (tối thiểu: {item.min_quantity})",
                "channel": "in_app",
                "priority": "urgent",
                "related_entity_type": "inventory",
                "related_entity_id": item.id
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=5)
            return response.status_code == 201
        except Exception as e:
            print(f"Failed to send alert: {e}")
            return False
    
    @staticmethod
    def update_item(item_id, data):
        # ... existing update code ...
        
        # After update, check if stock is low
        if item and item.quantity < item.min_quantity:
            InventoryService._send_low_stock_alert(item)
        
        return item, None
    @staticmethod
    def _get_admin_user_ids():
        """Lấy danh sách admin IDs (có thể gọi User Service)"""
        # TODO: Gọi User Service để lấy danh sách admin
        # Tạm thời hardcode
        return [1]  # Replace with actual admin IDs
    
    @staticmethod
    def _notify_low_stock(item):
        """Cảnh báo tồn kho thấp đến Admin"""
        from notification_helper import NotificationHelper
        
        admin_ids = InventoryService._get_admin_user()
        
        title = "⚠️ Cảnh báo tồn kho thấp"
        message = f"Phụ tùng '{item.name}' (#{item.part_number}) chỉ còn {item.quantity} (tối thiểu: {item.min_quantity}). Cần nhập hàng ngay!"
        
        return NotificationHelper.send_to_multiple_users(
            user_ids=admin_ids,
            notification_type="inventory_alert",
            title=title,
            message=message,
            channel="in_app",
            priority="urgent",
            related_entity_type="inventory",
            related_entity_id=item.id,
            metadata={
                "part_number": item.part_number,
                "current_quantity": item.quantity,
                "min_quantity": item.min_quantity,
                "difference": item.min_quantity - item.quantity
            }
        )
    
    @staticmethod
    def _notify_out_of_stock(item):
        """Cảnh báo hết hàng"""
        from notification_helper import NotificationHelper
        
        admin_ids = InventoryService._get_admin_user_ids()
        
        return NotificationHelper.send_to_multiple_users(
            user_ids=admin_ids,
            notification_type="inventory_alert",
            title="🚨 HẾT HÀNG KHẨN CẤP",
            message=f"Phụ tùng '{item.name}' (#{item.part_number}) ĐÃ HẾT HÀNG!",
            channel="in_app",
            priority="urgent",
            related_entity_type="inventory",
            related_entity_id=item.id
        )
    
    @staticmethod
    def update_item(item_id, data):
        item = InventoryService.get_item_by_id(item_id)
        if not item:
            return None, "Item not found"
        
        old_quantity = item.quantity
        
        try:
            # Update item
            for key, value in data.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            
            db.session.commit()
            
            # ✅ THÊM: Kiểm tra và gửi cảnh báo
            if item.quantity == 0 and old_quantity > 0:
                # Hết hàng
                InventoryService._notify_out_of_stock(item)
            elif item.quantity < item.min_quantity and old_quantity >= item.min_quantity:
                # Tồn kho thấp (chỉ gửi khi vừa giảm xuống dưới ngưỡng)
                InventoryService._notify_low_stock(item)
            
            return item, None
        except Exception as e:
            db.session.rollback()
            return None, f"Error: {str(e)}"
    @staticmethod
    def _notify_welcome_new_user(user):
        """Chào mừng người dùng mới"""
        from notification_helper import NotificationHelper
        
        return NotificationHelper.send_notification(
            user_id=user.id,
            notification_type="system",
            title="👋 Chào mừng đến với EV Service Center",
            message=f"Xin chào {user.username}! Cảm ơn bạn đã đăng ký tài khoản. Chúng tôi sẵn sàng phục vụ bạn!",
            channel="in_app",
            priority="medium"
        )
    
    @staticmethod
    def _notify_password_changed(user):
        """Thông báo đổi mật khẩu"""
        from notification_helper import NotificationHelper
        
        return NotificationHelper.send_notification(
            user_id=user.id,
            notification_type="system",
            title="🔐 Mật khẩu đã được thay đổi",
            message="Mật khẩu của bạn đã được thay đổi thành công. Nếu không phải bạn, vui lòng liên hệ ngay!",
            channel="in_app",
            priority="high"
        )


