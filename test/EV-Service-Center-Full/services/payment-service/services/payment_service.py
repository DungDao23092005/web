import requests
import json
import os # Import os để tạo random bytes
from flask import current_app, jsonify
from app import db
from models.payment_model import PaymentTransaction, PAYMENT_STATUSES
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError # Import để bắt lỗi DB

class PaymentService:
    """Service xử lý logic nghiệp vụ về Thanh toán"""
    
    # --- Helper Internal API Caller (Giữ nguyên) ---
    @staticmethod
    def _call_internal_api(service_url, endpoint, method="GET", json_data=None):
        """Hàm nội bộ gọi Internal API của các service khác"""
        internal_token = current_app.config.get("INTERNAL_SERVICE_TOKEN")
        url = f"{service_url}{endpoint}"
        headers = {"X-Internal-Token": internal_token}
        
        if not service_url or not internal_token:
             return None, "Lỗi cấu hình Service URL hoặc Internal Token."

        try:
            response = requests.request(method, url, headers=headers, json=json_data) 

            if response.status_code == 200 or response.status_code == 201:
                return response.json(), None
            else:
                error_msg = response.json().get('error', f"Lỗi Service (HTTP {response.status_code})")
                return None, error_msg
        except requests.exceptions.RequestException as e:
            return None, f"Lỗi kết nối Service: {str(e)}"

    @staticmethod
    def _get_invoice_details(invoice_id):
        """Lấy chi tiết Invoice từ Finance Service"""
        finance_url = current_app.config.get("FINANCE_SERVICE_URL")
        return PaymentService._call_internal_api(finance_url, f"/internal/invoices/{invoice_id}")
    
    @staticmethod
    def _update_invoice_status(invoice_id, new_status):
        """Cập nhật trạng thái Invoice"""
        finance_url = current_app.config.get("FINANCE_SERVICE_URL")
        return PaymentService._call_internal_api(
            finance_url, 
            f"/internal/invoices/{invoice_id}/status", 
            "PUT", 
            {"status": new_status}
        )
    
    @staticmethod
    def _generate_mock_pg_data(invoice_id, amount, method):
        """Giả lập tạo dữ liệu cho Cổng Thanh toán (QR/Bank info)"""
        # Tạo ID duy nhất bằng random hex
        pg_id = f"PG_{method.upper()}_{invoice_id}_{int(amount)}_{os.urandom(4).hex()}"
        note = f"EV_TT_{invoice_id}"
        
        # ✅ FIX: ĐỌC TRỰC TIẾP TỪ OS ENV ĐỂ KHÔNG PHỤ THUỘC current_app.config
        # Nếu biến môi trường đã được tải bằng load_dotenv (trong app.py), os.getenv sẽ hoạt động
        custom_momo_url = os.getenv("MOMO_QR_CODE_URL")
        
        # Logic tạo URL
        # Ưu tiên URL cá nhân chỉ khi phương thức là momo_qr
        if method == "momo_qr" and custom_momo_url: 
            qr_url = custom_momo_url # SỬ DỤNG URL CÁ NHÂN TỪ .ENV
        else:
            # Fallback: Code tạo QR động mặc định
            qr_content = f"MOMO|{note}|{amount}|{pg_id}"
            qr_url = f"https://chart.googleapis.com/chart?cht=qr&chs=150x150&chl={qr_content}"
            
        if method == "momo_qr":
            qr_data = {
                "qr_code_url": qr_url, 
                "payment_text": note,
                "amount": amount,
                "note": f"Thanh toan HD {invoice_id} cho EV Service Center",
                "test_code": f"SUCCESS_PG_{pg_id}" 
            }
            return pg_id, json.dumps(qr_data)
        
        elif method == "bank_transfer":
            bank_data = {
                "bank_name": "Techcombank",
                "account_name": "Trần Bảo Long",
                "account_number": "19072525585011",
                "amount": amount,
                "note": note,
                "test_code": f"SUCCESS_PG_{pg_id}"
            }
            return pg_id, json.dumps(bank_data)

        return None, None

    # --- Core Business Logic (Giữ nguyên logic đã sửa) ---
    @staticmethod
    def create_payment_request(invoice_id, method, user_id, amount): 
        """Bắt đầu tạo giao dịch thanh toán"""
        
        # Bỏ API call, chỉ kiểm tra trạng thái bên Finance
        # ...

        # 3. Tạo dữ liệu PG Mock
        pg_id, payment_data = PaymentService._generate_mock_pg_data(invoice_id, amount, method)
        
        if not pg_id:
             return None, "Phương thức thanh toán không hợp lệ."

        # 4. Tạo Payment Transaction trong DB (FIX CRASH)
        new_transaction = PaymentTransaction(
            invoice_id=invoice_id,
            user_id=user_id,
            amount=amount,
            method=method,
            pg_transaction_id=pg_id,
            payment_data_json=payment_data
        )

        try:
            db.session.add(new_transaction)
            db.session.commit()
            return new_transaction.to_dict(), None # Trả về dictionary
        except IntegrityError:
            # Lỗi khi PG ID bị trùng (rất hiếm do có random hex)
            db.session.rollback()
            return None, "Lỗi: Đã có giao dịch đang chờ hoặc giao dịch trùng lặp."
        except Exception as e:
            # Bắt mọi lỗi khác và rollback, ngăn chặn worker crash
            current_app.logger.error(f"CRITICAL ERROR in PaymentService.create_payment_request: {str(e)}")
            db.session.rollback()
            return None, "Lỗi máy chủ nghiêm trọng khi tạo giao dịch."
            
    # --- History Functions (Giữ nguyên) ---
    @staticmethod
    def get_transaction_by_pg_id(pg_transaction_id):
        return PaymentTransaction.query.filter_by(pg_transaction_id=pg_transaction_id).first()

    @staticmethod
    def handle_pg_webhook(pg_transaction_id, final_status):
        """Xử lý Webhook giả lập từ Cổng Thanh toán"""
        
        transaction = PaymentService.get_transaction_by_pg_id(pg_transaction_id)
        if not transaction:
            return None, "Không tìm thấy giao dịch với PG ID này."
        
        if transaction.status == 'success':
            return transaction, "Giao dịch đã được xử lý thành công trước đó."
        
        from models.payment_model import PAYMENT_STATUSES
        valid_statuses = [str(s.value) for s in PAYMENT_STATUSES.type.enums]
        if final_status not in valid_statuses:
            return None, "Trạng thái webhook không hợp lệ."
            
        try:
            # 1. Cập nhật trạng thái giao dịch
            transaction.status = final_status
            db.session.commit()

            # 2. Nếu thành công, cập nhật trạng thái Invoice
            if final_status == 'success':
                _, error = PaymentService._update_invoice_status(transaction.invoice_id, 'paid')
                if error:
                    current_app.logger.error(f"Failed to update Invoice {transaction.invoice_id} status to 'paid': {error}")

            return transaction, None
        except Exception as e:
            db.session.rollback()
            return None, f"Lỗi khi xử lý webhook: {str(e)}"

    @staticmethod
    def get_history_by_user(user_id):
        """Lấy lịch sử giao dịch của User"""
        return PaymentTransaction.query.filter_by(user_id=int(user_id)).order_by(desc(PaymentTransaction.created_at)).all()
    
    @staticmethod
    def get_all_history():
        """Lấy tất cả lịch sử giao dịch (Admin)"""
        return PaymentTransaction.query.order_by(desc(PaymentTransaction.created_at)).all()
    @staticmethod
    def _notify_payment_success(payment):
        """Thông báo thanh toán thành công"""
        from notification_helper import NotificationHelper
        
        return NotificationHelper.send_notification(
            user_id=payment.user_id,
            notification_type="payment",
            title="✅ Thanh toán thành công",
            message=f"Thanh toán {payment.amount:,.0f} VNĐ cho hóa đơn #{payment.invoice_id} đã được xử lý thành công.",
            channel="in_app",
            priority="high",
            related_entity_type="payment",
            related_entity_id=payment.id,
            metadata={
                "amount": payment.amount,
                "invoice_id": payment.invoice_id,
                "payment_method": payment.payment_method
            }
        )
    
    @staticmethod
    def _notify_payment_failed(payment):
        """Thông báo thanh toán thất bại"""
        from notification_helper import NotificationHelper
        
        return NotificationHelper.send_notification(
            user_id=payment.user_id,
            notification_type="payment",
            title="❌ Thanh toán thất bại",
            message=f"Thanh toán {payment.amount:,.0f} VNĐ không thành công. Vui lòng thử lại hoặc liên hệ hỗ trợ.",
            channel="in_app",
            priority="high",
            related_entity_type="payment",
            related_entity_id=payment.id
        )
    
    @staticmethod
    def process_payment(data):
        # ... existing payment processing code ...
        
        # ✅ THÊM: Gửi notification dựa trên kết quả
        if payment.status == "success": # type: ignore
            PaymentService._notify_payment_success(payment) # type: ignore
        elif payment.status == "failed": # type: ignore
            PaymentService._notify_payment_failed(payment) # type: ignore
        
        return payment, None # type: ignore
