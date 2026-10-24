#!/bin/bash
# ==============================================================================
# Script Kiểm Tra BƯỚC 5: Loki, Promtail, LogQL & Kịch Bản Sự Cố Brute Force
# Sinh viên: Ma Thị Thanh Tú - DTC245200587
# ==============================================================================

set -euo pipefail
CDIR="/home/ubuntu/clinic"
EVID_DIR="$CDIR/evidence"
LOGQL_EVID="$EVID_DIR/buoc5-logql.txt"
SUCO_EVID="$EVID_DIR/buoc5-sucodo.txt"

mkdir -p "$EVID_DIR"
cd "$CDIR"

echo "=============================================================================="
echo "BƯỚC 5: KHỞI TẠO VÀ KIỂM TRA HẠ TẦNG LOG & KỊCH BẢN SỰ CỐ AN TOÀN THÔNG TIN"
echo "Sinh viên: Ma Thị Thanh Tú - MSSV: DTC245200587"
echo "Thời gian: $(date)"
echo "=============================================================================="
echo ""

echo "--- 1. KHỞI CHẠY LOKI, PROMTAIL & ALERT-SINK ---"
docker compose up -d --build alert-sink
docker compose up -d loki promtail
docker compose up -d --force-recreate grafana

echo "[*] Đang chờ 15s để Loki và Promtail khởi động và kết nối..."
sleep 15

# Kiểm tra Loki /ready
echo "[*] Kiểm tra trạng thái Loki (/ready):"
LOKI_STATUS=$(docker compose exec -T loki wget -qO- http://localhost:3100/ready || true)
echo "    -> Loki Status: $LOKI_STATUS"

# Kiểm tra tất cả container
docker compose ps

echo ""
echo "=============================================================================="
echo "PHẦN 1: THỰC THI KỊCH BẢN SỰ CỐ TẤN CÔNG BRUTE FORCE & ALERT"
echo "=============================================================================="

exec 3>&1 4>&2
exec > >(tee "$SUCO_EVID") 2>&1

GF_PASS=$(grep "GRAFANA_ADMIN_PASSWORD=" .env | cut -d '=' -f2)

echo "[*] GIAI ĐOẠN A: TRƯỚC TẤN CÔNG (Thời gian: $(date +'%T'))"
echo "    -> Kiểm tra trạng thái Alert Rule trong Grafana Alerting API:"
curl -k -s -u "admin:$GF_PASS" https://localhost/grafana/api/prometheus/grafana/api/v1/rules | python3 -c '
import json, sys
data = json.load(sys.stdin)
groups = data.get("data", {}).get("groups", [])
for g in groups:
    for r in g.get("rules", []):
        print(f"       * Alert Rule: {r.get(\"name\")} | State: {r.get(\"state\")} | Health: {r.get(\"health\")}")
' || echo "       * Chưa có cảnh báo nào kích hoạt (Hệ thống an toàn)"
echo ""

echo "[*] GIAI ĐOẠN B: TIẾN HÀNH TẤN CÔNG DÒ MẬT KHẨU (BRUTE FORCE)"
chmod +x scripts/simulate_bruteforce.sh
./scripts/simulate_bruteforce.sh
echo ""

echo "[*] GIAI ĐOẠN C: KIỂM TRA PHÁT HIỆN LOG & ALERT FIRING"
echo "    -> Đang chờ 15s để Promtail đẩy log và Grafana Alerting đánh giá chu kỳ..."
sleep 15

echo "    -> Kiểm tra trạng thái Alert Rule sau tấn công:"
curl -k -s -u "admin:$GF_PASS" https://localhost/grafana/api/prometheus/grafana/api/v1/rules | python3 -c '
import json, sys
data = json.load(sys.stdin)
groups = data.get("data", {}).get("groups", [])
for g in groups:
    for r in g.get("rules", []):
        print(f"       * Alert Rule: {r.get(\"name\")} | State: {r.get(\"state\").upper()} | Active Alerts: {len(r.get(\"alerts\", []))}")
'

echo ""
echo "    -> Kiểm tra log nhận được tại container alert-sink (Webhook Consumer):"
docker compose logs --tail=25 alert-sink
echo ""

echo "[*] GIAI ĐOẠN D: TRUY VẾT SỰ CỐ BẰNG LOGQL (INCIDENT INVESTIGATION)"
NOW_S=$(date +%s)
START_S=$((NOW_S - 600))
START_NS="${START_S}000000000"
END_NS="${NOW_S}000000000"

echo "    -> 1. Trích xuất các bản ghi LOGIN_FAILED từ webapp:"
docker compose exec -T loki wget -qO- "http://localhost:3100/loki/api/v1/query_range?query=%7Bjob%3D%22webapp%22%7D%20%7C%3D%20%22LOGIN_FAILED%22&start=${START_NS}&end=${END_NS}&limit=25" | python3 -c '
import json, sys, re
data = json.load(sys.stdin)
streams = data.get("data", {}).get("result", [])
total = 0
ips = set()
users = set()
timestamps = []
for s in streams:
    for val in s.get("values", []):
        total += 1
        ts_ns, line = val[0], val[1]
        timestamps.append(int(ts_ns))
        m_ip = re.search(r"ip=([^\s]+)", line)
        m_user = re.search(r"user=([^\s]+)", line)
        if m_ip: ips.add(m_ip.group(1))
        if m_user: users.add(m_user.group(1))

print(f"       [+] Tổng số sự kiện LOGIN_FAILED thu thập: {total}")
print(f"       [+] Địa chỉ IP nguồn tấn công: {list(ips)}")
print(f"       [+] Tài khoản mục tiêu: {list(users)}")
if timestamps:
    t_min = min(timestamps) / 1e9
    t_max = max(timestamps) / 1e9
    import datetime
    dt_start = datetime.datetime.fromtimestamp(t_min).strftime("%Y-%m-%d %H:%M:%S")
    dt_end = datetime.datetime.fromtimestamp(t_max).strftime("%Y-%m-%d %H:%M:%S")
    print(f"       [+] Thời điểm bắt đầu: {dt_start}")
    print(f"       [+] Thời điểm kết thúc: {dt_end}")
'

echo ""
echo "    -> 2. Đối chiếu nhật ký Nginx Access Log từ cùng IP nguồn:"
docker compose exec -T loki wget -qO- "http://localhost:3100/loki/api/v1/query_range?query=%7Bjob%3D%22nginx%22%7D%20%7C%3D%20%22POST%20%2Flogin%22&start=${START_NS}&end=${END_NS}&limit=10" | python3 -c '
import json, sys
data = json.load(sys.stdin)
streams = data.get("data", {}).get("result", [])
count = 0
for s in streams:
    for val in s.get("values", []):
        count += 1
        print(f"       * Nginx Request {count}: {val[1].strip()[:90]}...")
        if count >= 5: break
print(f"       [+] Tổng số request POST /login ghi nhận trên Nginx: {count}")
'

echo ""
echo "    -> 3. Kiểm tra dấu hiệu chiếm đoạt tài khoản (LOGIN_SUCCESS sau tấn công):"
docker compose exec -T loki wget -qO- "http://localhost:3100/loki/api/v1/query_range?query=%7Bjob%3D%22webapp%22%7D%20%7C%3D%20%22LOGIN_SUCCESS%22&start=${START_NS}&end=${END_NS}&limit=10" | python3 -c '
import json, sys
data = json.load(sys.stdin)
streams = data.get("data", {}).get("result", [])
count = sum(len(s.get("values", [])) for s in streams)
if count == 0:
    print("       [✓] AN TOÀN: Không phát hiện sự kiện LOGIN_SUCCESS nào từ IP tấn công.")
    print("       [✓] Kẻ tấn công KHÔNG chiếm được tài khoản quản trị.")
else:
    print(f"       [!] CẢNH BÁO: Phát hiện {count} lần đăng nhập thành công sau chuỗi tấn công.")
'

echo ""
echo "=============================================================================="
echo "KẾT THÚC KỊCH BẢN SỰ CỐ - BẰNG CHỨNG LƯU TẠI: $SUCO_EVID"
echo "=============================================================================="

exec 1>&3 2>&4

echo ""
echo "=============================================================================="
echo "PHẦN 2: THỰC THI 5 CÂU TRUY VẤN LOGQL VÀ LƯU VÀO $LOGQL_EVID"
echo "=============================================================================="

exec > >(tee "$LOGQL_EVID") 2>&1

echo "=============================================================================="
echo "BÁO CÁO KẾT QUẢ TRUY VẤN LOGQL - HỆ THỐNG PHÒNG KHÁM DTC245200587"
echo "Thời gian truy vấn: $(date)"
echo "Loki Server: http://loki:3100"
echo "=============================================================================="
echo ""

# Query 1
echo "--- Q1: LỖI HTTP CỦA NGINX ({job=\"nginx\"} |~ \" (4[0-9]{2}|5[0-9]{2}) \") ---"
echo "Câu lệnh LogQL: {job=\"nginx\"} |~ \" (4[0-9]{2}|5[0-9]{2}) \""
docker compose exec -T loki wget -qO- 'http://localhost:3100/loki/api/v1/query_range?query=%7Bjob%3D%22nginx%22%7D%20%7C~%20%22%20(4%5B0-9%5D%7B2%7D%7C5%5B0-9%5D%7B2%7D)%20%22&limit=5' | python3 -c '
import json, sys
data = json.load(sys.stdin)
for s in data.get("data", {}).get("result", []):
    for val in s.get("values", [])[:3]:
        print("  -> Log line:", val[1].strip()[:100])
' || echo "  (Chưa có mã lỗi 4xx/5xx trên Nginx)"
echo ""

# Query 2
echo "--- Q2: LỖI HOẶC NGOẠI LỆ ỨNG DỤNG WEB ({job=\"webapp\"} |~ \"(?i)(error|exception|failed)\") ---"
echo "Câu lệnh LogQL: {job=\"webapp\"} |~ \"(?i)(error|exception|failed)\""
docker compose exec -T loki wget -qO- 'http://localhost:3100/loki/api/v1/query_range?query=%7Bjob%3D%22webapp%22%7D%20%7C~%20%22(%3Fi)(error%7Cexception%7Cfailed)%22&limit=5' | python3 -c '
import json, sys
data = json.load(sys.stdin)
for s in data.get("data", {}).get("result", []):
    for val in s.get("values", [])[:5]:
        print("  -> Log line:", val[1].strip()[:100])
'
echo ""

# Query 3
echo "--- Q3: SỰ KIỆN ĐĂNG NHẬP THẤT BẠI ({job=\"webapp\"} |= \"LOGIN_FAILED\") ---"
echo "Câu lệnh LogQL: {job=\"webapp\"} |= \"LOGIN_FAILED\""
docker compose exec -T loki wget -qO- 'http://localhost:3100/loki/api/v1/query_range?query=%7Bjob%3D%22webapp%22%7D%20%7C%3D%20%22LOGIN_FAILED%22&limit=5' | python3 -c '
import json, sys
data = json.load(sys.stdin)
for s in data.get("data", {}).get("result", []):
    for val in s.get("values", [])[:5]:
        print("  -> Log line:", val[1].strip())
'
echo ""

# Query 4
echo "--- Q4: ĐẾM SỐ LẦN ĐĂNG NHẬP THẤT BẠI THEO PHÚT (sum(count_over_time({job=\"webapp\"} |= \"LOGIN_FAILED\" [1m]))) ---"
echo "Câu lệnh LogQL: sum(count_over_time({job=\"webapp\"} |= \"LOGIN_FAILED\" [1m]))"
docker compose exec -T loki wget -qO- 'http://localhost:3100/loki/api/v1/query?query=sum(count_over_time(%7Bjob%3D%22webapp%22%7D%20%7C%3D%20%22LOGIN_FAILED%22%20%5B1m%5D))' | python3 -c '
import json, sys
data = json.load(sys.stdin)
for r in data.get("data", {}).get("result", []):
    print("  -> Giá trị tính toán (count / 1m):", r.get("value", [0, 0])[1])
'
echo ""

# Query 5
echo "--- Q5: LOG HOẠT ĐỘNG VÀ CẢNH BÁO DATABASE ({job=\"postgres\"} |~ \"(?i)(error|fatal|starting|ready)\") ---"
echo "Câu lệnh LogQL: {job=\"postgres\"} |~ \"(?i)(error|fatal|starting|ready)\""
docker compose exec -T loki wget -qO- 'http://localhost:3100/loki/api/v1/query_range?query=%7Bjob%3D%22postgres%22%7D%20%7C~%20%22(%3Fi)(error%7Cfatal%7Cstarting%7Cready)%22&limit=5' | python3 -c '
import json, sys
data = json.load(sys.stdin)
for s in data.get("data", {}).get("result", []):
    for val in s.get("values", [])[:3]:
        print("  -> Log line:", val[1].strip()[:100])
'
echo ""

echo "=============================================================================="
echo "HOÀN THÀNH TOÀN BỘ 5 CÂU TRUY VẤN LOGQL - KẾT QUẢ ĐÃ LƯU TẠI $LOGQL_EVID"
echo "=============================================================================="
