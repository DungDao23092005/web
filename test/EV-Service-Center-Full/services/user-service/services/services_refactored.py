import os
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import timedelta
from models.user import User
from models.profile import Profile
from app import db, r  # ✅ Import db VÀ r (Redis) từ app
from werkzeug.security import generate_password_hash
class UserService:
    """Service xử lý logic nghiệp vụ liên quan đến User"""
    @staticmethod
    def _generate_otp(length=6):
        """Tạo mã OTP ngẫu nhiên"""
        characters = string.digits
        return "".join(random.choice(characters) for _ in range(length))

    @staticmethod
    def _send_email(to_email, subject, body):
        """Hàm nội bộ để gửi email"""
        sender_email = os.getenv("SENDER_EMAIL")
        app_password = os.getenv("APP_PASSWORD")

        if not sender_email or not app_password:
            print("❌ Lỗi gửi email: Vui lòng cài đặt SENDER_EMAIL và APP_PASSWORD trong file .env")
            return False, "Lỗi máy chủ: Không thể gửi email"

        try:
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html"))

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, to_email, msg.as_string())
            server.quit()
            return True, "Gửi email thành công"
        except Exception as e:
            print(f"❌ Lỗi smtplib: {str(e)}")
            return False, f"Lỗi khi gửi email: {str(e)}"

    @staticmethod
    def send_reset_otp(email):
        """Tạo, lưu và gửi OTP reset mật khẩu"""
        user = UserService.get_user_by_email(email)
        if not user:
            return False, "Không tìm thấy tài khoản với email này"

        otp = UserService._generate_otp()
        
        subject = "[EV Service Center] Mã OTP Đặt Lại Mật Khẩu"
        body = f"""
        <p>Xin chào {user.username},</p>
        <p>Bạn đã yêu cầu đặt lại mật khẩu. Mã OTP của bạn là:</p>
        <h2 style="font-size: 24px; letter-spacing: 2px;"><b>{otp}</b></h2>
        <p>Mã này sẽ hết hạn sau 10 phút.</p>
        """

        email_sent, email_error = UserService._send_email(email, subject, body)
        if not email_sent:
            return False, email_error

        try:
            redis_key = f"otp:{email}"
            r.setex(redis_key, timedelta(minutes=10), otp)
            return True, "Đã gửi mã OTP thành công. Vui lòng kiểm tra email."
        except Exception as e:
            print(f"❌ Lỗi Redis: {str(e)}")
            return False, "Lỗi máy chủ khi lưu OTP"

    @staticmethod
    def verify_otp_and_reset_password(email, otp, new_password):
        """Xác thực OTP và đặt lại mật khẩu"""
        redis_key = f"otp:{email}"
        try:
            stored_otp = r.get(redis_key)
        except Exception as e:
            print(f"❌ Lỗi Redis khi lấy OTP: {str(e)}")
            return False, "Lỗi máy chủ. Vui lòng thử lại sau."

        if not stored_otp:
            return False, "Mã OTP đã hết hạn hoặc không tồn tại"
        
        if stored_otp != otp:
            return False, "Mã OTP không chính xác"

        user = UserService.get_user_by_email(email)
        if not user:
            return False, "Lỗi không tìm thấy người dùng"

        try:
            user.set_password(new_password)
            db.session.commit()
            r.delete(redis_key)
            return True, "Đặt lại mật khẩu thành công"
        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi khi cập nhật mật khẩu: {str(e)}"

    @staticmethod
    def create_user(email, username, password, role="user"):
        """Tạo user mới"""
        # Kiểm tra email đã tồn tại
        if User.query.filter_by(email=email).first():
            return None, "Email đã được sử dụng"
        
        # Kiểm tra username đã tồn tại
        if User.query.filter_by(username=username).first():
            return None, "Tên đăng nhập đã được sử dụng"
        
        # Tạo user mới
        user = User(
            email=email,
            username=username,
            role=role,
            status="active"
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Tự động tạo profile trống cho user
            profile = Profile(user_id=user.user_id)
            db.session.add(profile)
            db.session.commit()
            
            return user, None
        except Exception as e:
            db.session.rollback()
            return None, f"Lỗi khi tạo tài khoản: {str(e)}"
    
    @staticmethod
    def get_user_by_id(user_id):
        """Lấy user theo ID"""
        return User.query.get(user_id)
    
    @staticmethod
    def get_user_by_email(email):
        """Lấy user theo email"""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def get_user_by_username(username):
        """Lấy user theo username"""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def get_user_by_email_or_username(email_or_username):
        """Lấy user theo email HOẶC username"""
        user = User.query.filter(
            (User.email == email_or_username) | 
            (User.username == email_or_username)
        ).first()
        return user
    
    @staticmethod
    def get_all_users():
        """Lấy tất cả users (cho admin)"""
        return User.query.all()
    
    @staticmethod
    def toggle_user_lock(user_id):
        """Khóa/mở khóa user"""
        user = User.query.get(user_id)
        if not user:
            return None, "Không tìm thấy người dùng"
        
        # Toggle status
        user.status = "locked" if user.status == "active" else "active"
        
        try:
            db.session.commit()
            return user, None
        except Exception as e:
            db.session.rollback()
            return None, f"Lỗi khi cập nhật trạng thái: {str(e)}"
    
    @staticmethod
    def delete_user(user_id):
        """Xóa user"""
        user = User.query.get(user_id)
        if not user:
            return False, "Không tìm thấy người dùng"
        
        try:
            # Xóa profile trước (nếu có foreign key constraint)
            Profile.query.filter_by(user_id=user_id).delete()
            
            # Xóa user
            db.session.delete(user)
            db.session.commit()
            return True, "Xóa người dùng thành công"
        except Exception as e:
            db.session.rollback()
            return False, f"Lỗi khi xóa người dùng: {str(e)}"


class ProfileService:
    """Service xử lý logic nghiệp vụ liên quan đến Profile"""
    
    @staticmethod
    def get_profile_by_user_id(user_id):
        """Lấy profile theo user_id"""
        return Profile.query.filter_by(user_id=user_id).first()
    
    @staticmethod
    def update_profile(user_id, profile_data):
        """Cập nhật profile"""
        profile = Profile.query.filter_by(user_id=user_id).first()
        
        # Nếu chưa có profile thì tạo mới
        if not profile:
            profile = Profile(user_id=user_id)
            db.session.add(profile)
        
        # Cập nhật các trường
        if "phone_number" in profile_data:
            profile.phone_number = profile_data["phone_number"]
        if "address" in profile_data:
            profile.address = profile_data["address"]
        if "vehicle_model" in profile_data:
            profile.vehicle_model = profile_data["vehicle_model"]
        if "vin_number" in profile_data:
            profile.vin_number = profile_data["vin_number"]
        if "full_name" in profile_data:
            profile.full_name = profile_data["full_name"]
        
        try:
            db.session.commit()
            return profile, None
        except Exception as e:
            db.session.rollback()
            return None, f"Lỗi khi cập nhật hồ sơ: {str(e)}"
    
    @staticmethod
    def get_profile_details(user_id):
        """Lấy thông tin chi tiết profile"""
        profile = Profile.query.filter_by(user_id=user_id).first()
        if not profile:
            return None, "Không tìm thấy hồ sơ"
        
        return {
            "full_name": profile.full_name,
            "phone_number": profile.phone_number,
            "address": profile.address,
            "vehicle_model": profile.vehicle_model,
            "vin_number": profile.vin_number
        }, None
    @staticmethod
    def get_all_admins():
        """Lấy tất cả admin users"""
        return User.query.filter_by(role="admin").all()