# File: services/user-service/app.py
import os
from flask import Flask, jsonify # <-- THÊM jsonify VÀO IMPORT
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from dotenv import load_dotenv
import redis
import click
from datetime import timedelta

# Load environment variables
load_dotenv()

# ✅ KHỞI TẠO EXTENSIONS TRỰC TIẾP Ở ĐÂY
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

# Redis toàn cục
r = None


def create_app():
    """Tạo và cấu hình Flask app chính cho User Service"""
    app = Flask(__name__)
    CORS(app)

    # ===== CẤU HÌNH =====
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "secretkey")
    app.config["INTERNAL_SERVICE_TOKEN"] = os.getenv("INTERNAL_SERVICE_TOKEN")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)
    # ===== KHỞI TẠO EXTENSIONS =====
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db, directory='migrations', version_table='alembic_version_users')

    # ===== KẾT NỐI REDIS =====
    global r
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    try:
        r = redis.from_url(redis_url, decode_responses=True)
        r.ping()
        print("✅ [User Service] Connected to Redis successfully.")
    except redis.exceptions.ConnectionError as e:
        print(f"❌ [User Service] Could not connect to Redis: {e}")

    # ===== IMPORT MODELS (Sau khi db đã init) =====
    with app.app_context():
        from models.user import User
        from models.profile import Profile
        
        # Tạo tables nếu chưa có
        db.create_all()

    # ===== ĐĂNG KÝ BLUEPRINTS =====
    from controllers.controllers_api import api_bp
    from controllers.internal_controller import internal_bp
    
    app.register_blueprint(api_bp)
    app.register_blueprint(internal_bp)

    # ===== CLI COMMAND: Tạo Admin (Đặt ở đây) =====
    @app.cli.command("create-admin")
    @click.argument("username")
    @click.argument("email")
    @click.argument("password")
    def create_admin_command(username, email, password):
        """Lệnh CLI để tạo tài khoản admin mới"""
        with app.app_context():
            from services.services_refactored import UserService

            if UserService.get_user_by_email_or_username(email) or \
               UserService.get_user_by_email_or_username(username):
                print(f"❌ Người dùng '{email}' hoặc '{username}' đã tồn tại.")
                return

            user, error = UserService.create_user(
                email=email,
                username=username,
                password=password,
                role="admin",
            )
            if error:
                print(f"❌ Lỗi khi tạo admin: {error}")
            else:
                print(f"✅ Tài khoản admin '{username}' đã được tạo thành công.")
    
    # ===== HEALTH CHECK (Đặt ở CUỐI CÙNG) =====
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "User Service is running!"}), 200

    return app # <--- ĐẢM BẢO LỆNH RETURN Ở CUỐI CÙNG


# ===== CHẠY APP (CHỈ KHI CHẠY TRỰC TIẾP) =====
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
