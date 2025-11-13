# File: services/maintenance-service/app.py
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
    """Tạo và cấu hình Flask app chính cho Maintenance Service"""
    app = Flask(__name__)
    CORS(app)

    # ===== CẤU HÌNH (Lấy từ .env) =====
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["INTERNAL_SERVICE_TOKEN"] = os.getenv("INTERNAL_SERVICE_TOKEN")
    app.config["BOOKING_SERVICE_URL"] = os.getenv("BOOKING_SERVICE_URL")
    app.config["USER_SERVICE_URL"] = os.getenv("USER_SERVICE_URL")
    
    # ===== KHỞI TẠO EXTENSIONS =====
    db.init_app(app)
    jwt.init_app(app)
    # Cấu hình migration riêng cho Maintenance Service
    migrate.init_app(app, db, directory='migrations', version_table='alembic_version_maintenance')

    # ===== IMPORT MODELS & TẠO TABLES =====
    with app.app_context():
        from models.maintenance_model import MaintenanceTask 
        db.create_all()

    # ===== ĐĂNG KÝ BLUEPRINTS (Controllers) =====
    from controllers.maintenance_controller import maintenance_bp
    app.register_blueprint(maintenance_bp) 

    # ===== HEALTH CHECK =====
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "Maintenance Service is running!"}), 200

    return app