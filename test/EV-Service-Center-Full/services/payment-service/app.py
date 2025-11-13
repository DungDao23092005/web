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
    """Tạo và cấu hình Flask app chính cho Payment Service"""
    app = Flask(__name__)
    CORS(app)

    # ===== CẤU HÌNH (Lấy từ .env) =====
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Lấy và làm sạch JWT_SECRET_KEY
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if jwt_secret:
        app.config["JWT_SECRET_KEY"] = jwt_secret.strip()

    # Lấy và làm sạch INTERNAL_SERVICE_TOKEN (Bắt buộc cho giao tiếp nội bộ)
    internal_token = os.getenv("INTERNAL_SERVICE_TOKEN")
    if internal_token:
        app.config["INTERNAL_SERVICE_TOKEN"] = internal_token.strip()

    app.config["FINANCE_SERVICE_URL"] = os.getenv("FINANCE_SERVICE_URL")
    # ✅ THÊM DÒNG NÀY: Đọc biến môi trường MOMO QR và đưa vào cấu hình Flask
    app.config["MOMO_QR_CODE_URL"] = os.getenv("MOMO_QR_CODE_URL")
    
    # ===== KHỞI TẠO EXTENSIONS =====
    db.init_app(app)
    jwt.init_app(app)
    # Cấu hình migration riêng cho Payment Service
    migrate.init_app(app, db, directory='migrations', version_table='alembic_version_payment')

    # ===== IMPORT MODELS & TẠO TABLES (CHỈ TRONG CLI/LẦN ĐẦU) =====
    # KHÔNG gọi db.create_all() ở đây khi chạy Gunicorn để tránh worker crash
    with app.app_context():
        from models.payment_model import PaymentTransaction
        # db.create_all() # <-- BỎ DÒNG NÀY ĐI

    # ===== ĐĂNG KÝ BLUEPRINTS (Controllers) =====
    from controllers.payment_controller import payment_bp
    
    app.register_blueprint(payment_bp) 

    # ===== HEALTH CHECK =====
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "Payment Service is running!"}), 200

    return app

# Kích hoạt db.create_all() thủ công khi chạy CLI (migration)
if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # Chỉ chạy db.create_all() khi chạy trực tiếp hoặc trong môi trường CLI
        from models.payment_model import PaymentTransaction
        db.create_all() 
    app.run(host='0.0.0.0', port=8004, debug=True)