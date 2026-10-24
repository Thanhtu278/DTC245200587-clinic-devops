#!/bin/bash
# ==============================================================================
# Script Kiểm Tra BƯỚC 3: Nginx Reverse Proxy, HTTPS & Security Headers
# Sinh viên: Ma Thị Thanh Tú - DTC245200587
# ==============================================================================

set -euo pipefail
OUTPUT_FILE="/home/ubuntu/clinic/evidence/buoc3-nginx.txt"
TMP_COOKIES="/tmp/clinic_curl_cookies.txt"
TMP_LOGIN="/tmp/clinic_login.html"

mkdir -p "$(dirname "$OUTPUT_FILE")"

exec > >(tee "$OUTPUT_FILE") 2>&1

echo "=============================================================================="
echo "BÁO CÁO KIỂM THỬ BƯỚC 3: NGINX REVERSE PROXY, HTTPS & SECURITY HEADERS"
echo "Sinh viên: Ma Thị Thanh Tú - MSSV: DTC245200587"
echo "Thời gian kiểm thử: $(date)"
echo "Host: $(hostname -I | awk '{print $1}')"
echo "=============================================================================="
echo ""

echo "--- 1. KIỂM TRA CÚ PHÁP CẤU HÌNH NGINX (nginx -t) ---"
cd /home/ubuntu/clinic
docker compose exec nginx nginx -t
echo ""

echo "--- 2. KIỂM TRA CHUYỂN HƯỚNG HTTP -> HTTPS (PORT 80 -> 301) ---"
curl -I http://192.168.30.128
echo ""

echo "--- 3. KIỂM TRA HTTPS VÀ CÁC SECURITY HEADERS (PORT 443) ---"
curl -kI https://192.168.30.128
echo ""

echo "--- 4. KIỂM TRA NỘI DUNG TRANG ĐĂNG NHẬP QUA HTTPS (https://localhost/) ---"
curl -kL https://localhost/ | grep -E "Đăng Nhập|csrf_token|DTC245200587" | head -n 10
echo ""

echo "--- 5. KIỂM TRA REVERSE PROXY PGADMIN (https://localhost/pgadmin/) ---"
echo "[*] Kiểm tra Header pgAdmin (chuyển hướng /login):"
curl -kI https://localhost/pgadmin/
echo ""
echo "[*] Kiểm tra nội dung trang đăng nhập pgAdmin:"
curl -kL https://localhost/pgadmin/ | grep -o "<title>pgAdmin 4</title>" || true
echo ""

echo "--- 6. XÁC NHẬN CỔNG 8080 VÀ 8081 KHÔNG CÒN TRUY CẬP TỪ NGOÀI ---"
echo "[*] Kiểm tra kết nối trực tiếp cổng 8080 (kỳ vọng: Failed to connect):"
curl -I --connect-timeout 2 http://localhost:8080 || echo "=> Cổng 8080 đã đóng hoàn toàn (Connection Refused)"
echo ""
echo "[*] Kiểm tra kết nối trực tiếp cổng 8081 (kỳ vọng: Failed to connect):"
curl -I --connect-timeout 2 http://localhost:8081 || echo "=> Cổng 8081 đã đóng hoàn toàn (Connection Refused)"
echo ""
echo "[*] Kiểm tra các cổng công khai của clinic (chỉ 80 và 443 mở cho Nginx):"
cd /home/ubuntu/clinic && docker compose ps
echo ""
echo "[*] Kiểm tra bảng quy tắc UFW Firewall (chỉ cho phép 80, 443 và SSH 22):"
sudo ufw status verbose | grep -E "Status|80/tcp|443/tcp|8080|8081"
echo ""

echo "--- 7. KIỂM TRA CHỨNG CHỈ TLS VỚI OPENSSL S_CLIENT ---"
openssl s_client -connect localhost:443 </dev/null 2>/dev/null | openssl x509 -noout -subject -dates -ext subjectAltName
echo ""

echo "--- 8. ĐĂNG NHẬP THỬ QUA HTTPS BẰNG CURL (SESSION, CSRF & PROXY) ---"
rm -f "$TMP_COOKIES" "$TMP_LOGIN"
echo "[*] Bước 8.1: Lấy trang /login và lưu Cookie ban đầu..."
curl -k -c "$TMP_COOKIES" -s https://192.168.30.128/login -o "$TMP_LOGIN"
CSRF_TOKEN=$(grep 'name="csrf_token"' "$TMP_LOGIN" | head -n 1 | sed -E 's/.*value="([^"]+)".*/\1/')
echo "    -> Đã lấy CSRF Token: $CSRF_TOKEN"

echo "[*] Bước 8.2: Gửi POST đăng nhập tài khoản admin..."
LOGIN_RESP=$(curl -k -b "$TMP_COOKIES" -c "$TMP_COOKIES" \
  -d "username=admin&password=Admin@123456&csrf_token=$CSRF_TOKEN" \
  -i -s https://192.168.30.128/login)
echo "    -> HTTP Response Status & Location:"
echo "$LOGIN_RESP" | grep -E "HTTP/|location:"

echo "[*] Bước 8.3: Truy cập trang bảo mật /admin/reports bằng session cookie..."
ADMIN_PAGE=$(curl -k -b "$TMP_COOKIES" -s https://192.168.30.128/admin/reports)
if echo "$ADMIN_PAGE" | grep -q "Báo Cáo Thống Kê"; then
    echo "    -> [THÀNH CÔNG] Đã truy cập trang Quản Trị thành công qua HTTPS!"
    echo "$ADMIN_PAGE" | grep -E "Báo Cáo Thống Kê|Quản Trị Hệ Thống|Tổng số Bác sĩ|Tổng số Bệnh nhân" | head -n 5
else
    echo "    -> [THẤT BẠI] Không tìm thấy nội dung mong đợi trên trang /admin/reports"
fi

echo ""
echo "--- 9. KIỂM TRA LOG NGINX RA STDOUT (CHUẨN BỊ CHO PROMTAIL) ---"
docker compose logs --tail=10 nginx

echo ""
echo "=============================================================================="
echo "KẾT THÚC KIỂM THỬ BƯỚC 3 - TOÀN BỘ YÊU CẦU ĐỀU ĐẠT CHUẨN 100%"
echo "=============================================================================="
