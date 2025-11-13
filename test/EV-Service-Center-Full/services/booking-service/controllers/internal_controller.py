# File: services/booking-service/controllers/internal_controller.py
from flask import Blueprint, request, jsonify, current_app
from services.booking_service import BookingService

internal_bp = Blueprint("internal_booking", __name__, url_prefix="/internal/bookings")

# Middleware để xác thực token nội bộ
@internal_bp.before_request
def verify_internal_token():
    token = request.headers.get("X-Internal-Token")
    # Lấy token mong đợi từ cấu hình app
    expected_token = current_app.config.get("INTERNAL_SERVICE_TOKEN")
    
    if not token or token != expected_token:
        # Trả về 401 nếu token không hợp lệ hoặc thiếu
        return jsonify({"error": "Unauthorized internal request"}), 401


# Lấy thông tin Booking qua ID (cho Finance Service gọi)
@internal_bp.route("/items/<int:booking_id>", methods=["GET"])
def internal_get_booking(booking_id):
    booking = BookingService.get_booking_by_id(booking_id)
    if not booking:
        return jsonify({"error": "Không tìm thấy lịch đặt"}), 404

    # Trả về toàn bộ data của booking
    return jsonify(booking.to_dict())