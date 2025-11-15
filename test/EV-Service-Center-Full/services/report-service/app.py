# File: services/report-service/app.py
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
    """Tạo và cấu hình Flask app chính cho Report Service"""
    app = Flask(__name__)
    CORS(app)

    # ===== CẤU HÌNH (Lấy từ .env) =====
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["INTERNAL_SERVICE_TOKEN"] = os.getenv("INTERNAL_SERVICE_TOKEN")
    
    # Lấy URL của các service khác
    app.config["USER_SERVICE_URL"] = os.getenv("USER_SERVICE_URL")
    app.config["BOOKING_SERVICE_URL"] = os.getenv("BOOKING_SERVICE_URL")
    app.config["FINANCE_SERVICE_URL"] = os.getenv("FINANCE_SERVICE_URL")
    app.config["MAINTENANCE_SERVICE_URL"] = os.getenv("MAINTENANCE_SERVICE_URL")
    app.config["INVENTORY_SERVICE_URL"] = os.getenv("INVENTORY_SERVICE_URL")
    
    # ===== KHỞI TẠO EXTENSIONS =====
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db, directory='migrations', version_table='alembic_version_report')

    # ===== IMPORT MODELS & TẠO TABLES =====
    with app.app_context():
        from models.report_model import Report 
        db.create_all()

    # ===== ĐĂNG KÝ BLUEPRINTS (Controllers) =====
    from controllers.report_controller import report_bp
    app.register_blueprint(report_bp) 

    # ===== HEALTH CHECK =====
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "Report Service is running!"}), 200

    return app