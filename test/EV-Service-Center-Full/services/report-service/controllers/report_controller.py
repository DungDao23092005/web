# File: services/report-service/controllers/report_controller.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from functools import wraps

from services.report_service import ReportService as service

report_bp = Blueprint("report", __name__, url_prefix="/api/reports")

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

# 1. ADMIN: Yêu cầu tạo báo cáo mới (POST /api/reports)
@report_bp.route("/", methods=["POST"])
@jwt_required()
@admin_required()
def create_report_request():
    data = request.json
    report_type = data.get("report_type")
    
    if not report_type:
        return jsonify({"error": "Thiếu report_type"}), 400
        
    admin_id = get_jwt_identity()
    
    # Logic: Tạo yêu cầu báo cáo (ban đầu là 'pending')
    report, error = service.request_new_report(admin_id, report_type)
    
    if error:
        return jsonify({"error": error}), 400

    return jsonify({
        "message": "Đã nhận yêu cầu tạo báo cáo. Báo cáo đang được xử lý.",
        "report": report.to_dict()
    }), 201

# 2. ADMIN: Lấy danh sách các báo cáo đã tạo (GET /api/reports)
@report_bp.route("/", methods=["GET"])
@jwt_required()
@admin_required()
def get_all_reports_route():
    reports = service.get_all_reports()
    return jsonify([r.to_dict() for r in reports]), 200

# 3. ADMIN: Lấy chi tiết một báo cáo (GET /api/reports/<id>)
@report_bp.route("/<int:report_id>", methods=["GET"])
@jwt_required()
@admin_required()
def get_report_details_route(report_id):
    report = service.get_report_by_id(report_id)
    if not report:
        return jsonify({"error": "Không tìm thấy báo cáo."}), 404
    
    return jsonify(report.to_dict()), 200

# 4. ADMIN: (Tùy chọn) Chạy lại một báo cáo (PUT /api/reports/<id>/regenerate)
@report_bp.route("/<int:report_id>/regenerate", methods=["PUT"])
@jwt_required()
@admin_required()
def regenerate_report_route(report_id):
    admin_id = get_jwt_identity()
    report, error = service.regenerate_report(report_id, admin_id)
    if error:
        status_code = 404 if "Không tìm thấy" in error else 400
        return jsonify({"error": error}), status_code
    
    return jsonify({
        "message": "Đã gửi yêu cầu chạy lại báo cáo.",
        "report": report.to_dict()
    }), 200