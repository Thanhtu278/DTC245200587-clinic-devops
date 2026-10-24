# DTC245200587-clinic-devops: Hệ Thống Quản Lý Phòng Khám / Bệnh Viện

## 1. Thông Tin Sinh Viên
- **Họ và tên**: Ma Thị Thanh Tú
- **Mã số sinh viên**: DTC245200587
- **Lớp**: CNTT K23C
- **Email**: dtc245200587@ictu.edu.vn
- **Tài khoản GitHub**: DTC245200587
- **Tên Repository**: DTC245200587-clinic-devops
- **Môn học**: Triển khai và Quản trị Hệ thống Phần mềm
- **Đề tài 8**: Hệ thống Quản lý Phòng khám / Bệnh viện

## 2. Kiến Trúc & Công Nghệ Triển Khai
- **Backend / Web**: Python 3.12 (Flask + Gunicorn, Psycopg 3, RBAC, CSRF, ProxyFix)
- **Database**: PostgreSQL 16 (Tách biệt quyền admin, role ứng dụng `clinic_app`, role `exporter` với `pg_monitor`)
- **Database Management**: pgAdmin 4 (Reverse proxy qua đường dẫn con `/pgadmin/`)
- **Reverse Proxy & SSL**: Nginx 1.27 Alpine (HTTPS tự ký, TLS 1.2/1.3, Security Headers: HSTS, CSP, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy)
- **Monitoring**: Prometheus (scrape 4 jobs) + Grafana (3 dashboards provisioning: Containers, Nginx, PostgreSQL)
- **Log Management**: Loki + Promtail (Thu thập access log định dạng đầy đủ, truy vấn LogQL, cảnh báo an toàn)
- **Orchestration**: Docker Compose v2 (`docker compose up -d`)

## 3. Cấu Trúc Thư Mục
```text
clinic/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── web/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
├── db/
│   ├── 01-init.sh
│   ├── 02-exporter-role.sql
│   └── init.sql
├── pgadmin/
│   └── servers.json
├── nginx/
│   ├── gen-cert.sh
│   ├── nginx.conf
│   └── certs/
│       └── server.crt
├── prometheus/
│   └── prometheus.yml
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── datasources.yaml
│       └── dashboards/
│           ├── dashboards.yaml
│           ├── containers.json
│           ├── nginx.json
│           └── postgres.json
├── loki/
│   └── loki-config.yaml
├── promtail/
│   └── promtail-config.yaml
├── alert-sink/
│   ├── Dockerfile
│   └── app.py
├── scripts/
│   ├── gen-cert.sh
│   ├── simulate_bruteforce.sh
│   ├── verify_buoc3.sh
│   ├── verify_buoc4.sh
│   └── verify_buoc5.sh
├── evidence/
│   ├── buoc3-nginx.txt
│   ├── buoc4-giamsat.txt
│   ├── buoc5-logql.txt
│   └── buoc5-sucodo.txt
└── docs/
    └── su-co-bruteforce.md
```

## 4. Hướng Dẫn Khởi Chạy Nhanh

### Bước 1: Chuẩn bị biến môi trường
```bash
cp .env.example .env
# Chỉnh sửa mật khẩu bảo mật trong .env nếu cần
```

### Bước 2: Sinh chứng chỉ SSL/TLS tự ký
Dự án cung cấp sẵn script `nginx/gen-cert.sh` để sinh chứng chỉ tự ký với CN=192.168.30.128, SAN IP:192.168.30.128 và DNS:localhost:
```bash
chmod +x nginx/gen-cert.sh
./nginx/gen-cert.sh
```
*Lưu ý: File khóa bí mật `server.key` được bảo vệ nghiêm ngặt và tự động loại trừ khỏi Git qua `.gitignore`.*

### Bước 3: Khởi chạy toàn bộ hệ thống bằng Docker Compose
```bash
docker compose up -d --build
```

### Bước 4: Khởi tạo Role Exporter cho PostgreSQL (Nếu volume DB đã tồn tại từ trước)
Nếu volume `db_data` đã được khởi tạo trước đó, entrypoint SQL sẽ không tự chạy lại. Để tạo role `exporter` giám sát cơ sở dữ liệu:
```bash
docker compose exec -T db psql -U clinic_admin -d clinic < db/02-exporter-role.sql
```

### Bước 5: Kiểm tra trạng thái các container
```bash
docker compose ps
docker compose exec nginx nginx -t
```

### Bước 6: Chạy kịch bản mô phỏng sự cố An toàn thông tin (Tấn công Brute Force)
Để kích hoạt cảnh báo Grafana Alerting và kiểm tra truy vết log:
```bash
./scripts/simulate_bruteforce.sh
```
Xem báo cáo chi tiết sự cố tại: [`docs/su-co-bruteforce.md`](docs/su-co-bruteforce.md).

## 5. Truy Cập Hệ Thống & Giám Sát

### 5.1 Các Đường Dẫn Chính
- **Ứng dụng Phòng khám (Web App)**: `https://192.168.30.128` hoặc `https://localhost`
  *(Tự động chuyển hướng từ cổng 80 HTTP sang HTTPS)*
- **Quản trị Database (pgAdmin 4)**: `https://192.168.30.128/pgadmin/`
- **Hệ thống Giám sát Grafana**: `https://192.168.30.128/grafana/`
- **Prometheus UI (Mạng nội bộ - Truy cập qua SSH Tunnel)**:
  Vì cổng 9090 không publish ra ngoài để đảm bảo an toàn, sử dụng lệnh sau từ máy cá nhân để mở tunnel:
  ```bash
  ssh -L 9090:localhost:9090 ubuntu@192.168.30.128
  ```
  Sau đó truy cập: `http://localhost:9090/targets`

### 5.2 Tài Khoản & Quản Lý Bí Mật
*Theo quy tắc Hardening, toàn bộ mật khẩu thực tế được quản lý độc quyền và an toàn trong file `.env` (phân quyền `chmod 600`), không ghi trực tiếp mật khẩu thật vào tài liệu để phòng ngừa rò rỉ mã nguồn.*

| Dịch vụ / Hệ thống | Tên đăng nhập | Biến môi trường mật khẩu trong `.env` | Ghi chú |
| :--- | :--- | :--- | :--- |
| **Web - Admin** | `admin` | `APP_ADMIN_PASSWORD` | Quản trị viên phòng khám (>=16 ký tự) |
| **Web - Lễ tân** | `letan01` | `APP_LETAN_PASSWORD` | Tiếp đón bệnh nhân, đặt lịch |
| **Web - Bác sĩ** | `bs.nguyen` | `APP_DOCTOR_PASSWORD` | Lịch khám và hồ sơ bệnh án |
| **pgAdmin 4** | `dtc245200587@ictu.edu.vn` | `PGADMIN_DEFAULT_PASSWORD` | Quản trị CSDL PostgreSQL (>=16 ký tự) |
| **Grafana** | `admin` | `GRAFANA_ADMIN_PASSWORD` | Xem 4 Dashboards & Alerting (>=16 ký tự) |
| **PostgreSQL Exporter** | `exporter` | `PG_EXPORTER_PASSWORD` | Role chỉ đọc với `pg_monitor` |

## 6. Các Biện Pháp Gia Cố Bảo Mật (Hardening)

Hệ thống đã triển khai toàn diện các tầng bảo vệ:
1. **Non-root Container**: Các container ứng dụng (`clinic_web`, `clinic_nginx`, `clinic_pgadmin`, `clinic_prometheus`, `clinic_grafana`, `clinic_loki`, `clinic_alert_sink`) chạy hoàn toàn bằng user không đặc quyền (non-root). Các container cần đặc quyền theo dõi hệ thống (`cadvisor`, `promtail`) được giới hạn quyền bằng `read_only`, `:ro` mounts và giải trình kiến trúc.
2. **Network Isolation**: Tách biệt 3 mạng Docker (`clinic_frontend`, `clinic_backend`, `clinic_monitoring`). Database `clinic_db` chỉ kết nối mạng `backend` với `internal: true`, không publish cổng và không thể truy cập từ `frontend`. Chỉ có Nginx publish cổng 80/443.
3. **Database Least Privilege & SCRAM-SHA-256**: Role ứng dụng `clinic_app` chỉ có quyền `SELECT, INSERT, UPDATE, DELETE` trên các bảng public; bị từ chối mọi thao tác `DROP TABLE` / `CREATE TABLE`. Sử dụng thuật toán băm mật khẩu `scram-sha-256`. Giới hạn `pg_hba.conf` chỉ chấp nhận kết nối từ subnet nội bộ `backend`.
4. **Container Security & Resource Limits**: Cấu hình `cap_drop: [ALL]`, `security_opt: [no-new-privileges:true]`, hệ thống tệp chỉ đọc `read_only: true` kèm `tmpfs` cho thư mục tạm `/tmp`, giới hạn CPU (`cpus`) và RAM (`mem_limit`).
5. **Nginx Hardening & Rate Limiting**: `server_tokens off;`, ẩn `Server` và `X-Powered-By` header, áp dụng rate limiting `limit_req_zone` bảo vệ endpoint `/login` ngăn chặn tấn công Brute Force / DoS.
6. **Tường lửa UFW**: Bật UFW chỉ cho phép các cổng bắt buộc: `22/tcp` (SSH), `80/tcp` (HTTP) và `443/tcp` (HTTPS). Mặc định chặn toàn bộ kết nối đến (`default deny incoming`).
7. **Bảo vệ Cookie & Phiên làm việc**: Cookie session cấu hình `HttpOnly=True`, `Secure=True`, `SameSite='Lax'`, thời gian hết hạn phiên làm việc hợp lý.

