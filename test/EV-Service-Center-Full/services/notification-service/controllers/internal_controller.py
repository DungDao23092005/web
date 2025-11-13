from flask import Blueprint, request, jsonify, current_app
from services.notification_service import NotificationService

internal_bp = Blueprint("internal_notification", __name__, url_prefix="/internal/notifications")

@internal_bp.before_request
def verify_internal_token():
    token = request.headers.get("X-Internal-Token")
    expected_token = current_app.config.get("INTERNAL_SERVICE_TOKEN")
    
    if not token or token != expected_token:
        return jsonify({"error": "Unauthorized internal request"}), 401

@internal_bp.route("/create", methods=["POST"])
def internal_create_notification():
    """Internal API to create notification"""
    data = request.json
    
    notification, error = NotificationService.create_notification(data)
    if error:
        return jsonify({"error": error}), 400
    
    return jsonify({
        "message": "Notification created successfully",
        "notification": notification.to_dict()
    }), 201