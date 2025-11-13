# File: services/booking-service/app.py

import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

import sys # ✅ THÊM: Import sys
# ✅ THÊM: Thêm thư mục hiện tại (/app) vào Python Path để tìm thấy các module con
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) 

load_dotenv()

# Khởi tạo Extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager() 

def create_app():
    """Tạo và cấu hình Flask app chính cho Booking Service"""
    app = Flask(__name__)
    CORS(app)

    # ===== CẤU HÌNH =====
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["INTERNAL_SERVICE_TOKEN"] = os.getenv("INTERNAL_SERVICE_TOKEN")
    app.config["USER_SERVICE_URL"] = os.getenv("USER_SERVICE_URL")

    # ===== KHỞI TẠO EXTENSIONS =====
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db, directory='migrations', version_table='alembic_version_booking')

    # ===== IMPORT MODELS & TẠO TABLES =====
    with app.app_context():
        from models.booking_model import Booking # <-- Import model mới
        db.create_all()

    # ===== ĐĂNG KÝ BLUEPRINTS (Controllers) =====
    
    from controllers.booking_controller import booking_bp 
    from controllers.internal_controller import internal_bp # <-- THÊM DÒNG NÀY
    
    app.register_blueprint(booking_bp) 
    app.register_blueprint(internal_bp) # <-- VÀ DÒNG NÀY 

    # ===== HEALTH CHECK =====
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "Booking Service is running!"}), 200

    return app