#!/bin/bash
# ==============================================================================
# Script: nginx/gen-cert.sh
# Mục đích: Tự động sinh chứng chỉ SSL/TLS tự ký cho Nginx Reverse Proxy
# Sinh viên: Ma Thị Thanh Tú - DTC245200587
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERTS_DIR="$SCRIPT_DIR/certs"

mkdir -p "$CERTS_DIR"

echo "[*] Đang khởi tạo chứng chỉ SSL/TLS tự ký cho Nginx..."
echo "    - Domain / IP: 192.168.30.128, localhost"
echo "    - Thuật toán: RSA 2048-bit"
echo "    - Thời hạn: 365 ngày"

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$CERTS_DIR/server.key" \
  -out "$CERTS_DIR/server.crt" \
  -subj "/C=VN/ST=ThaiNguyen/O=ICTU/OU=DTC245200587/CN=192.168.30.128" \
  -addext "subjectAltName = IP:192.168.30.128,DNS:localhost"

chmod 644 "$CERTS_DIR/server.key"
chmod 644 "$CERTS_DIR/server.crt"

echo "[✓] Đã tạo chứng chỉ thành công tại: $CERTS_DIR"
echo "    - Private Key: $CERTS_DIR/server.key"
echo "    - Certificate: $CERTS_DIR/server.crt"
echo ""
echo "=== THÔNG TIN CHỨNG CHỈ ==="
openssl x509 -in "$CERTS_DIR/server.crt" -noout -subject -dates -ext subjectAltName
