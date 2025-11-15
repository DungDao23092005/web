# File: services/report-service/services/report_service.py
import requests
from datetime import datetime
from flask import current_app
from app import db
from models.report_model import Report 

class ReportService:
    """Service xử lý logic nghiệp vụ về Báo cáo"""
    
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

    # --- Hàm lấy dữ liệu từ các service khác ---
    
    @staticmethod
    def _get_all_paid_invoices():
        """Lấy tất cả hóa đơn đã thanh toán từ Finance Service"""
        finance_url = current_app.config.get("FINANCE_SERVICE_URL")
        # Giả định Finance Service có internal endpoint /internal/invoices/all
        data, error = ReportService._call_internal_api(finance_url, "/api/invoices/", "GET")
        if error:
            return None, error
        # Lọc các hóa đơn đã 'paid'
        paid_invoices = [inv for inv in data if inv.get('status') == 'paid']
        return paid_invoices, None

    @staticmethod
    def _get_all_users():
        """Lấy tất cả user từ User Service"""
        user_url = current_app.config.get("USER_SERVICE_URL")
        return ReportService._call_internal_api(user_url, "/api/admin/users", "GET") # Sử dụng endpoint admin

    # --- Logic nghiệp vụ chính ---
    
    @staticmethod
    def get_report_by_id(report_id):
        return Report.query.get(report_id)

    @staticmethod
    def get_all_reports():
        return Report.query.order_by(Report.created_at.desc()).all()

    @staticmethod
    def request_new_report(admin_id, report_type):
        """Tạo một yêu cầu báo cáo mới (trạng thái 'pending')"""
        
        # Kiểm tra report_type có hợp lệ không
        valid_types = [str(s.value) for s in Report.report_type.type.enums]
        if report_type not in valid_types:
            return None, f"Loại báo cáo '{report_type}' không hợp lệ."

        try:
            new_report = Report(
                requested_by_id=admin_id,
                report_type=report_type,
                status='pending' 
            )
            db.session.add(new_report)
            db.session.commit()
            
            # TODO: Triển khai chạy nền (ví dụ: Celery, RQ)
            # Tạm thời, chúng ta gọi trực tiếp hàm generate
            ReportService.generate_report(new_report.id)
            
            return new_report, None
        except Exception as e:
            db.session.rollback()
            return None, f"Lỗi khi tạo yêu cầu báo cáo: {str(e)}"

    @staticmethod
    def regenerate_report(report_id, admin_id):
        """Tạo lại một báo cáo đã có"""
        report = Report.query.get(report_id)
        if not report:
            return None, "Không tìm thấy báo cáo."
            
        try:
            # Reset trạng thái và dữ liệu
            report.status = 'pending'
            report.report_data = None
            report.error_message = None
            report.requested_by_id = admin_id
            report.created_at = datetime.now()
            db.session.commit()
            
            # Chạy lại
            ReportService.generate_report(report.id)
            return report, None
        except Exception as e:
            db.session.rollback()
            return None, f"Lỗi khi yêu cầu chạy lại: {str(e)}"

    @staticmethod
    def generate_report(report_id):
        """Hàm chính xử lý việc tạo báo cáo (Nên chạy nền)"""
        report = Report.query.get(report_id)
        if not report:
            return

        try:
            # Cập nhật trạng thái
            report.status = 'processing'
            db.session.commit()

            report_data = {}
            if report.report_type == 'sales_summary':
                report_data = ReportService._generate_sales_summary()
            elif report.report_type == 'user_activity':
                report_data = ReportService._generate_user_activity()
            # Thêm các loại báo cáo khác ở đây...
            else:
                raise Exception(f"Loại báo cáo '{report.report_type}' chưa được hỗ trợ.")

            # Thành công
            report.report_data = report_data
            report.status = 'completed'
            report.generated_at = datetime.now()

        except Exception as e:
            report.status = 'failed'
            report.error_message = str(e)
        
        finally:
            db.session.commit()

    @staticmethod
    def _generate_sales_summary():
        """Logic tạo Báo cáo Doanh thu"""
        invoices, error = ReportService._get_all_paid_invoices()
        if error:
            raise Exception(f"Lỗi khi lấy dữ liệu Finance: {error}")
            
        total_sales = sum(inv.get('total_amount', 0) for inv in invoices)
        count = len(invoices)
        
        return {
            "total_sales_vnd": total_sales,
            "total_paid_invoices": count,
            "average_invoice_value": total_sales / count if count > 0 else 0
        }

    @staticmethod
    def _generate_user_activity():
        """Logic tạo Báo cáo Người dùng"""
        users, error = ReportService._get_all_users()
        if error:
            raise Exception(f"Lỗi khi lấy dữ liệu User: {error}")
            
        total_users = len(users)
        admin_count = sum(1 for u in users if u.get('role') == 'admin')
        active_count = sum(1 for u in users if u.get('status') == 'active')
        
        return {
            "total_users": total_users,
            "admin_users": admin_count,
            "regular_users": total_users - admin_count,
            "active_users": active_count,
            "locked_users": total_users - active_count
        }