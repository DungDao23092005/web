docker-compose up -d --force-recreate listing-service
docker-compose up -d --build frontend
docker-compose down -v
"\\wsl.localhost\docker-desktop\mnt\docker-desktop-disk\data\docker\volumes\second-handevbatterytradingplatform_listing_uploads_data"

Move-Item -Path .\app\* -Destination .\ # Di chuyển toàn bộ nội dung bên trong thư mục app ra thư mục hiện tại

<!-- lần đầu chạy -->
<!-- 1. xây dựng (build) và chạy container của chương trình ở chế độ nền -->

docker-compose up -d --build

<!-- 2. tạo và cập nhật cơ sở dữ liệu trong Flask -->
<!-- db init: khởi tạo thư mục migration. -->
<!-- db migrate: tạo file migration (các thay đổi bảng). -->
<!-- db upgrade: áp dụng migration vào database. -->

 <!-- user-service -->

docker-compose exec user-service flask db init
docker-compose exec user-service flask db migrate -m "Initial user service tables"
docker-compose exec user-service flask db upgrade

<!-- inventory-service -->

docker-compose exec inventory-service flask db init
docker-compose exec inventory-service flask db migrate -m "Initial inventory service tables"
docker-compose exec inventory-service flask db upgrade

<!-- booking-service -->

docker-compose exec booking-service flask db init
docker-compose exec booking-service flask db migrate -m "Initial booking service tables"
docker-compose exec booking-service flask db upgrade

<!-- finance-service -->

docker-compose exec finance-service flask db init
docker-compose exec finance-service flask db migrate -m "Initial finance service tables"
docker-compose exec finance-service flask db upgrade

<!-- maintenance-service -->

docker-compose exec maintenance-service flask db init
docker-compose exec maintenance-service flask db migrate -m "Initial maintenance service tables"
docker-compose exec maintenance-service flask db upgrade

<!-- Payment-service -->

docker-compose exec payment-service flask db init
docker-compose exec payment-service flask db migrate -m "Initial payment service tables"
docker-compose exec payment-service flask db upgrade

<!-- tạo tài khoản admin(có hàm trong user-service/app.py) -->

docker-compose exec user-service flask create-admin admin1 kyu764904@gmail.com 12345

<!-- xem log (nhật ký chạy) của container(thay tên service để có thể xem log của các service khác) -->

docker-compose logs -f transaction-service

<!-- vào terminal bên trong container transaction_db(thay tên db để có thể xem log của các db khác -->

docker exec -it transaction_db bash

<!-- mở PostgreSQL CLI và kết nối vào database transaction_db(thay tên db để có thể xem log của các db khác với user db_user (POSTGRES_USER=db_user trong .env) -->

psql -U db_user -d transaction_db

<!-- xóa toàn bộ dữ liệu trong bảng -->

TRUNCATE TABLE transaction_db CASCADE;

<!-- xóa toàn bộ dữ liệu bảng transaction, đặt lại ID về 1, và xóa cả dữ liệu ở bảng liên quan (CASCADE). -->

TRUNCATE TABLE transaction RESTART IDENTITY CASCADE;

<!-- các câu lệnh truy vấn csdl -->

select _ from
INSERT INTO ... () VALUES ();
UPDATE ... SET * = * WHERE * = *;
select _ from ...;
DELETE FROM ... WHERE _ = _;
UPDATE auctions SET start_time = start_time::date + interval '8 hour 5 minute', end_time = start_time::date + interval '10 hour 5 minute' WHERE EXTRACT(HOUR FROM start_time) = 8;
UPDATE auctions SET auction_status = 'started' where auction_id = 1;
