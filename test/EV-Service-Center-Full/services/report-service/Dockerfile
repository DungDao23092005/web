# File: services/report-service/Dockerfile
FROM python:3.9-slim
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app
WORKDIR $APP_HOME

RUN apt-get update 

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy tất cả các file code
COPY . $APP_HOME 

# Port mới cho service
EXPOSE 8006

# Lệnh CMD CHUẨN
CMD ["gunicorn", "--bind", "0.0.0.0:8006", "app:create_app()"]