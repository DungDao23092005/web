# File: services/notification-service/app.py
import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

load_dotenv()

# Khởi tạo Extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager() 

def create_app():
    """Tạo và cấu hình Flask app chính cho Notification Service"""
    app = Flask(__name__)
    CORS(app)

    # ===== CẤU HÌNH (Lấy từ .env) =====
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["INTERNAL_SERVICE_TOKEN"] = os.getenv("INTERNAL_SERVICE_TOKEN")
    
    # ===== KHỞI TẠO EXTENSIONS =====
    db.init_app(app)
    jwt.init_app(app)
    # Sửa: trỏ đúng version_table cho notification
    migrate.init_app(app, db, directory='migrations', version_table='alembic_version_notification')

    # ===== IMPORT MODELS & TẠO TABLES =====
    with app.app_context():
        # Sửa: import đúng model
        from models.notification_model import Notification 
        db.create_all()

    # ===== ĐĂNG KÝ BLUEPRINTS (Controllers) =====
    # Sửa: import đúng controllers
    from controllers.notification_controller import notification_bp
    from controllers.internal_controller import internal_bp
    
    app.register_blueprint(notification_bp) 
    app.register_blueprint(internal_bp)

    # ===== HEALTH CHECK =====
    @app.route("/health", methods=["GET"])
    def health_check():
        # Sửa: trả về đúng tên service
        return jsonify({"status": "Notification Service is running!"}), 200

    return app