from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from functools import wraps

from services.notification_service import NotificationService as service

notification_bp = Blueprint("notification", __name__, url_prefix="/api/notifications")

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

@notification_bp.route("/my-notifications", methods=["GET"])
@jwt_required()
def get_my_notifications():
    """Get all notifications for current user"""
    user_id = get_jwt_identity()
    unread_only = request.args.get("unread_only", "false").lower() == "true"
    
    notifications = service.get_user_notifications(user_id, unread_only)
    return jsonify([n.to_dict() for n in notifications]), 200

@notification_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_stats():
    """Get notification statistics"""
    user_id = get_jwt_identity()
    stats = service.get_notification_stats(user_id)
    return jsonify(stats), 200

@notification_bp.route("/<int:notification_id>/read", methods=["PUT"])
@jwt_required()
def mark_as_read(notification_id):
    """Mark a notification as read"""
    user_id = get_jwt_identity()
    notification, error = service.mark_as_read(notification_id, user_id)
    
    if error:
        return jsonify({"error": error}), 404
    
    return jsonify({
        "message": "Notification marked as read",
        "notification": notification.to_dict()
    }), 200

@notification_bp.route("/read-all", methods=["PUT"])
@jwt_required()
def mark_all_as_read():
    """Mark all notifications as read"""
    user_id = get_jwt_identity()
    success, message = service.mark_all_as_read(user_id)
    
    if not success:
        return jsonify({"error": message}), 400
    
    return jsonify({"message": message}), 200

@notification_bp.route("/<int:notification_id>", methods=["DELETE"])
@jwt_required()
def delete_notification(notification_id):
    """Delete a notification"""
    user_id = get_jwt_identity()
    success, message = service.delete_notification(notification_id, user_id)
    
    if not success:
        return jsonify({"error": message}), 404
    
    return jsonify({"message": message}), 200

@notification_bp.route("/admin/all", methods=["GET"])
@jwt_required()
@admin_required()
def get_all_notifications_admin():
    """Admin: Get all notifications"""
    notifications = service.get_all_notifications()
    return jsonify([n.to_dict() for n in notifications]), 200