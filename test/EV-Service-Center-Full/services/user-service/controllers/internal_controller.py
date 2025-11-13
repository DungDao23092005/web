from flask import Blueprint, request, jsonify, current_app
from services.services_refactored import UserService

internal_bp = Blueprint("internal", __name__, url_prefix="/internal")

# Middleware để xác thực token nội bộ
@internal_bp.before_request
def verify_internal_token():
    token = request.headers.get("X-Internal-Token")
    expected_token = current_app.config.get("INTERNAL_SERVICE_TOKEN")
    if not token or token != expected_token:
        return jsonify({"error": "Unauthorized internal request"}), 403


# Lấy thông tin người dùng qua email hoặc id (cho các service khác gọi)
@internal_bp.route("/user/<int:user_id>", methods=["GET"])
def internal_get_user(user_id):
    user = UserService.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "Không tìm thấy người dùng"}), 404

    return jsonify({
        "id": user.user_id,
        "username": user.username,
        "email": user.email,
        "role": user.role
    })
