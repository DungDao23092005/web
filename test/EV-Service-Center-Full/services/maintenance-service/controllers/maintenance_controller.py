# File: services/maintenance-service/controllers/maintenance_controller.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from functools import wraps

from services.maintenance_service import MaintenanceService as service

maintenance_bp = Blueprint("maintenance", __name__, url_prefix="/api/maintenance")

# --- Decorators (Sao chép Admin Required) ---
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

# 1. ADMIN: CREATE TASK (POST /api/maintenance/tasks)
@maintenance_bp.route("/tasks", methods=["POST"])
@jwt_required()
@admin_required()
def create_maintenance_task():
    data = request.json
    booking_id = data.get("booking_id")
    technician_id = data.get("technician_id")

    if not booking_id or not technician_id:
        return jsonify({"error": "Thiếu booking_id hoặc technician_id"}), 400
    
    try:
        booking_id = int(booking_id)
        technician_id = int(technician_id)
    except ValueError:
        return jsonify({"error": "booking_id và technician_id phải là số nguyên"}), 400
    
    task, error = service.create_task_from_booking(booking_id, technician_id)
    
    if error:
        status_code = 409 if "tồn tại" in error else 400
        return jsonify({"error": error}), status_code

    return jsonify({
        "message": "Công việc bảo trì được tạo thành công!",
        "task": task.to_dict()
    }), 201

# 2. ADMIN: GET ALL TASKS (GET /api/maintenance/tasks)
@maintenance_bp.route("/tasks", methods=["GET"])
@jwt_required()
@admin_required()
def get_all_tasks_route():
    tasks = service.get_all_tasks()
    return jsonify([t.to_dict() for t in tasks]), 200

# 3. USER: GET MY TASKS (GET /api/maintenance/my-tasks)
@maintenance_bp.route("/my-tasks", methods=["GET"])
@jwt_required()
def get_my_tasks_route():
    user_id = get_jwt_identity()
    tasks = service.get_tasks_by_user(user_id)
    return jsonify([t.to_dict() for t in tasks]), 200

# 4. GET TASK BY ID (Admin hoặc User sở hữu)
@maintenance_bp.route("/tasks/<int:task_id>", methods=["GET"])
@jwt_required()
def get_task_details_route(task_id):
    task = service.get_task_by_id(task_id)
    
    if not task:
        return jsonify({"error": "Không tìm thấy Công việc."}), 404
    
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    is_admin = claims.get("role") == "admin"
    is_owner = str(task.user_id) == str(current_user_id)

    if not is_admin and not is_owner:
        return jsonify(error="Unauthorized access to task"), 403

    return jsonify(task.to_dict()), 200

# 5. ADMIN: UPDATE STATUS (PUT /api/maintenance/tasks/<id>/status)
@maintenance_bp.route("/tasks/<int:task_id>/status", methods=["PUT"])
@jwt_required()
@admin_required()
def update_task_status_route(task_id):
    data = request.json
    new_status = data.get("status")
    
    if not new_status:
        return jsonify({"error": "Missing 'status' field."}), 400
    
    task, error = service.update_task_status(task_id, new_status)
    if error:
        status_code = 404 if "Không tìm thấy" in error else 400
        return jsonify({"error": error}), status_code
        
    return jsonify({
        "message": f"Cập nhật trạng thái công việc thành '{new_status}' thành công.", 
        "task": task.to_dict()
    }), 200