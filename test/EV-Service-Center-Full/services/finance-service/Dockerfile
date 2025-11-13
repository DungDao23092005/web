FROM python:3.9-slim
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app
WORKDIR $APP_HOME

# ⚠️ THÊM BIẾN MÔI TRƯỜNG MỚI CHO GUNICORN
ENV GUNICORN_ENV=true

RUN apt-get update 

COPY services/finance-service/requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

COPY services/finance-service/ $APP_HOME 

EXPOSE 8002

# Lệnh CMD CHUẨN cho Production
CMD ["gunicorn", "--bind", "0.0.0.0:8002", "app:create_app()", "--workers", "4"]