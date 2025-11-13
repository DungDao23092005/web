# File: services/booking-service/services/booking_service.py
import os
from datetime import datetime
from flask import current_app
from sqlalchemy import and_, or_
import requests 

from app import db
from models.booking_model import Booking # ✅ Sửa lỗi: Đã đổi về absolute import (Giả định path đã được set trong app.py)

class BookingService:
    """Service xử lý logic nghiệp vụ liên quan đến Đặt lịch"""
    
    @staticmethod
    def _verify_user(user_id):
        """Hàm nội bộ: Gọi User Service để xác minh User tồn tại"""
        user_service_url = current_app.config.get("USER_SERVICE_URL")
        internal_token = current_app.config.get("INTERNAL_SERVICE_TOKEN")
        
        if not user_service_url or not internal_token:
            return None, "Lỗi cấu hình Service URL hoặc Internal Token"

        try:
            # Gọi Internal API của User Service
            url = f"{user_service_url}/internal/user/{user_id}"
            headers = {"X-Internal-Token": internal_token}
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                return user_data, None
            else:
                return None, f"User Service lỗi: {response.json().get('error', 'Không tìm thấy người dùng')}"
        except requests.exceptions.RequestException as e:
            return None, f"Lỗi kết nối User Service: {str(e)}"

    @staticmethod
    def is_time_available(technician_id, station_id, start_time, end_time, exclude_booking_id=None):
        """Kiểm tra xem lịch có bị trùng không"""
        
        dt_start = datetime.fromisoformat(start_time)
        dt_end = datetime.fromisoformat(end_time)
        
        query = Booking.query.filter(
            and_(
                Booking.status == 'confirmed',
                Booking.technician_id == technician_id,
                Booking.station_id == station_id,
                or_(
                    and_(Booking.start_time <= dt_start, Booking.end_time > dt_start),
                    and_(Booking.start_time < dt_end, Booking.end_time >= dt_end),
                    and_(Booking.start_time >= dt_start, Booking.end_time <= dt_end)
                )
            )
        )
        
        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)

        return query.count() == 0

    @staticmethod
    def create_booking(data):
        """Tạo lịch đặt mới"""
        required_fields = ["user_id", "service_type", "technician_id", "station_id", "start_time", "end_time"]
        if not all(k in data for k in required_fields):
            return None, "Thiếu thông tin đặt lịch bắt buộc."
        
        user_id = data['user_id']
        start_time = data['start_time']
        end_time = data['end_time']
        technician_id = data['technician_id']
        station_id = data['station_id']
        
        # 1. Xác minh người dùng tồn tại
        user_data, user_error = BookingService._verify_user(user_id)
        if user_error:
            return None, user_error
        
        # 2. Kiểm tra trùng lịch
        if not BookingService.is_time_available(technician_id, station_id, start_time, end_time):
            return None, "Thời gian này đã có lịch hẹn trùng."

        # 3. Tạo Booking
        try:
            customer_name = user_data.get('username') 
            
            new_booking = Booking(
                user_id=user_id,
                customer_name=customer_name, 
                service_type=data["service_type"],
                technician_id=technician_id,
                station_id=station_id,
                start_time=datetime.fromisoformat(start_time),
                end_time=datetime.fromisoformat(end_time),
                status='confirmed'
            )
            
            db.session.add(new_booking)
            db.session.commit()
            return new_booking, None
        except Exception as e:
            db.session.rollback()
            return None, f"Lỗi khi tạo lịch đặt: {str(e)}"

    @staticmethod
    def get_all_bookings():
        return Booking.query.all()
    
    @staticmethod
    def get_booking_by_id(booking_id):
        return Booking.query.get(booking_id)

    @staticmethod
    def update_booking_status(booking_id, new_status):
        booking = BookingService.get_booking_by_id(booking_id)
        if not booking:
            return None, "Không tìm thấy lịch đặt."
        
        valid_statuses = ["pending", "confirmed", "canceled", "completed"]
        if new_status not in valid_statuses:
            return None, f"Trạng thái '{new_status}' không hợp lệ."
        
        try:
            booking.status = new_status
            db.session.commit()
            return booking, None
        except Exception as e:
            db.session.rollback()
            return None, f"Lỗi khi cập nhật trạng thái: {str(e)}"
    
    @staticmethod
    def delete_booking(booking_id):
        booking = BookingService.get_booking_by_id(booking_id)
        if not booking:
            return False, "Không tìm thấy lịch đặt."

        try:
            db.session.delete(booking)
            db.session.commit()
            return True, "Xóa lịch đặt thành công."
        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi khi xóa lịch đặt: {str(e)}"
    
    @staticmethod
    def get_bookings_by_user(user_id):
        """Lấy tất cả lịch đặt của một người dùng"""
        # Đảm bảo user_id là integer
        user_id_int = int(user_id)
        
        # Sắp xếp theo start_time để lịch sắp tới hiển thị trước
        return Booking.query.filter_by(user_id=user_id_int).order_by(Booking.start_time.desc()).all()
    @staticmethod
    def _send_booking_notification(booking):
        """Send notification after booking creation"""
        try:
            url = "http://notification-service:8005/internal/notifications/create"
            headers = {
                "X-Internal-Token": os.getenv("INTERNAL_SERVICE_TOKEN"),
                "Content-Type": "application/json"
            }
            data = {
                "user_id": booking.user_id,
                "notification_type": "booking_status",
                "title": "Đặt lịch thành công! 🎉",
                "message": f"Lịch hẹn {booking.service_type} của bạn đã được xác nhận.",
                "channel": "in_app",
                "priority": "high",
                "related_entity_type": "booking",
                "related_entity_id": booking.id
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=5)
            return response.status_code == 201
        except Exception as e:
            # Log error but don't fail booking creation
            print(f"Failed to send notification: {e}")
            return False
    
    @staticmethod
    def create_booking(data):
        # ... existing booking creation code ...
        
        # After successful booking creation
        if booking:
            BookingService._send_booking_notification(booking)
        
        return booking, None

# Hàm gửi thông báo khi tạo booking thành công

    @staticmethod
    def _notify_booking_created(booking):
        """Thông báo khi tạo booking thành công"""
        from notification_helper import NotificationHelper
        
        return NotificationHelper.send_notification(
            user_id=booking.user_id,
            notification_type="booking_status",
            title="✅ Đặt lịch thành công!",
            message=f"Lịch hẹn {booking.service_type} của bạn đã được xác nhận cho ngày {booking.start_time.strftime('%d/%m/%Y %H:%M')}",
            channel="in_app",
            priority="high",
            related_entity_type="booking",
            related_entity_id=booking.id,
            metadata={
                "service_type": booking.service_type,
                "technician_id": booking.technician_id,
                "station_id": booking.station_id
            }
        )
    
    @staticmethod
    def _notify_booking_status_changed(booking, old_status, new_status):
        """Thông báo khi trạng thái booking thay đổi"""
        from notification_helper import NotificationHelper
        
        messages = {
            "confirmed": "✅ Lịch hẹn của bạn đã được xác nhận",
            "completed": "🎉 Dịch vụ đã hoàn tất! Cảm ơn bạn đã sử dụng dịch vụ",
            "canceled": "❌ Lịch hẹn đã bị hủy"
        }
        
        priorities = {
            "confirmed": "high",
            "completed": "medium",
            "canceled": "high"
        }
        
        return NotificationHelper.send_notification(
            user_id=booking.user_id,
            notification_type="booking_status",
            title=f"Cập nhật trạng thái: {new_status}",
            message=messages.get(new_status, f"Trạng thái đã chuyển từ {old_status} sang {new_status}"),
            channel="in_app",
            priority=priorities.get(new_status, "medium"),
            related_entity_type="booking",
            related_entity_id=booking.id
        )
    
    @staticmethod
    def _notify_booking_reminder(booking):
        """Nhắc nhở trước 24h (dùng với scheduled job)"""
        from notification_helper import NotificationHelper
        
        return NotificationHelper.send_notification(
            user_id=booking.user_id,
            notification_type="reminder",
            title="⏰ Nhắc nhở lịch hẹn",
            message=f"Bạn có lịch hẹn {booking.service_type} vào ngày mai lúc {booking.start_time.strftime('%H:%M')}",
            channel="in_app",
            priority="high",
            related_entity_type="booking",
            related_entity_id=booking.id
        )
    
    @staticmethod
    def create_booking(data):
        # ... existing booking creation code ...
        
        # ✅ THÊM: Gửi notification sau khi tạo thành công
        if Booking:
            BookingService._notify_booking_created(Booking)
        
        return Booking, None
    
    @staticmethod
    def update_booking_status(booking_id, new_status):
        booking = BookingService.get_booking_by_id(booking_id)
        if not booking:
            return None, "Không tìm thấy lịch đặt."
        
        old_status = booking.status
        
        valid_statuses = ["pending", "confirmed", "canceled", "completed"]
        if new_status not in valid_statuses:
            return None, f"Trạng thái '{new_status}' không hợp lệ."
        
        try:
            booking.status = new_status
            db.session.commit()
            
            # ✅ THÊM: Gửi notification khi trạng thái thay đổi
            BookingService._notify_booking_status_changed(booking, old_status, new_status)
            
            return booking, None
        except Exception as e:
            db.session.rollback()
            return None, f"Lỗi khi cập nhật trạng thái: {str(e)}"