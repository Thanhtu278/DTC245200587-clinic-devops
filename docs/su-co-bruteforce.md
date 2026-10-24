# BÁO CÁO ĐIỀU TRA SỰ CỐ AN TOÀN THÔNG TIN: TẤN CÔNG DÒ MẬT KHẨU (BRUTE FORCE) VÀO HỆ THỐNG PHÒNG KHÁM

- **Hệ thống mục tiêu**: Hệ thống Quản lý Phòng khám / Bệnh viện (Clinic Management System)
- **Sinh viên thực hiện**: Ma Thị Thanh Tú - MSSV: DTC245200587
- **Mã sự cố**: SEC-INC-2026-001
- **Mức độ nghiêm trọng**: **CRITICAL** (Đe dọa lộ lọt hồ sơ y tế bệnh nhân & chiếm đoạt quyền quản trị)
- **Thời gian phát hiện**: Tháng 10/2026

---

## 1. MÔ TẢ SỰ CỐ
Hệ thống Quản lý Phòng khám lưu trữ dữ liệu y tế nhạy cảm bao gồm thông tin định danh cá nhân bệnh nhân (PII), lịch sử khám bệnh, chẩn đoán bệnh lý và đơn thuốc. Trang đăng nhập web (`https://192.168.30.128/login`) là cửa ngõ bảo vệ chính của hệ thống.

Vào thời điểm ghi nhận, hệ thống giám sát phát hiện một chuỗi bất thường gồm **20 yêu cầu đăng nhập liên tiếp trong thời gian ngắn (~15 giây)** nhắm vào tài khoản quản trị tối cao (`admin`). Kẻ tấn công sử dụng danh sách mật khẩu phổ biến (dictionary attack/wordlist) nhằm dò tìm mật khẩu quản trị viên.

---

## 2. CƠ CHẾ PHÁT HIỆN SỰ CỐ (DETECTION & ALERTING)
Hệ thống sử dụng hạ tầng giám sát tập trung **Loki + Promtail + Grafana Alerting**:
1. **Thu thập Log**: Container `clinic_web` ghi nhận mọi lần xác thực thất bại ra STDERR với định dạng chuẩn:
   ```text
   LOGIN_FAILED ip=<IP> user=<username> reason=wrong_password
   ```
   Promtail tự động thu thập log từ Docker socket và đẩy về Loki dưới nhãn `job="webapp"`.
2. **Quy tắc Cảnh báo (Alert Rule)**:
   - Tên quy tắc: `Clinic - Brute force login`
   - Nhóm: `Clinic Security Alerts`
   - Biểu thức LogQL:
     ```logql
     sum(count_over_time({job="webapp"} |= "LOGIN_FAILED" [1m])) > 5
     ```
   - Điều kiện: Số lần đăng nhập sai vượt quá 5 lần trong 1 phút.
   - Thời gian kích hoạt (`for`): `0s` (kích hoạt ngay lập tức khi vượt ngưỡng).
3. **Phát tín hiệu Cảnh báo**:
   - Grafana Alerting chuyển trạng thái từ **Normal** sang **Firing**.
   - Gửi webhook thông báo ngay lập tức tới dịch vụ tiếp nhận cảnh báo `alert-sink` (`http://alert-sink:5001/webhook`).
   - Log của `alert-sink` ghi nhận sự kiện cảnh báo `CRITICAL` và lưu vào `/var/log/alerts.log`.

---

## 3. TRUY VẾT VÀ PHÂN TÍCH SỰ CỐ (INVESTIGATION & LOGQL TRACE)

### 3.1 Truy vấn LogQL phát hiện các lần đăng nhập sai
Sử dụng câu truy vấn LogQL:
```logql
{job="webapp"} |= "LOGIN_FAILED"
```
**Kết quả phân tích**:
- **Tài khoản bị nhắm mục tiêu**: `user=admin`
- **Địa chỉ IP nguồn tấn công**: `192.168.30.128` (hoặc IP từ mạng LAN / client)
- **Tổng số lần thử sai**: 20 lần thử liên tiếp.
- **Lý do thất bại**: `reason=wrong_password`.

### 3.2 Tần suất tấn công theo thời gian
Sử dụng câu truy vấn LogQL:
```logql
sum(count_over_time({job="webapp"} |= "LOGIN_FAILED" [1m]))
```
Biểu đồ trên Grafana Dashboard `Clinic - Logs` ghi nhận đột biến từ 0 vọt lên 20 lần/phút trong khoảng thời gian diễn ra brute force.

### 3.3 Đối chiếu với Nhật ký Truy cập Nginx (Cross-Correlation)
Truy vấn Nginx access log qua LogQL:
```logql
{job="nginx"} |= "POST /login"
```
**Kết quả đối chiếu**:
- Ghi nhận 20 request `POST /login HTTP/2.0` với mã phản hồi `302 Moved Temporarily` (chuyển hướng trở lại `/login` do sai thông tin đăng nhập).
- Thời gian giữa các request xấp xỉ 0.5 - 0.7 giây, chứng minh đây là công cụ tự động (script/tool) chứ không phải thao tác người dùng bình thường.

### 3.4 Kiểm tra dấu hiệu tài khoản bị chiếm đoạt (Post-Incident Verification)
Truy vấn LogQL kiểm tra xem có lần đăng nhập thành công nào ngay sau chuỗi brute force không:
```logql
{job="webapp"} |= "LOGIN_SUCCESS"
```
**Kết luận**: Toàn bộ 20 lần thử đều thất bại, không có sự kiện `LOGIN_SUCCESS` trái phép nào được ghi nhận sau đó từ IP của kẻ tấn công. Tài khoản `admin` vẫn được bảo vệ nguyên vẹn.

---

## 4. BIỆN PHÁP XỬ LÝ VÀ KHẮC PHỤC ĐỀ XUẤT (REMEDIATION & HARDENING)

1. **Giới hạn tần suất trên Reverse Proxy (Nginx Rate Limiting)**:
   - Cấu hình vùng nhớ `limit_req_zone` trong `nginx.conf`:
     ```nginx
     limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
     ```
   - Áp dụng vào endpoint đăng nhập:
     ```nginx
     location = /login {
         limit_req zone=login_limit burst=3 nodelay;
         proxy_pass http://web:8000;
     }
     ```
   - Khi vượt quá 5 request/phút, Nginx lập tức chặn và trả về HTTP `429 Too Many Requests` hoặc `503 Service Unavailable`, triệt tiêu hoàn toàn khả năng dò mật khẩu tự động.

2. **Chính sách khóa tài khoản tạm thời (Account Lockout Policy)**:
   - Khóa tạm thời tài khoản trong 15 - 30 phút nếu nhập sai quá 5 lần liên tiếp.
   - Gửi email cảnh báo tới chủ sở hữu tài khoản và quản trị viên an ninh.

3. **Bắt buộc Xác thực Hai Yếu tố (2FA / MFA)**:
   - Triển khai TOTP (Google Authenticator / Microsoft Authenticator) cho toàn bộ bác sĩ, lễ tân và quản trị viên. Dù kẻ tấn công đoán đúng mật khẩu cũng không thể đăng nhập nếu không có OTP.

4. **Triển khai Web Application Firewall (WAF) & Fail2Ban**:
   - Sử dụng Fail2Ban quét log của Promtail / Nginx để tự động thêm IP tấn công vào bảng chặn iptables / UFW trong 24 giờ.

---

## 5. BÀI HỌC KINH NGHIỆM
1. **Dữ liệu y tế là mục tiêu giá trị cao**: Bệnh án và thông tin cá nhân bệnh nhân được bảo vệ theo Luật Khám bệnh, chữa bệnh và Nghị định 13/2023/NĐ-CP về Bảo vệ dữ liệu cá nhân. Một sự cố lộ lọt có thể dẫn đến hậu quả pháp lý nghiêm trọng và mất uy tín cơ sở y tế.
2. **Tầm quan trọng của giám sát thời gian thực**: Nhờ hạ tầng Loki + Promtail và Grafana Alerting, sự cố dò mật khẩu được phát hiện ngay trong vòng vài giây, giúp đội ngũ vận hành phản ứng kịp thời trước khi tài khoản bị xâm nhập.
3. **Phòng thủ theo chiều sâu (Defense in Depth)**: Cần kết hợp đồng thời nhiều lớp phòng thủ: Rate limit tại Nginx, Captcha/CSRF tại Web App, mã hóa mật khẩu PBKDF2 tại Database, và hệ thống cảnh báo tự động tới Alert-sink.
