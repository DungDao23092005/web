# File: services/booking-service/controllers/booking_controller.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    jwt_required, 
    verify_jwt_in_request, 
    get_jwt,
    get_jwt_identity # ✅ Đã thêm import bị thiếu
)
from functools import wraps

from services.booking_service import BookingService as service

booking_bp = Blueprint("booking", __name__, url_prefix="/api/bookings")

# --- Decorators (Tạm thời định nghĩa ở đây) ---
def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                verify_jwt_in_request()
                claims = get_jwt()
                if claims.get("role") == "admin":
                    return fn(*args, **kwargs)
                else:
                    return jsonify(error="Admins only!"), 403
            except Exception:
                return jsonify(error="Token invalid or missing."), 401
        return decorator
    return wrapper

# --- Routes ---

# 1. GET ALL BOOKINGS (Chỉ Admin)
@booking_bp.route("/items", methods=["GET"])
@jwt_required()
@admin_required() 
def get_bookings():
    bookings = service.get_all_bookings()
    return jsonify([b.to_dict() for b in bookings]), 200

# 2. CREATE BOOKING (User)
@booking_bp.route("/items", methods=["POST"])
@jwt_required()
def create_booking_route():
    data = request.json
    
    # ✅ Đã sửa: get_jwt_identity đã được import ở trên, không cần import lại ở đây
    current_user_id = get_jwt_identity()
    
    data['user_id'] = int(current_user_id) 
    
    booking, error = service.create_booking(data)
    if error:
        status_code = 409 if "trùng" in error else 400 
        return jsonify({"error": error}), status_code

    return jsonify({
        "message": "Đặt lịch thành công!", 
        "booking": booking.to_dict()
    }), 201

# 3. UPDATE STATUS (Admin)
@booking_bp.route("/items/<int:booking_id>/status", methods=["PUT"])
@jwt_required()
@admin_required()
def update_booking_status_route(booking_id):
    data = request.json
    new_status = data.get("status")
    
    if not new_status:
        return jsonify({"error": "Missing 'status' field."}), 400
    
    booking, error = service.update_booking_status(booking_id, new_status)
    if error:
        return jsonify({"error": error}), 404

    return jsonify({
        "message": f"Cập nhật trạng thái thành '{new_status}' thành công.", 
        "booking": booking.to_dict()
    }), 200

# 4. DELETE BOOKING (Admin)
@booking_bp.route("/items/<int:booking_id>", methods=["DELETE"])
@jwt_required()
@admin_required()
def delete_booking_route(booking_id):
    success, message = service.delete_booking(booking_id)
    
    if not success:
        return jsonify({"error": message}), 404
    
    return jsonify({"message": message}), 200

# 5. GET BOOKING BY ID (Admin)
@booking_bp.route("/items/<int:booking_id>", methods=["GET"])
@jwt_required()
@admin_required() 
def get_booking_by_id_route(booking_id):
    booking = service.get_booking_by_id(booking_id)
    if not booking:
        return jsonify({"error": "Không tìm thấy lịch đặt."}), 404
    return jsonify(booking.to_dict()), 200

@booking_bp.route("/my-bookings", methods=["GET"])
@jwt_required()
def get_my_bookings():
    """Lấy danh sách lịch đặt của User hiện tại (lấy ID từ JWT)"""
    try:
        user_id = get_jwt_identity() # ✅ Hàm đã được tìm thấy
        bookings = service.get_bookings_by_user(user_id)
        
        return jsonify([b.to_dict() for b in bookings]), 200
    except Exception as e:
        current_app.logger.error(f"Error getting user bookings: {str(e)}")
        return jsonify(error="Không thể tải lịch hẹn của bạn."), 500