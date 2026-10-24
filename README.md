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
- **Database**: PostgreSQL 16 (Tách biệt quyền admin và role ứng dụng `clinic_app`, index tối ưu)
- **Database Management**: pgAdmin 4 (Reverse proxy qua đường dẫn con `/pgadmin/`)
- **Reverse Proxy & SSL**: Nginx 1.27 Alpine (HTTPS tự ký, TLS 1.2/1.3, Security Headers: HSTS, CSP, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy)
- **Monitoring**: Prometheus + Grafana (Giám sát Container, Nginx stub_status, Web App, PostgreSQL)
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
│   └── init.sql
├── pgadmin/
│   └── servers.json
├── nginx/
│   ├── gen-cert.sh
│   ├── nginx.conf
│   └── certs/
│       └── server.crt
├── prometheus/
├── grafana/
│   └── provisioning/
├── loki/
├── promtail/
├── alert-sink/
├── scripts/
├── evidence/
└── docs/
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

### Bước 4: Kiểm tra trạng thái các container
```bash
docker compose ps
docker compose exec nginx nginx -t
```

## 5. Truy Cập Hệ Thống
- **Ứng dụng Phòng khám (Web App)**: `https://192.168.30.128` hoặc `https://localhost`
  *(Tự động chuyển hướng từ cổng 80 HTTP sang HTTPS)*
- **Quản trị Database (pgAdmin 4)**: `https://192.168.30.128/pgadmin/` hoặc `https://localhost/pgadmin/`
- **Tài khoản mặc định**:
  - `admin` / `Admin@123456` (Quản trị viên)
  - `letan01` / `Letan@123456` (Lễ tân)
  - `bs.nguyen` / `Doctor@123456` (Bác sĩ)
  - pgAdmin: `dtc245200587@ictu.edu.vn`
