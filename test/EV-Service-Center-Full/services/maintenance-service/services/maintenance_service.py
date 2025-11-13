# File: services/maintenance-service/services/maintenance_service.py
import requests
from flask import current_app
from app import db
from models.maintenance_model import MaintenanceTask 

class MaintenanceService:
    """Service xử lý logic nghiệp vụ về Công việc bảo trì"""
    
    @staticmethod
    def _call_internal_api(service_url, endpoint, method="GET", json_data=None):
        """Hàm nội bộ gọi Internal API của các service khác (Sao chép từ Finance Service)"""
        internal_token = current_app.config.get("INTERNAL_SERVICE_TOKEN")
        url = f"{service_url}{endpoint}"
        headers = {"X-Internal-Token": internal_token}
        
        if not service_url or not internal_token:
             return None, "Lỗi cấu hình Service URL hoặc Internal Token."

        try:
            response = requests.request(method, url, headers=headers, json=json_data)

            if response.status_code == 200 or response.status_code == 201:
                return response.json(), None
            else:
                error_msg = response.json().get('error', f"Lỗi Service (HTTP {response.status_code})")
                return None, error_msg
        except requests.exceptions.RequestException as e:
            return None, f"Lỗi kết nối Service: {str(e)}"

    @staticmethod
    def _get_booking_details(booking_id):
        """Lấy chi tiết Booking từ Booking Service"""
        booking_url = current_app.config.get("BOOKING_SERVICE_URL")
        return MaintenanceService._call_internal_api(booking_url, f"/internal/bookings/items/{booking_id}")

    @staticmethod
    def _get_user_profile(user_id):
        """Lấy thông tin User từ User Service"""
        user_url = current_app.config.get("USER_SERVICE_URL")
        # Gọi Internal Endpoint của User Service
        return MaintenanceService._call_internal_api(user_url, f"/internal/user/{user_id}")
    
    @staticmethod
    def get_task_by_id(task_id):
        return MaintenanceTask.query.get(task_id)

    @staticmethod
    def get_all_tasks():
        return MaintenanceTask.query.order_by(MaintenanceTask.created_at.desc()).all()

    @staticmethod
    def get_tasks_by_user(user_id):
        return MaintenanceTask.query.filter_by(user_id=int(user_id)).order_by(MaintenanceTask.created_at.desc()).all()

    @staticmethod
    def create_task_from_booking(booking_id, technician_id):
        """Tạo Maintenance Task mới từ một Booking ID"""
        
        if MaintenanceTask.query.filter_by(booking_id=booking_id).first():
            return None, "Công việc cho Booking này đã tồn tại."

        # 1. Lấy chi tiết Booking (lấy user_id và service_type)
        booking_data, error = MaintenanceService._get_booking_details(booking_id)
        if error:
            return None, f"Lỗi khi lấy Booking: {error}"
            
        user_id = booking_data.get('user_id')
        service_type = booking_data.get('service_type')

        # 2. Lấy thông tin User để lấy VIN (Tạm thời Mock VIN vì chưa có Internal Profile Endpoint)
        user_data, error = MaintenanceService._get_user_profile(user_id)
        if error:
            return None, f"Lỗi khi lấy thông tin User: {error}"
        
        # MOCK: Lấy VIN từ Profile (Nếu User Service có Profile Endpoint, ta sẽ dùng nó)
        # Tạm thời gán VIN là một chuỗi Mock
        vehicle_vin = f"VIN_{booking_id}_{user_data.get('username', 'N/A')}" 

        # 3. Tạo Task
        try:
            new_task = MaintenanceTask(
                booking_id=booking_id,
                user_id=user_id,
                vehicle_vin=vehicle_vin, 
                description=service_type,
                technician_id=technician_id,
                status='pending'
            )
            db.session.add(new_task)
            db.session.commit()
            return new_task, None
        except Exception as e:
            db.session.rollback()
            return None, f"Lỗi khi tạo công việc bảo trì: {str(e)}"

    @staticmethod
    def update_task_status(task_id, new_status):
        """Cập nhật trạng thái của Maintenance Task"""
        task = MaintenanceTask.query.get(task_id)
        if not task:
            return None, "Không tìm thấy Công việc bảo trì."

        valid_statuses = [str(s.value) for s in MaintenanceTask.status.type.enums]
        if new_status not in valid_statuses:
            return None, f"Trạng thái '{new_status}' không hợp lệ. Phải là: {', '.join(valid_statuses)}"
        
        try:
            task.status = new_status
            db.session.commit()
            return task, None
        except Exception as e:
            db.session.rollback()
            return None, f"Lỗi khi cập nhật trạng thái: {str(e)}"
    @staticmethod
    def _notify_maintenance_started(maintenance_record):
        """Thông báo bắt đầu bảo dưỡng"""
        from notification_helper import NotificationHelper
        
        return NotificationHelper.send_notification(
            user_id=maintenance_record.customer_id,
            notification_type="booking_status",
            title="🔧 Bắt đầu bảo dưỡng",
            message=f"Xe của bạn đã được tiếp nhận và bắt đầu quá trình bảo dưỡng.",
            channel="in_app",
            priority="medium",
            related_entity_type="maintenance",
            related_entity_id=maintenance_record.id
        )
    
    @staticmethod
    def _notify_maintenance_in_progress(maintenance_record, stage):
        """Thông báo tiến độ bảo dưỡng"""
        from notification_helper import NotificationHelper
        
        stages = {
            "inspection": "Đang kiểm tra tổng thể",
            "repair": "Đang sửa chữa",
            "testing": "Đang kiểm tra cuối cùng",
            "cleaning": "Đang vệ sinh xe"
        }
        
        return NotificationHelper.send_notification(
            user_id=maintenance_record.customer_id,
            notification_type="booking_status",
            title="🔄 Cập nhật tiến độ",
            message=f"Xe của bạn: {stages.get(stage, stage)}",
            channel="in_app",
            priority="low",
            related_entity_type="maintenance",
            related_entity_id=maintenance_record.id,
            metadata={"stage": stage}
        )
    
    @staticmethod
    def _notify_maintenance_completed(maintenance_record):
        """Thông báo hoàn tất bảo dưỡng"""
        from notification_helper import NotificationHelper
        
        return NotificationHelper.send_notification(
            user_id=maintenance_record.customer_id,
            notification_type="booking_status",
            title="✅ Hoàn tất bảo dưỡng",
            message="Xe của bạn đã được bảo dưỡng xong và sẵn sàng để nhận. Vui lòng đến trung tâm để nhận xe!",
            channel="in_app",
            priority="high",
            related_entity_type="maintenance",
            related_entity_id=maintenance_record.id
        )