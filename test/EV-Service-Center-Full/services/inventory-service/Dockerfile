# services/inventory-service/Dockerfile
# Dùng base image giống user-service
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV PYTHONUNBUFFERED=1

# Đổi cổng sang 8000
EXPOSE 8000

# ✅ SỬA LỖI Ở ĐÂY: Dùng Gunicorn, không phải Uvicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:create_app()"]