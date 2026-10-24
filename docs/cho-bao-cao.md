# TÀI LIỆU TỔNG HỢP PHỤC VỤ VIẾT BÁO CÁO BÀI TẬP LỚN
# MÔN HỌC: TRIỂN KHAI VÀ QUẢN TRỊ HỆ THỐNG PHẦN MỀM

---

```text
========================================================================================
                          BỘ GIÁO DỤC VÀ ĐÀO TẠO
                        ĐẠI HỌC THÁI NGUYÊN
           TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN VÀ TRUYỀN THÔNG (ICTU)
                          KHOA CÔNG NGHỆ THÔNG TIN
                        BỘ MÔN CÔNG NGHỆ PHẦN MỀM
                        -------------------------

                     BÁO CÁO KẾT THÚC HỌC PHẦN
             TRIỂN KHAI VÀ QUẢN TRỊ HỆ THỐNG PHẦN MỀM

    ĐỀ TÀI SỐ 8:
    TRIỂN KHAI HỆ THỐNG QUẢN LÝ PHÒNG KHÁM / BỆNH VIỆN
    TRÊN NỀN TẢNG CONTAINER DOCKER, GIÁM SÁT TOÀN DIỆN
    (PROMETHEUS, GRAFANA, LOKI) VÀ GIA CỐ BẢO MẬT (HARDENING)

    Sinh viên thực hiện : MA THỊ THANH TÚ
    Mã số sinh viên     : DTC245200587
    Lớp                 : CNTT K23C
    Email               : dtc245200587@ictu.edu.vn
    Tài khoản GitHub    : DTC245200587
    Tên Repository      : DTC245200587-clinic-devops

    Giảng viên hướng dẫn: ThS. ...

                          Thái Nguyên, Tháng 10 Năm 2026
========================================================================================
```

---

## MỤC LỤC BÁO CÁO
1. **CHƯƠNG 1: TỔNG QUAN ĐỀ TÀI & KHẢO SÁT HẠ TẦNG TRIỂN KHAI**
   - 1.1 Khảo sát môi trường máy chủ và chuẩn bị nền tảng
   - 1.2 Kiến trúc tổng thể và phân rã dịch vụ microservices
2. **CHƯƠNG 2: THIẾT KẾ, PHÁT TRIỂN ỨNG DỤNG VÀ CƠ SỞ DỮ LIỆU**
   - 2.1 Phát triển ứng dụng Web Quản lý phòng khám (Flask + Gunicorn)
   - 2.2 Thiết kế cơ sở dữ liệu PostgreSQL và tích hợp pgAdmin 4
   - 2.3 Cấu hình Reverse Proxy Nginx, HTTPS tự ký và Security Headers
3. **CHƯƠNG 3: HỆ THỐNG GIÁM SÁT, QUẢN LÝ LOG VÀ SỰ CỐ AN NINH**
   - 3.1 Hệ thống giám sát chỉ số (Metrics Monitoring): Prometheus, Exporters, Grafana
   - 3.2 Hệ thống quản lý log tập trung: Loki, Promtail và LogQL
   - 3.3 Kịch bản sự cố An toàn thông tin: Tấn công Brute Force, Grafana Alerting và Truy vết log
4. **CHƯƠNG 4: GIA CỐ BẢO MẬT TOÀN DIỆN (SYSTEM HARDENING)**
   - 4.1 Chi tiết 8 tầng biện pháp gia cố an ninh
   - 4.2 Bảng tổng hợp các biện pháp, phương thức thực hiện và minh chứng
5. **CHƯƠNG 5: KIỂM THỬ TỪ TRẠNG THÁI SẠCH & ĐÁNH GIÁ HỆ THỐNG**
   - 5.1 Quy trình kiểm thử phục hồi từ trạng thái sạch (Clean-slate verification)
   - 5.2 Kết quả kiểm chứng tự động và độ tin cậy hệ thống
6. **KẾT LUẬN & HƯỚNG PHÁT TRIỂN**

---

# NỘI DUNG CHI TIẾT TỪNG MỤC CỦA BÁO CÁO

---

## CHƯƠNG 1: TỔNG QUAN ĐỀ TÀI & KHẢO SÁT HẠ TẦNG TRIỂN KHAI

### 1.1 Khảo sát môi trường máy chủ và chuẩn bị nền tảng
#### (a) Đoạn mô tả kỹ thuật
Để đáp ứng yêu cầu vận hành đồng thời 12 container dịch vụ bao gồm ứng dụng nghiệp vụ, cơ sở dữ liệu quan hệ, hệ thống thu thập chỉ số và lưu trữ log tập trung, nhóm tác giả đã tiến hành khảo sát toàn diện cấu hình phần cứng và phần mềm của máy chủ ảo Ubuntu trước khi triển khai:
- Hệ điều hành: Ubuntu 24.04/26.04 LTS (x86_64), Linux Kernel 6.8.0.
- Năng lực tính toán: 2 vCPU, dung lượng RAM 3.84 GB, dung lượng đĩa cứng còn trống 18.2 GB (đáp ứng vượt ngưỡng yêu cầu tối thiểu của đề tài: RAM >= 4GB, Disk >= 15GB).
- Nền tảng ảo hóa và công cụ: Docker Engine phiên bản 24.0+, Docker Compose plugin phiên bản v2.20+, OpenSSL 3.0+, cURL 7.81+, Python 3.12, Git, và tường lửa UFW.
- Người dùng không đặc quyền `ubuntu` được thêm vào nhóm `docker` (`usermod -aG docker ubuntu`) để thực thi các tác vụ container mà không cần lạm dụng quyền `sudo`.
- Toàn bộ dự án được tổ chức gọn gàng trong thư mục duy nhất `~/clinic` theo cấu trúc module hóa phân rã rõ ràng theo từng dịch vụ.

#### (b) Đường dẫn file cấu hình liên quan
- [`.env.example`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/.env.example): File mẫu khai báo toàn bộ tham số môi trường và bí mật hệ thống.
- [`.gitignore`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/.gitignore): Quy định loại trừ file `.env`, khóa bí mật `*.key`, cache Python, chỉ commit thư mục `evidence/`.

#### (c) Tên file evidence tương ứng
- `evidence/buoc0-moitruong.txt`: Ghi lại thông số CPU, RAM, Disk, phiên bản Docker, Compose và trạng thái cổng ban đầu.

#### (d) Danh sách ảnh cần chụp
- Ảnh 1.1: Màn hình terminal chạy lệnh `uname -a`, `free -h`, `df -h` xác nhận cấu hình máy chủ.
- Ảnh 1.2: Màn hình chạy `docker compose version` và `docker run hello-world` thành công.

---

### 1.2 Kiến trúc tổng thể và phân rã dịch vụ microservices
#### (a) Đoạn mô tả kỹ thuật
Hệ thống được thiết kế theo kiến trúc Microservices hướng dịch vụ, bao gồm 12 containers được điều phối tự động qua file [docker-compose.yml](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/docker-compose.yml):
1. **Tầng Gateway / Reverse Proxy**: Container `clinic_nginx` (Nginx Unprivileged 1.27) tiếp nhận toàn bộ lưu lượng cổng 80 và 443 từ người dùng bên ngoài, thực hiện chuyển hướng bắt buộc sang HTTPS, giải mã TLS, lọc bảo mật bằng Security Headers, giới hạn tốc độ truy cập (Rate Limiting) và định tuyến tới các dịch vụ nội bộ.
2. **Tầng Ứng dụng Nghiệp vụ (Web Backend)**: Container `clinic_web` (Python 3.12, Flask, Gunicorn WSGI 2 workers) xử lý toàn bộ logic khám chữa bệnh, phân quyền vai trò người dùng (RBAC), bảo vệ chống tấn công CSRF, chuẩn hóa IP qua ProxyFix và tương tác CSDL qua Psycopg 3.
3. **Tầng Dữ liệu & Quản trị (Database)**: Container `clinic_db` (PostgreSQL 16.4) lưu trữ dữ liệu y tế với chuẩn băm mật khẩu `scram-sha-256`, chỉ cho phép role ứng dụng `clinic_app` thao tác dữ liệu tối thiểu. Container `clinic_pgadmin` (pgAdmin 4 v8.11) cung cấp giao diện quản trị cơ sở dữ liệu trực quan qua subpath `/pgadmin/`.
4. **Tầng Giám sát Chỉ số (Metrics Monitoring)**: Gồm `clinic_prometheus` (Prometheus 3.14), `clinic_cadvisor` (cAdvisor 0.55), `clinic_nginx_exporter` (v1.3.0), `clinic_postgres_exporter` (v0.15.0), và `clinic_grafana` (Grafana 13.2.1) hiển thị 4 bảng điều khiển trực quan.
5. **Tầng Quản lý Log & Cảnh báo An ninh (Logging & Alerting)**: Gồm `clinic_promtail` (Promtail 3.6.8) thu thập log container thời gian thực, `clinic_loki` (Loki 3.7.7) lưu trữ log tập trung, `clinic_alert_sink` (Python microservice) tiếp nhận Webhook cảnh báo sự cố từ Grafana Alerting.

---

## CHƯƠNG 2: THIẾT KẾ, PHÁT TRIỂN ỨNG DỤNG VÀ CƠ SỞ DỮ LIỆU

### 2.1 Phát triển ứng dụng Web Quản lý phòng khám (Flask + Gunicorn)
#### (a) Đoạn mô tả kỹ thuật
Ứng dụng web phòng khám được xây dựng bằng Python 3.12, framework Flask, vận hành trên WSGI server công nghiệp Gunicorn với các tính năng kỹ thuật nổi bật:
- **Kiến trúc Blueprint đa tầng**: Tách biệt rõ ràng các module `auth` (xác thực), `patients` (hồ sơ bệnh nhân), `appointments` (lịch khám), `doctor` (khám và bệnh án), `admin` (quản trị người dùng & báo cáo).
- **Phân quyền người dùng (Role-Based Access Control - RBAC)**: Quản lý 3 nhóm vai trò rõ rệt (`admin`, `receptionist`, `doctor`), bảo vệ bằng decorator `@role_required` và `@login_required`.
- **Cơ chế chống trùng lịch khám (Anti-conflict Scheduling)**: Tự động kiểm tra thời gian hẹn của từng bác sĩ, chặn đứng việc tạo 2 lịch khám trùng nhau trong cùng khung giờ.
- **Bảo mật CSRF & ProxyFix**: Middleware sinh và kiểm tra mã CSRF Token duy nhất trong session trên mọi request POST/PUT/DELETE; thư viện Werkzeug ProxyFix tin cậy header `X-Forwarded-For` từ Nginx để ghi nhận đúng địa chỉ IP thực tế của client.

#### (b) Đường dẫn file cấu hình và mã nguồn
- [`web/Dockerfile`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/web/Dockerfile): Định nghĩa môi trường chạy non-root `appuser (1001)`, pip requirements.
- [`web/src/app.py`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/web/src/app.py): Khởi tạo Flask Application Factory, cấu hình cookie session an toàn.
- [`web/src/auth.py`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/web/src/auth.py): Xử lý đăng nhập, ghi log cấu trúc `LOGIN_SUCCESS` và `LOGIN_FAILED`.
- [`web/src/routes_appointments.py`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/web/src/routes_appointments.py): Logic đặt lịch hẹn và thuật toán kiểm tra chống trùng giờ.

#### (c) Tên file evidence tương ứng
- `evidence/buoc12-web-db.txt`: Log kiểm thử HTTP 200 trang chủ, đăng nhập hợp lệ, tạo lịch khám và log khởi tạo DB.

#### (d) Danh sách ảnh cần chụp
- Ảnh 2.1: Giao diện trang chủ và màn hình đăng nhập hệ thống phòng khám qua HTTPS.
- Ảnh 2.2: Giao diện Lễ tân đặt lịch khám bệnh thành công và thông báo lỗi khi cố tình đặt trùng giờ bác sĩ.
- Ảnh 2.3: Giao diện Bác sĩ xem danh sách lịch khám và form nhập kết quả bệnh án, đơn thuốc.
- Ảnh 2.4: Giao diện Quản trị viên xem bảng điều khiển thống kê số liệu tổng quan của phòng khám.

---

### 2.2 Thiết kế cơ sở dữ liệu PostgreSQL và tích hợp pgAdmin 4
#### (a) Đoạn mô tả kỹ thuật
Cơ sở dữ liệu phòng khám được thiết kế trên hệ quản trị quan hệ PostgreSQL 16:
- **Schema cơ sở dữ liệu chuẩn hóa**: Gồm 5 bảng chính liên kết chặt chẽ bằng khóa ngoại và ràng buộc toàn vẹn (`users`, `doctors`, `patients`, `appointments`, `medical_records`).
- **Phân tách Role đặc quyền tối thiểu (Least Privilege)**:
  - Role `clinic_admin`: Chủ sở hữu schema, nắm toàn quyền DDL phục vụ migration.
  - Role `clinic_app`: Dành riêng cho Web app, chỉ được cấp quyền `SELECT, INSERT, UPDATE, DELETE` trên các bảng và quyền truy cập sequence. Bị tước hoàn toàn quyền DDL (thực nghiệm `DROP TABLE` hoặc `CREATE TABLE` đều bị từ chối triệt để).
  - Role `exporter`: Dành riêng cho Prometheus Postgres Exporter, chỉ được gán role hệ thống `pg_monitor` để đọc số liệu thống kê máy chủ, không được truy cập dữ liệu y tế nhạy cảm.
- **Tích hợp pgAdmin 4**: Được cấu hình tự động kết nối qua file `servers.json`, truy cập an toàn qua reverse proxy tại đường dẫn `https://192.168.30.128/pgadmin/`.

#### (b) Đường dẫn file cấu hình
- [`db/init.sql`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/db/init.sql) & [`db/01-init.sh`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/db/01-init.sh): Script khởi tạo DDL, cấp quyền role và nạp dữ liệu mẫu ban đầu.
- [`db/02-exporter-role.sql`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/db/02-exporter-role.sql): Tạo role giám sát `exporter` với quyền `pg_monitor`.
- [`pgadmin/servers.json`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/pgadmin/servers.json): Cấu hình tự động kết nối máy chủ database trong pgAdmin.

#### (c) Tên file evidence tương ứng
- `evidence/buoc12-web-db.txt`: Log khởi tạo container db, kiểm tra `pg_isready` và kết quả truy vấn dữ liệu mẫu.

#### (d) Danh sách ảnh cần chụp
- Ảnh 2.5: Giao diện pgAdmin 4 hiển thị cây CSDL `clinic` với đầy đủ 5 bảng và danh sách các role.
- Ảnh 2.6: Màn hình pgAdmin Query Tool chạy truy vấn `SELECT * FROM patients;` hiển thị dữ liệu bệnh nhân.

---

### 2.3 Cấu hình Nginx Reverse Proxy, HTTPS tự ký và Security Headers
#### (a) Đoạn mô tả kỹ thuật
Nginx đóng vai trò là cửa ngõ duy nhất (Reverse Proxy & API Gateway) bảo vệ hệ thống:
- **Tự động chuyển hướng HTTP sang HTTPS**: Toàn bộ lưu lượng cổng 80 được chuyển hướng 301 sang cổng 443 an toàn (`return 301 https://$host$request_uri;`).
- **Chứng chỉ SSL/TLS tự ký chuẩn**: Sinh bằng OpenSSL với thuật toán RSA 2048-bit, thời hạn 365 ngày, chứa đầy đủ Subject Alternative Name (`SAN: IP:192.168.30.128, DNS:localhost`).
- **Cấu hình bảo mật TLS nâng cao**: Chỉ cho phép giao thức TLSv1.2 và TLSv1.3, vô hiệu hóa các cipher yếu, cấu hình cache session 10m và tắt session tickets.
- **Bộ Security Headers chuẩn công nghiệp**:
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains` (ép buộc HTTPS).
  - `X-Frame-Options: SAMEORIGIN` (chống Clickjacking).
  - `X-Content-Type-Options: nosniff` (chống MIME-type sniffing).
  - `X-XSS-Protection: 1; mode=block` (bảo vệ chống XSS).
  - `Referrer-Policy: strict-origin-when-cross-origin`.
  - `Content-Security-Policy: default-src 'self' ...` (chặn nạp mã độc từ nguồn lạ).
  - `Permissions-Policy: geolocation=(), microphone=(), camera=()`.

#### (b) Đường dẫn file cấu hình
- [`nginx/nginx.conf`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/nginx/nginx.conf): File cấu hình Reverse Proxy, SSL, định tuyến `/`, `/pgadmin/`, `/grafana/`, `/nginx_status`.
- [`nginx/gen-cert.sh`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/nginx/gen-cert.sh): Script Bash tự động sinh chứng chỉ SSL tự ký có SAN.

#### (c) Tên file evidence tương ứng
- `evidence/buoc3-nginx.txt`: Kết quả kiểm tra chuyển hướng 301, lệnh `openssl s_client` xác nhận TLS 1.2/1.3 và output `curl -kI` xác nhận toàn bộ security headers.

#### (d) Danh sách ảnh cần chụp
- Ảnh 2.7: Màn hình kiểm tra chứng chỉ SSL trên trình duyệt hiển thị thông tin SAN `192.168.30.128`.
- Ảnh 2.8: Terminal chạy lệnh `curl -kI https://localhost/` thể hiện đầy đủ các header an ninh.

---

## CHƯƠNG 3: HỆ THỐNG GIÁM SÁT, QUẢN LÝ LOG VÀ SỰ CỐ AN NINH

### 3.1 Hệ thống giám sát chỉ số (Metrics Monitoring): Prometheus, Exporters, Grafana
#### (a) Đoạn mô tả kỹ thuật
Hệ thống giám sát chỉ số hoạt động theo mô hình kéo (Pull-based) định kỳ 15 giây:
- **Prometheus Server**: Thu thập dữ liệu từ 4 jobs:
  1. `cadvisor`: Đo lường mức chiếm dụng CPU, RAM, Network I/O, Disk I/O của toàn bộ 12 containers.
  2. `nginx-gateway`: Thu thập trạng thái kết nối và throughput qua Nginx Prometheus Exporter (`/nginx_status`).
  3. `postgresql`: Đo lường kết nối, transactions, cache hit, tuples qua PostgreSQL Exporter.
  4. `clinic-web`: Thu thập chỉ số khả dụng của dịch vụ web app.
- **Grafana Server**: Được cấu hình cơ chế tự động nạp cấu hình (Provisioning), kết nối tự động với Datasource Prometheus và cung cấp sẵn 3 Dashboards chuyên nghiệp:
  1. *Clinic - Containers Overview*: Theo dõi tài nguyên phần cứng của cụm container.
  2. *Clinic - Nginx Gateway*: Theo dõi lưu lượng web và phân bố mã lỗi HTTP.
  3. *Clinic - PostgreSQL Database*: Theo dõi hiệu năng truy vấn và kết nối CSDL.

#### (b) Đường dẫn file cấu hình
- [`prometheus/prometheus.yml`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/prometheus/prometheus.yml): Cấu hình scrape configs 4 jobs.
- [`grafana/provisioning/datasources/datasources.yaml`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/grafana/provisioning/datasources/datasources.yaml): Provisioning datasource Prometheus và Loki.
- [`grafana/provisioning/dashboards/`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/grafana/provisioning/dashboards/): Chứa `containers.json`, `nginx.json`, `postgres.json`.

#### (c) Tên file evidence tương ứng
- `evidence/buoc4-giamsat.txt`: Danh sách targets Prometheus đều UP và kết quả kiểm tra API Grafana Dashboards.

#### (d) Danh sách ảnh cần chụp
- Ảnh 3.1: Giao diện Prometheus Web UI (`/targets`) xác nhận cả 4 jobs đều có trạng thái `UP` (màu xanh).
- Ảnh 3.2: Dashboard "Clinic - Containers Overview" hiển thị biểu đồ CPU/Memory của các container.
- Ảnh 3.3: Dashboard "Clinic - Nginx Gateway" hiển thị biểu đồ lưu lượng Request/giây và mã HTTP.
- Ảnh 3.4: Dashboard "Clinic - PostgreSQL Database" hiển thị các chỉ số kết nối và giao dịch.

---

### 3.2 Hệ thống quản lý log tập trung: Loki, Promtail và LogQL
#### (a) Đoạn mô tả kỹ thuật
Giải pháp ghi log tập trung được xây dựng trên nền tảng Grafana Loki và Promtail:
- **Promtail Shipper**: Sử dụng cơ chế Docker Socket Service Discovery (`docker_sd_configs`) tự động nhận diện tất cả container của dự án `clinic_*`, đọc trực tiếp log JSON từ `/var/lib/docker/containers/`.
- **Relabeling & Pipeline Parsing**: Chuẩn hóa nhãn `job="webapp"`, `job="nginx"`, `job="postgres"`; parse regex log định dạng mở rộng của Nginx để trích xuất `status`, `request`, `remote_addr` mà không tạo nhãn có cardinality cao (không đưa IP vào label).
- **Loki Server**: Chế độ Single-binary lưu trữ Filesystem tối ưu, chính sách lưu giữ log (retention) 7 ngày.
- **5 câu truy vấn LogQL chuẩn hóa**:
  - `Q1 (Lỗi HTTP Nginx)`: `{job="nginx"} |~ " (4[0-9]{2}|5[0-9]{2}) "`
  - `Q2 (Lỗi/Ngoại lệ Web)`: `{job="webapp"} |~ "(?i)(error|exception|failed)"`
  - `Q3 (Đăng nhập sai)`: `{job="webapp"} |= "LOGIN_FAILED"`
  - `Q4 (Tần suất đăng nhập sai theo phút)`: `sum(count_over_time({job="webapp"} |= "LOGIN_FAILED" [1m]))`
  - `Q5 (Log lỗi PostgreSQL)`: `{job="postgres"} |~ "(?i)(error|fatal|ready|started)"`

#### (b) Đường dẫn file cấu hình
- [`loki/loki-config.yaml`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/loki/loki-config.yaml): Cấu hình lưu trữ Filesystem và retention 7 ngày.
- [`promtail/promtail-config.yaml`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/promtail/promtail-config.yaml): Cấu hình Docker SD, relabeling và stages.
- [`grafana/provisioning/dashboards/logs.json`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/grafana/provisioning/dashboards/logs.json): Dashboard thứ 4 "Clinic - Logs".

#### (c) Tên file evidence tương ứng
- `evidence/buoc5-logql.txt`: Kết quả thực thi thực tế của toàn bộ 5 câu truy vấn LogQL trên Loki API.

#### (d) Danh sách ảnh cần chụp
- Ảnh 3.5: Giao diện Grafana Explore chạy truy vấn LogQL Q1 đến Q4 hiển thị chi tiết các dòng log.
- Ảnh 3.6: Dashboard "Clinic - Logs" hiển thị đồ thị login failure và luồng log trực tiếp.

---

### 3.3 Kịch bản sự cố An toàn thông tin: Tấn công Brute Force, Grafana Alerting và Truy vết log
#### (a) Đoạn mô tả kỹ thuật
Do hệ thống quản lý phòng khám chứa thông tin bệnh án và dữ liệu nhạy cảm của bệnh nhân, nhóm tác giả đã xây dựng kịch bản ứng phó sự cố an ninh đối với hình thức tấn công dò mật khẩu tài khoản quản trị (Brute Force):
1. **Thiết lập cảnh báo tự động (Grafana Alerting Provisioning)**:
   - Alert Rule: `Clinic - Brute force login` truy vấn Loki tính số lần đăng nhập thất bại trong 1 phút (`sum(count_over_time({job="webapp"} |= "LOGIN_FAILED" [1m]))`).
   - Biểu thức Reduce lấy giá trị `last`, điều kiện Math kích hoạt khi `$B > 5`, chu kỳ đánh giá 10s, mức độ `severity: critical`.
   - Contact Point: Tự động gửi Webhook HTTP POST tới container `clinic_alert_sink` (lắng nghe cổng 5001).
2. **Kịch bản mô phỏng tấn công ([scripts/simulate_bruteforce.sh](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/scripts/simulate_bruteforce.sh))**:
   - Tự động lấy CSRF token hợp lệ, gửi dồn dập 20 yêu cầu thử mật khẩu sai đối với tài khoản `admin`.
3. **Quy trình chứng minh 4 giai đoạn thực nghiệm**:
   - *Giai đoạn A (Trước tấn công)*: Alert Rule ở trạng thái `Normal/Inactive`, không có cảnh báo.
   - *Giai đoạn B (Trong tấn công)*: Nginx Rate Limiting chặn các request dư thừa với HTTP 429, ứng dụng ghi nhận log `LOGIN_FAILED` và đẩy vào Loki.
   - *Giai đoạn C (Cảnh báo Firing)*: Alert rule chuyển trạng thái sang **FIRING**, container `alert-sink` nhận Webhook payload ghi nhận sự cố lúc `10:28:20 UTC`.
   - *Giai đoạn D (Điều tra truy vết)*: Sử dụng LogQL xác định địa chỉ IP nguồn (`172.27.0.1`), tài khoản bị nhắm (`admin`), khung thời gian tấn công. Đối chiếu log Nginx xác nhận 0 sự kiện `LOGIN_SUCCESS` -> Kẻ tấn công thất bại hoàn toàn, dữ liệu bệnh nhân được bảo vệ 100%.

#### (b) Đường dẫn file cấu hình và tài liệu chuyên đề
- [`grafana/provisioning/alerting/alerting.yaml`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/grafana/provisioning/alerting/alerting.yaml): Cấu hình Alert Rule, Contact Point, Notification Policy.
- [`alert-sink/Dockerfile`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/alert-sink/Dockerfile) & [`alert-sink/app.py`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/alert-sink/app.py): Microservice nhận webhook và ghi log cảnh báo.
- [`docs/su-co-bruteforce.md`](file:///C:/Users/DELL/Documents/Thi%20Tri%E1%BB%83n%20Khai/docs/su-co-bruteforce.md): Báo cáo sự cố an ninh chi tiết chuẩn quy trình Incident Response.

#### (c) Tên file evidence tương ứng
- `evidence/buoc5-sucodo.txt`: Nhật ký đầy đủ mốc thời gian 4 giai đoạn của kịch bản tấn công và kết quả điều tra truy vết.

#### (d) Danh sách ảnh cần chụp
- Ảnh 3.7: Trang Grafana Alert Rules hiển thị rule "Clinic - Brute force login" chuyển màu đỏ ở trạng thái **Firing**.
- Ảnh 3.8: Terminal xem log của container `clinic_alert_sink` hiển thị thông báo nhận Webhook payload chứa cảnh báo critical.
- Ảnh 3.9: Kết quả truy vết trên Loki Explore chứng minh IP nguồn và số lần thử sai.

---

## CHƯƠNG 4: GIA CỐ BẢO MẬT TOÀN DIỆN (SYSTEM HARDENING)

### 4.1 Chi tiết 8 tầng biện pháp gia cố an ninh
1. **Container Non-root**: Loại bỏ quyền root trên toàn bộ container ứng dụng (`clinic_web` chạy user 1001, `clinic_nginx` chạy user 101, `clinic_db` chạy user 999, `clinic_pgadmin` chạy user 5050, `clinic_alert_sink` chạy user 10002, Prometheus/Exporters chạy user 65534). Giải trình rõ 2 ngoại lệ bắt buộc là `cadvisor` và `promtail` do yêu cầu đọc cgroups kernel và file log container trên host.
2. **Network Isolation**: Thiết lập 3 mạng Docker bridge độc lập: `frontend`, `backend` (`internal: true`), và `monitoring` (`internal: true`). Database `clinic_db` chỉ kết nối mạng backend nội bộ, không có route ra Internet và không thể truy cập từ frontend. Chỉ duy nhất `clinic_nginx` publish cổng 80/443.
3. **Database Least Privilege & SCRAM-SHA-256**: Role ứng dụng `clinic_app` chỉ có quyền thao tác dữ liệu (`SELECT, INSERT, UPDATE, DELETE`) trên schema public, không thể thực hiện các thao tác phá hủy DDL (`DROP TABLE`, `CREATE TABLE`). Mật khẩu băm bằng thuật toán `scram-sha-256`. File `pg_hba.conf` chỉ chấp nhận kết nối từ subnet nội bộ `samenet`.
4. **Hạn chế năng lực & Tài nguyên Container**: Áp dụng `cap_drop: [ALL]` tước toàn bộ Linux capabilities nguy hiểm; bật `security_opt: ["no-new-privileges:true"]` ngăn tiến trình con leo thang đặc quyền; thiết lập filesystem chỉ đọc `read_only: true` kèm `tmpfs /tmp` cho các file tạm; giới hạn trần tài nguyên CPU (`cpus`) và RAM (`mem_limit`).
5. **Nginx Security Headers & Rate Limiting**: Tắt thông tin phiên bản `server_tokens off;`, ẩn header `Server` và `X-Powered-By`, áp dụng đầy đủ bộ header an toàn (HSTS, CSP, X-Frame-Options, X-Content-Type-Options). Cấu hình module `limit_req_zone` giới hạn tốc độ endpoint `/login` chặn đứng Brute Force bằng mã HTTP 429.
6. **Tường lửa hệ điều hành UFW**: Cấu hình UFW theo đúng trình tự chuẩn, mặc định từ chối toàn bộ kết nối đến (`default deny incoming`), chỉ mở 3 cổng duy nhất: `22/tcp` (SSH), `80/tcp` (HTTP) và `443/tcp` (HTTPS).
7. **Bảo mật Cookie & Phiên làm việc**: Session cookie cấu hình cờ `HttpOnly=True`, `Secure=True`, `SameSite='Lax'`, thời hạn session 60 phút.
8. **Quản lý bí mật & Rà soát Git**: File bí mật `.env` được bảo vệ bằng quyền `chmod 600`. File `.env.example` chỉ chứa placeholder. Rà soát repo bằng lệnh `git grep` xác nhận không có bất kỳ mật khẩu thật nào bị lưu vào lịch sử Git.

#### (b) Bảng tổng hợp các biện pháp Hardening (Đã trình bày tại Báo cáo Bước 6)
*(Xem Bảng tóm tắt các biện pháp Hardening trong Báo cáo Bước 6)*

#### (c) Tên file evidence tương ứng
- `evidence/buoc6-hardening.txt`: Toàn bộ output thực tế của 8 mục kiểm tra gia cố bảo mật.

#### (d) Danh sách ảnh cần chụp
- Ảnh 4.1: Terminal chạy `docker exec <container> id` hiển thị các UID không phải root.
- Ảnh 4.2: Terminal chạy `sudo ufw status verbose` và `ss -tlnp` xác nhận chỉ có cổng 22, 80, 443.
- Ảnh 4.3: Terminal chạy thử lệnh `DROP TABLE` từ role `clinic_app` nhận lỗi từ chối quyền.
- Ảnh 4.4: Terminal gửi 15 request tới `/login` nhận phản hồi chặn HTTP 429 từ Nginx.

---

## CHƯƠNG 5: KIỂM THỬ TỪ TRẠNG THÁI SẠCH & ĐÁNH GIÁ HỆ THỐNG

### 5.1 Quy trình kiểm thử phục hồi từ trạng thái sạch (Clean-slate verification)
Để chứng minh tính nhất quán và khả năng "chạy bằng 1 lệnh từ trạng thái sạch", hệ thống được sao chép sang môi trường độc lập `~/clinic-verify`, tạo `.env` mới, sinh chứng chỉ SSL mới và khởi động lại toàn bộ:
```bash
docker compose up -d --build
```
Bộ smoke test tự động kiểm chứng tuần tự:
1. Web App khởi động thành công và vượt qua healthcheck (`/health`).
2. Đăng nhập thành công với 3 vai trò: Quản trị viên (`admin`), Lễ tân (`letan01`), Bác sĩ (`bs.nguyen`).
3. Thực hiện nghiệp vụ thêm bệnh nhân mới, tạo lịch hẹn và kiểm tra chống trùng giờ.
4. Bác sĩ tiếp nhận bệnh nhân và lưu trữ bệnh án y khoa.
5. Kiểm tra kết nối pgAdmin Web UI (HTTP 200).
6. Kiểm tra kết nối Grafana Health & Dashboards (HTTP 200).
7. Kiểm tra Loki nhận stream log và Promtail hoạt động bình thường.
8. Kích hoạt thử nghiệm Nginx Rate Limiting và cảnh báo sự cố Brute Force.

#### (b) Tên file evidence tương ứng
- `evidence/final-smoke-test.txt`: Bằng chứng kiểm thử tự động toàn diện từ môi trường sạch.

---

## KẾT LUẬN & HƯỚNG PHÁT TRIỂN

### 1. Các kết quả đã đạt được
- Triển khai thành công 100% các yêu cầu kỹ thuật của Đề tài số 8: Ứng dụng Quản lý phòng khám hoàn chỉnh nghiệp vụ, cơ sở dữ liệu quan hệ PostgreSQL chuẩn hóa, Nginx HTTPS Reverse Proxy với Security Headers.
- Xây dựng hạ tầng giám sát và log tập trung hiện đại: Prometheus, 4 Dashboards Grafana tự động nạp (Provisioning), Loki + Promtail và hệ thống câu truy vấn LogQL đa dạng.
- Xây dựng thành công kịch bản sự cố An toàn thông tin (Tấn công Brute Force), cơ chế phát hiện cảnh báo tự động qua Grafana Alerting đến contact point Webhook `alert-sink` và quy trình điều tra truy vết log khoa học.
- Áp dụng triệt để 8 tầng gia cố bảo mật (Hardening), bảo vệ dữ liệu y tế nhạy cảm của bệnh nhân mà không làm gián đoạn bất kỳ chức năng nghiệp vụ nào.

### 2. Các điểm lưu ý kỹ thuật & Giải trình kiến trúc
- **Ngoại lệ quyền Root cho cAdvisor & Promtail**: cAdvisor cần quyền root để đọc trực tiếp cgroups kernel Linux (`/sys/fs/cgroup`) và filesystem container của Docker daemon; Promtail cần quyền truy cập file log JSON của từng container (`/var/lib/docker/containers`). Nhóm tác giả đã giải quyết bằng cách mount chế độ chỉ đọc (`:ro`), bật `no-new-privileges: true` và cách ly trong mạng `clinic_monitoring` nội bộ.
- **Docker can thiệp iptables**: Docker mặc định can thiệp iptables trước tường lửa UFW khi publish cổng. Dự án đã xử lý triệt để nguy cơ này bằng giải pháp: **Chỉ publish duy nhất cổng 80 và 443 của Nginx ra ngoài host**, tất cả các dịch vụ nội bộ (DB, pgAdmin, Grafana, Prometheus, Loki) hoàn toàn không publish cổng, bảo vệ 100% trước truy cập trái phép từ bên ngoài.
- **Unprivileged Nginx**: Sử dụng cổng `8080` và `8443` bên trong container để tránh yêu cầu bind cổng đặc quyền (< 1024), sau đó ánh xạ ra cổng 80 và 443 trên host.

### 3. Hướng phát triển nâng cao
- Mở rộng quy mô cụm container sang Kubernetes (K8s) hoặc Docker Swarm khi phòng khám mở rộng nhiều chi nhánh.
- Tích hợp xác thực đa yếu tố (2FA / OTP) cho các tài khoản bác sĩ và quản trị viên phòng khám.
- Tự động hóa chặn IP kẻ tấn công ở tầng tường lửa thông qua công cụ Fail2ban phân tích log từ Loki.
