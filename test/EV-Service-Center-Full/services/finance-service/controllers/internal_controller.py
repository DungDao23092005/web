# File: services/finance-service/controllers/internal_controller.py
from flask import Blueprint, request, jsonify, current_app
from services.finance_service import FinanceService
from controllers.finance_controller import serialize_invoice # Tái sử dụng helper

internal_bp = Blueprint("internal_invoice", __name__, url_prefix="/internal/invoices")

# Middleware để xác thực token nội bộ (Copy từ các Service khác)
@internal_bp.before_request
def verify_internal_token():
    token = request.headers.get("X-Internal-Token")
    expected_token = current_app.config.get("INTERNAL_SERVICE_TOKEN")
    
    if not token or token != expected_token:
        # Trả về 403 nếu token không hợp lệ hoặc thiếu (403 vì chỉ internal service gọi)
        return jsonify({"error": "Unauthorized internal request"}), 403


# 1. Lấy chi tiết Invoice (dùng cho Payment Service)
@internal_bp.route("/<int:invoice_id>", methods=["GET"])
def internal_get_invoice(invoice_id):
    # Lấy invoice chỉ cần các field cơ bản
    invoice_data, error = FinanceService.get_invoice_with_items(invoice_id)
    if error:
        return jsonify({"error": error}), 404
    
    # Chỉ trả về dữ liệu cần thiết cho Payment Service
    return jsonify({
        "id": invoice_data.get('id'),
        "user_id": invoice_data.get('user_id'),
        "total_amount": invoice_data.get('total_amount'),
        "status": invoice_data.get('status')
    })

# 2. Cập nhật trạng thái Invoice (dùng cho Payment Service)
@internal_bp.route("/<int:invoice_id>/status", methods=["PUT"])
def internal_update_invoice_status(invoice_id):
    data = request.json
    new_status = data.get("status")

    if not new_status:
        return jsonify({"error": "Missing 'status' field."}), 400
    
    # Sử dụng logic nghiệp vụ của FinanceService để cập nhật
    invoice, error = FinanceService.update_invoice_status(invoice_id, new_status)
    if error:
        status_code = 404 if "Không tìm thấy Hóa đơn" in error else 400
        return jsonify({"error": error}), status_code
        
    return jsonify({
        "message": f"Cập nhật trạng thái hóa đơn thành '{new_status}' thành công (Internal).", 
        "invoice": serialize_invoice(invoice)
    }), 200