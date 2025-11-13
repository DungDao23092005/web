# File: migrations/create_token.py
from flask import Flask
from flask_jwt_extended import create_access_token, JWTManager

# 1️⃣ Tạo Flask app tạm
app = Flask(__name__)

# 2️⃣ Đặt secret key (phải khớp với JWT_SECRET_KEY trong .env)
app.config["JWT_SECRET_KEY"] = "supersecretkey_for_ev_system"
jwt = JWTManager(app)

# 3️⃣ Sinh token vĩnh viễn cho service nội bộ
with app.app_context():
    system_identity = {"role": "system", "service_name": "internal_comm"}

    system_token = create_access_token(
        identity=system_identity,
        expires_delta=False  # Token không bao giờ hết hạn
    )

    print("\n✅ TẠO TOKEN THÀNH CÔNG!")
    print("---------------------------------")
    print("SAO CHÉP TOÀN BỘ DÒNG DƯỚI ĐÂY:")
    print(f"Bearer {system_token}")
    print("---------------------------------")
    print("(Dán dòng trên vào file .env với tên INTERNAL_SERVICE_TOKEN)\n")
