# File: services/inventory-service/app.py

import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables từ .env trong thư mục service
load_dotenv()

# Khởi tạo Extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    """Tạo và cấu hình Flask app chính cho Inventory Service"""
    app = Flask(__name__)
    CORS(app)

    # ===== CẤU HÌNH =====
    # Lấy DATABASE_URL từ file .env của service
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # Bạn có thể thêm JWT_SECRET_KEY nếu cần bảo vệ các route nội bộ

    # ===== KHỞI TẠO EXTENSIONS =====
    db.init_app(app)
    # Cấu hình migration riêng cho Inventory Service
    migrate.init_app(app, db, directory='migrations', version_table='alembic_version_inventory')

    # ===== IMPORT MODELS & TẠO TABLES =====
    with app.app_context():
        # Đảm bảo bạn có file models/inventory_model.py
        from models.inventory_model import Inventory 
        
        # Tạo tables (nếu chưa có)
        db.create_all()

    # ===== ĐĂNG KÝ BLUEPRINTS (Controllers) =====
    # Đảm bảo bạn đã viết file controllers/inventory_controller.py
    from controllers.inventory_controller import inventory_bp 
    
    # Đăng ký blueprint (route sẽ là /api/inventory/...)
    app.register_blueprint(inventory_bp) 

    # ===== HEALTH CHECK =====
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "Inventory Service is running!"}), 200

    return app

# Gunicorn sẽ gọi create_app() để khởi động ứng dụng