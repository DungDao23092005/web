# File: services/finance-service/controllers/finance_controller.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from functools import wraps

from services.finance_service import FinanceService as service

invoice_bp = Blueprint("invoice", __name__, url_prefix="/api/invoices")

# --- Decorators (Định nghĩa Admin Required để giữ tính độc lập) ---
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

# --- Helpers ---
def serialize_invoice(invoice, include_items=False):
    """Chuyển đổi đối tượng Invoice thành dictionary để trả về API"""
    if not invoice: return None
    
    data = invoice.to_dict()
    # Nếu dùng lazy='dynamic', cần gọi .all()
    if include_items and hasattr(invoice, 'items'):
        data['items'] = [item.to_dict() for item in invoice.items.all()]
    
    return data

# --- Routes ---

# 1. ADMIN: CREATE INVOICE (POST /api/invoices)
@invoice_bp.route("/", methods=["POST"])
@jwt_required()
@admin_required()
def create_invoice():
    data = request.json
    booking_id = data.get("booking_id")
    parts_data = data.get("parts_data", []) 

    if not booking_id:
        return jsonify({"error": "Thiếu booking_id"}), 400
    
    # Logic: Tạo hóa đơn
    invoice, error = service.create_invoice_from_booking(booking_id, parts_data)
    
    if error:
        # 409 Conflict: đã tồn tại. 400 Bad Request: lỗi khác.
        status_code = 409 if "tồn tại" in error else 400
        return jsonify({"error": error}), status_code

    return jsonify({
        "message": "Hóa đơn được tạo thành công!",
        "invoice": serialize_invoice(invoice, include_items=True)
    }), 201

# 2. ADMIN: GET ALL INVOICES (GET /api/invoices)
@invoice_bp.route("/", methods=["GET"])
@jwt_required()
@admin_required()
def get_all_invoices():
    invoices = service.get_all_invoices()
    return jsonify([serialize_invoice(i) for i in invoices]), 200

# 3. USER: GET MY INVOICES (GET /api/invoices/my)
@invoice_bp.route("/my", methods=["GET"])
@jwt_required()
def get_my_invoices():
    user_id = get_jwt_identity()
    invoices = service.get_invoices_by_user(user_id)
    return jsonify([serialize_invoice(i) for i in invoices]), 200

# 4. GET INVOICE BY ID (GET /api/invoices/<id>)
@invoice_bp.route("/<int:invoice_id>", methods=["GET"])
@jwt_required()
def get_invoice_details(invoice_id):
    invoice_data, error = service.get_invoice_with_items(invoice_id)
    
    if error:
        return jsonify({"error": error}), 404
    
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    
    # Phân quyền: Chỉ Admin HOẶC User sở hữu mới được xem
    is_admin = claims.get("role") == "admin"
    is_owner = str(invoice_data.get('user_id')) == str(current_user_id)

    if not is_admin and not is_owner:
        return jsonify(error="Unauthorized access to invoice"), 403

    return jsonify(invoice_data), 200

# 5. ADMIN: UPDATE STATUS (PUT /api/invoices/<id>/status)
@invoice_bp.route("/<int:invoice_id>/status", methods=["PUT"])
@jwt_required()
@admin_required()
def update_invoice_status_route(invoice_id):
    data = request.json
    new_status = data.get("status")
    
    if not new_status:
        return jsonify({"error": "Missing 'status' field."}), 400
    
    invoice, error = service.update_invoice_status(invoice_id, new_status)
    if error:
        # Trả về 400 nếu lỗi về trạng thái, 404 nếu không tìm thấy
        status_code = 404 if "Không tìm thấy Hóa đơn" in error else 400
        return jsonify({"error": error}), status_code
        
    return jsonify({
        "message": f"Cập nhật trạng thái hóa đơn thành '{new_status}' thành công.", 
        "invoice": serialize_invoice(invoice)
    }), 200
# 6. USER: INITIATE INVOICE PAYMENT (POST /api/invoices/<id>/pay) <--- THÊM KHỐI NÀY
@invoice_bp.route("/<int:invoice_id>/pay", methods=["POST"])
@jwt_required()
def initiate_invoice_payment_route(invoice_id):
    data = request.json
    payment_method = data.get("method")
    
    if not payment_method:
        return jsonify({"error": "Thiếu phương thức thanh toán (method)."}), 400

    current_user_id = get_jwt_identity()
    
    # 1. Gọi Finance Service logic (sẽ gọi tiếp Payment Service)
    transaction_data, error = service.initiate_payment(invoice_id, payment_method, int(current_user_id))
    
    if error:
        return jsonify({"error": error}), 400

    # 2. Trả về thông tin giao dịch để Frontend hiển thị QR/Bank details
    return jsonify({
        "message": "Giao dịch đã được tạo. Vui lòng hoàn tất thanh toán.", 
        "transaction": transaction_data
    }), 200

