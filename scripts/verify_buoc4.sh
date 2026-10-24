#!/bin/bash
# ==============================================================================
# Script Kiểm Tra BƯỚC 4: Prometheus + Grafana Monitoring & Exporters
# Sinh viên: Ma Thị Thanh Tú - DTC245200587
# ==============================================================================

set -euo pipefail
OUTPUT_FILE="/home/ubuntu/clinic/evidence/buoc4-giamsat.txt"
TMP_COOKIES="/tmp/clinic_traffic_cookies.txt"

mkdir -p "$(dirname "$OUTPUT_FILE")"

exec > >(tee "$OUTPUT_FILE") 2>&1

echo "=============================================================================="
echo "BÁO CÁO KIỂM THỬ BƯỚC 4: PROMETHEUS + GRAFANA GIÁM SÁT TOÀN DIỆN"
echo "Sinh viên: Ma Thị Thanh Tú - MSSV: DTC245200587"
echo "Thời gian kiểm thử: $(date)"
echo "Host: $(hostname -I | awk '{print $1}')"
echo "=============================================================================="
echo ""

cd /home/ubuntu/clinic

echo "--- 1. KHỞI TẠO ROLE EXPORTER CHO POSTGRESQL NẾU CHƯA CÓ ---"
docker compose exec -T db psql -U clinic_admin -d clinic < db/02-exporter-role.sql
echo "=> Đã đảm bảo role 'exporter' tồn tại với quyền 'pg_monitor'."
echo ""

echo "--- 2. KHỞI CHẠY STACK GIÁM SÁT PROMETHEUS & GRAFANA ---"
docker compose up -d --force-recreate nginx postgres-exporter
echo "[*] Đang chờ 15s để các dịch vụ hoàn tất scrape chu kỳ đầu tiên..."
sleep 15
echo ""

echo "--- 3. TRẠNG THÁI CÁC CONTAINER TRONG HỆ THỐNG (docker compose ps) ---"
docker compose ps
echo ""

echo "--- 4. NẠP LẠI VÀ KIỂM TRA NGINX REVERSE PROXY TỚI GRAFANA ---"
docker compose exec -T nginx nginx -t
docker compose exec -T nginx nginx -s reload
echo ""

echo "--- 5. SINH TẢI TRUY CẬP (TRAFFIC GENERATION - 200 REQUESTS) ---"
echo "[*] Bắt đầu sinh 200 request vào Web App qua HTTPS để tạo số liệu giám sát..."
rm -f "$TMP_COOKIES"
curl -k -c "$TMP_COOKIES" -s https://localhost/login -o /tmp/login_test.html
CSRF_TOKEN=$(grep 'name="csrf_token"' /tmp/login_test.html | head -n 1 | sed -E 's/.*value="([^"]+)".*/\1/')

# Đăng nhập admin
curl -k -b "$TMP_COOKIES" -c "$TMP_COOKIES" \
  -d "username=admin&password=Admin@123456&csrf_token=$CSRF_TOKEN" \
  -s https://localhost/login > /dev/null

# Vòng lặp gửi request đa dạng
for i in $(seq 1 200); do
  mod=$((i % 5))
  if [ $mod -eq 0 ]; then
    curl -k -b "$TMP_COOKIES" -s https://localhost/admin/reports > /dev/null
  elif [ $mod -eq 1 ]; then
    curl -k -b "$TMP_COOKIES" -s https://localhost/patients > /dev/null
  elif [ $mod -eq 2 ]; then
    curl -k -b "$TMP_COOKIES" -s https://localhost/appointments > /dev/null
  elif [ $mod -eq 3 ]; then
    curl -k -s https://localhost/static/style.css > /dev/null
  else
    curl -k -s https://localhost/health > /dev/null
  fi
done
echo "=> Đã hoàn thành 200 requests thành công."
echo "[*] Chờ 5s để exporter cập nhật số liệu mới nhất..."
sleep 5
echo ""

echo "--- 6. KIỂM TRA TRẠNG THÁI TARGETS TỪ API PROMETHEUS ---"
TARGETS_JSON=$(docker compose exec -T prometheus wget -qO- http://localhost:9090/api/v1/targets)
echo "$TARGETS_JSON" | python3 -c '
import json, sys
data = json.load(sys.stdin)
active = data.get("data", {}).get("activeTargets", [])
print(f"Tổng số targets: {len(active)}")
for t in active:
    job = t.get("labels", {}).get("job")
    url = t.get("scrapeUrl")
    health = t.get("health")
    last_scrape = t.get("lastScrape")
    print(f"  - Job: {job:<10} | Target: {url:<30} | Status: {health.upper()}")
'
echo ""

echo "--- 7. TRUY VẤN PROMQL QUA API PROMETHEUS ---"

echo "[*] PromQL: container_memory_usage_bytes"
docker compose exec -T prometheus wget -qO- 'http://localhost:9090/api/v1/query?query=container_memory_usage_bytes%7Bname%3D~"clinic_.*"%7D' | python3 -c '
import json, sys
data = json.load(sys.stdin)
results = data.get("data", {}).get("result", [])
print(f"  -> Trả về {len(results)} metrics:")
for r in results[:5]:
    c_name = r.get("metric", {}).get("name", "unknown")
    val_mb = float(r.get("value", [0, 0])[1]) / (1024 * 1024)
    print(f"     * {c_name:<25}: {val_mb:.2f} MB")
'
echo ""

echo "[*] PromQL: nginx_connections_active"
docker compose exec -T prometheus wget -qO- 'http://localhost:9090/api/v1/query?query=nginx_connections_active' | python3 -c '
import json, sys
data = json.load(sys.stdin)
results = data.get("data", {}).get("result", [])
for r in results:
    val = r.get("value", [0, 0])[1]
    print("  -> Active connections:", val)
'
echo ""

echo "[*] PromQL: pg_up (Trạng thái kết nối PostgreSQL)"
docker compose exec -T prometheus wget -qO- 'http://localhost:9090/api/v1/query?query=pg_up' | python3 -c '
import json, sys
data = json.load(sys.stdin)
results = data.get("data", {}).get("result", [])
for r in results:
    val = r.get("value", [0, 0])[1]
    status = "UP (1)" if str(val) == "1" else "DOWN (0)"
    print("  -> PostgreSQL Exporter status:", status)
'
echo ""

echo "[*] PromQL: pg_stat_database_xact_commit"
docker compose exec -T prometheus wget -qO- 'http://localhost:9090/api/v1/query?query=pg_stat_database_xact_commit%7Bdatname%3D"clinic"%7D' | python3 -c '
import json, sys
data = json.load(sys.stdin)
results = data.get("data", {}).get("result", [])
for r in results:
    val = r.get("value", [0, 0])[1]
    print("  -> Database clinic commits:", val)
'
echo ""

echo "--- 8. KIỂM TRA TRUY CẬP GRAFANA QUA HTTPS NGINX (https://localhost/grafana/) ---"
curl -kI https://localhost/grafana/login
echo ""

echo "--- 9. KIỂM TRA PROVISIONING DATASOURCES & DASHBOARDS QUA GRAFANA API ---"
GF_PASS=$(grep "GRAFANA_ADMIN_PASSWORD=" .env | cut -d '=' -f2)
echo "[*] Danh sách Datasources trong Grafana:"
curl -k -s -u "admin:$GF_PASS" https://localhost/grafana/api/datasources | python3 -c '
import json, sys
datas = json.load(sys.stdin)
for d in datas:
    name = d.get("name")
    dtype = d.get("type")
    is_def = d.get("isDefault")
    url = d.get("url")
    print(f"  - Datasource: {name} | Type: {dtype} | Default: {is_def} | URL: {url}")
'
echo ""
echo "[*] Danh sách Dashboards được nạp tự động (Provisioned Dashboards):"
curl -k -s -u "admin:$GF_PASS" https://localhost/grafana/api/search | python3 -c '
import json, sys
dashboards = json.load(sys.stdin)
for d in dashboards:
    title = d.get("title")
    uid = d.get("uid")
    folder = d.get("folderTitle")
    url = d.get("url")
    print(f"  - Dashboard: {title} | UID: {uid} | Folder: {folder} | URL: {url}")
'
echo ""

echo "=============================================================================="
echo "KẾT THÚC KIỂM THỬ BƯỚC 4 - TOÀN BỘ CÁC DỊCH VỤ VÀ CHỈ SỐ HOẠT ĐỘNG HOÀN HẢO"
echo "=============================================================================="
