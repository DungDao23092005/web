# ========== BASE IMAGE ==========
FROM python:3.9-slim

# ========== WORKDIR ==========
WORKDIR /app

# ========== CÀI ĐẶT THƯ VIỆN ==========
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ========== COPY SOURCE CODE ==========
COPY . .

# ========== CẤU HÌNH ENV ==========
ENV PYTHONUNBUFFERED=1

# ========== EXPOSE PORT ==========
EXPOSE 8001

# ========== CHẠY APP BẰNG GUNICORN ==========
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "app:create_app()"]