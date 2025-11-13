# File: api_routes.py
from functools import wraps
from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
    verify_jwt_in_request
)

from app import jwt
from services.services_refactored import ProfileService as ProfileLogic
from services.services_refactored import UserService as UserLogic

api_bp = Blueprint('api', __name__, url_prefix='/api')

# --- Serializers ---
def serialize_user(user):
    if not user:
        return None
    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "status": user.status
    }

def serialize_profile(profile):
    if not profile:
        return None
    return {
        "user_id": profile.user_id,
        "full_name": profile.full_name,
        "phone_number": profile.phone_number,
        "address": profile.address,
        "bio": profile.bio,
        "avatar_url": profile.avatar_url,
        "vehicle_model": getattr(profile, "vehicle_model", None),
        "vin_number": getattr(profile, "vin_number", None)
    }

# --- Admin Decorator ---
def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") == "admin":
                return fn(*args, **kwargs)
            else:
                return jsonify(error="Admins only!"), 403
        return decorator
    return wrapper

# --- JWT Callbacks ---
@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return UserLogic.get_user_by_id(identity)

@jwt.additional_claims_loader
def add_claims_to_access_token(identity):
    user = UserLogic.get_user_by_id(identity)
    if user:
        return {"role": user.role}
    return {}

# --- Auth Endpoints ---
@api_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data or not all(k in data for k in ["email", "username", "password"]):
        return jsonify({"error": "Missing required fields: email, username, password"}), 400
    
    user, error = UserLogic.create_user(data["email"], data["username"], data["password"])
    if error:
        return jsonify({"error": error}), 409
    
    return jsonify({
        "message": "Registration successful!",
        "user": serialize_user(user)
    }), 201

@api_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("email_username") or not data.get("password"):
        return jsonify({"error": "Missing email/username or password"}), 400

    user = UserLogic.get_user_by_email_or_username(data["email_username"])
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401
    if user.status != "active":
        return jsonify({"error": "Account has been locked"}), 403

    access_token = create_access_token(identity=str(user.user_id))
    return jsonify(access_token=access_token)

@api_bp.route("/send-otp", methods=["POST"])
def send_otp():
    email = request.json.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400
    success, message = UserLogic.send_reset_otp(email)
    if not success:
        return jsonify(error=message), 404
    return jsonify(message=message), 200




@api_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    if not data or not all(k in data for k in ["email", "otp", "new_password"]):
        return jsonify({"error": "Missing required fields"}), 400
    success, message = UserLogic.verify_otp_and_reset_password(
        data["email"], data["otp"], data["new_password"]
    )
    if not success:
        return jsonify(error=message), 400
    return jsonify(message=message), 200

# --- Profile Endpoints ---
@api_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_my_profile():
    current_user_id = get_jwt_identity()
    profile = ProfileLogic.get_profile_by_user_id(current_user_id)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify(serialize_profile(profile)), 200

@api_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_my_profile():
    current_user_id = get_jwt_identity()
    profile, error = ProfileLogic.update_profile(current_user_id, request.json)
    if error:
        return jsonify({"error": error}), 404
    return jsonify({"message": "Profile updated", "profile": serialize_profile(profile)}), 200

# --- Profile Details Endpoint for frontend ---
@api_bp.route("/profile-details", methods=["POST"])
@jwt_required()
def get_profile_details():
    data = request.get_json()
    if not data or not data.get("subject"):
        return jsonify({"error": "Subject (userId) is required"}), 422

    user_id = data["subject"]
    profile = ProfileLogic.get_profile_by_user_id(user_id)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify(serialize_profile(profile)), 200

# --- Account Endpoints ---
@api_bp.route("/account", methods=["PUT"])
@jwt_required()
def update_my_account():
    current_user_id = get_jwt_identity()
    user, error = UserLogic.update_user_by_member(current_user_id, request.json)
    if error:
        return jsonify({"error": error}), 400
    return jsonify({"message": "Account updated", "user": serialize_user(user)}), 200

@api_bp.route("/account", methods=["DELETE"])
@jwt_required()
def delete_my_account():
    current_user_id = get_jwt_identity()
    success, message = UserLogic.delete_user(current_user_id)
    if not success:
        return jsonify({"error": message}), 404
    return jsonify({"message": message}), 200

# --- Admin endpoints (commented for now) ---
@api_bp.route("/admin/users", methods=["GET"])
@admin_required()
def get_all_users():
    users = UserLogic.get_all_users()
    return jsonify([serialize_user(u) for u in users]), 200

@api_bp.route("/admin/users/<string:user_id>", methods=["DELETE"])
@admin_required()
def delete_user_account(user_id):
    """
    Route để xóa một tài khoản người dùng (chỉ admin)
    """
    success, message = UserLogic.delete_user(user_id)
    
    if not success:
        # Nếu service báo lỗi (ví dụ: không tìm thấy user)
        return jsonify(error=message), 404
    
    # Xóa thành công
    return jsonify(message=message), 200

@api_bp.route("/admin/users/<string:user_id>/toggle-lock", methods=["PUT"])
@admin_required()
def toggle_user_lock_account(user_id):
    """
    Route để Khóa hoặc Mở khóa tài khoản (chỉ admin)
    """
    user, error = UserLogic.toggle_user_lock(user_id)
    if error:
        return jsonify(error=error), 404
    return jsonify(serialize_user(user)), 200

@api_bp.route("/admin/users", methods=["POST"])
@admin_required()
def create_user_by_admin():
    """
    Route để admin tạo một tài khoản người dùng mới
    """
    data = request.get_json()
    if not data or not data.get('email') or not data.get('username') or not data.get('password'):
        return jsonify(error="Thiếu email, username, hoặc password"), 400
    
    # Admin có thể tùy chọn vai trò, nếu không thì mặc định là 'user'
    role = data.get('role', 'user')
    
    user, error = UserLogic.create_user(
        data['email'],
        data['username'],
        data['password'],
        role=role
    )
    
    if error:
        # Lỗi 409 (Conflict) nếu email/username đã tồn tại
        return jsonify(error=error), 409
    
    # 201 (Created) khi tạo thành công
    return jsonify(serialize_user(user)), 201