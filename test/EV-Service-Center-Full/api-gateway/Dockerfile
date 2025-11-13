# Dùng image Nginx
FROM nginx:1.25-alpine

# Xóa file config mặc định của Nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copy file nginx.conf đã cấu hình của bạn vào
COPY ./api-gateway/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]