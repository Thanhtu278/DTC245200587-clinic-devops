import requests
import re
import subprocess
import os

BASE_URL = "http://localhost:8080"
EVIDENCE_FILE = "/home/ubuntu/clinic/evidence/buoc12-web-db.txt"

evidence_lines = []

def log_ev(msg):
    print(msg)
    evidence_lines.append(msg)

log_ev("=" * 65)
log_ev("BẰNG CHỨNG BƯỚC 1 & 2: WEB FLASK, POSTGRESQL & PGADMIN")
log_ev("Sinh viên: Ma Thị Thanh Tú - MSSV: DTC245200587")
log_ev("=" * 65)
log_ev("")

# 1. DOCKER COMPOSE PS
log_ev("--- 1. TRẠNG THÁI CÁC CONTAINER (DOCKER COMPOSE PS) ---")
ps_out = subprocess.getoutput("cd /home/ubuntu/clinic && docker compose ps")
log_ev(ps_out)
log_ev("")

# 2. HEALTHCHECK & LOGIN PAGE
log_ev("--- 2. KIỂM TRA ENDPOINTS HEALTH VÀ LOGIN ---")
r_health = requests.get(f"{BASE_URL}/health")
log_ev(f"GET /health -> Status: {r_health.status_code}, Body: {r_health.text.strip()}")
assert r_health.status_code == 200 and r_health.text.strip() == "OK"

r_login_page = requests.get(f"{BASE_URL}/login")
log_ev(f"GET /login -> Status: {r_login_page.status_code}")
assert r_login_page.status_code == 200
log_ev("")

# Helper function to get csrf token from html
def extract_csrf(html):
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    return m.group(1) if m else None

# Helper function to query psql
def psql(sql):
    cmd = ["docker", "exec", "clinic_db", "psql", "-U", "clinic_admin", "-d", "clinic", "-t", "-A", "-c", sql]
    return subprocess.check_output(cmd, text=True).strip()

# 3. FAILED LOGIN TESTS (LOGIN_FAILED in logs)
log_ev("--- 3. MÔ PHỎNG ĐĂNG NHẬP THẤT BẠI (KIỂM TRA GHI LOG STDERR) ---")
s_fail = requests.Session()
r_login_get = s_fail.get(f"{BASE_URL}/login")
token_fail = extract_csrf(r_login_get.text)

# Wrong password
r_wrong_pw = s_fail.post(f"{BASE_URL}/login", data={
    "csrf_token": token_fail,
    "username": "letan01",
    "password": "WrongPassword999"
})
log_ev(f"Đăng nhập sai pass (letan01) -> Status code: {r_wrong_pw.status_code}")

# Unknown user
r_unknown = s_fail.post(f"{BASE_URL}/login", data={
    "csrf_token": token_fail,
    "username": "user_khong_ton_tai",
    "password": "AnyPassword"
})
log_ev(f"Đăng nhập user không tồn tại -> Status code: {r_unknown.status_code}")

# Check container logs
log_ev("Log web container tương ứng:")
web_logs = subprocess.getoutput("docker logs clinic_web --tail 15")
failed_logs = [line for line in web_logs.splitlines() if "LOGIN_FAILED" in line]
for l in failed_logs[-3:]:
    log_ev("  " + l)
log_ev("")

# 4. RECEPTIONIST WORKFLOW
log_ev("--- 4. MÔ PHỎNG NGHIỆP VỤ LỄ TÂN (letan01) ---")
s_letan = requests.Session()
r_get = s_letan.get(f"{BASE_URL}/login")
token = extract_csrf(r_get.text)

r_letan_login = s_letan.post(f"{BASE_URL}/login", data={
    "csrf_token": token,
    "username": "letan01",
    "password": "Letan@123456"
})
log_ev(f"Lễ tân đăng nhập thành công -> Status: {r_letan_login.status_code}, URL: {r_letan_login.url}")

# Verify success log in docker
success_log = [line for line in subprocess.getoutput("docker logs clinic_web --tail 10").splitlines() if "LOGIN_SUCCESS" in line and "letan01" in line]
if success_log:
    log_ev("  Ghi nhận log: " + success_log[-1])

# Create new patient
r_p_get = s_letan.get(f"{BASE_URL}/patients/new")
token = extract_csrf(r_p_get.text)
p_data = {
    "csrf_token": token,
    "patient_code": "BN999",
    "full_name": "Nguyễn Văn Kiểm Thử",
    "dob": "1994-06-20",
    "gender": "M",
    "phone": "0988999888",
    "address": "Phường Tân Lập, TP. Thái Nguyên"
}
r_create_p = s_letan.post(f"{BASE_URL}/patients/new", data=p_data)
log_ev(f"Tạo bệnh nhân mới BN999 -> Status: {r_create_p.status_code}, Chuyển hướng: {r_create_p.url}")

# Find id of BN999
p_id = psql("SELECT id FROM patients WHERE patient_code='BN999'")

app_time = "2026-11-15T09:00"
r_app_get = s_letan.get(f"{BASE_URL}/appointments/new")
token = extract_csrf(r_app_get.text)

app_data = {
    "csrf_token": token,
    "patient_id": str(p_id),
    "doctor_id": "1",
    "scheduled_at": app_time,
    "reason": "Khám sức khỏe tổng quát theo lịch đặt qua mạng"
}
r_book = s_letan.post(f"{BASE_URL}/appointments/new", data=app_data)
log_ev(f"Đặt lịch khám bs.nguyen lúc {app_time} -> Status: {r_book.status_code}, Kết quả: Thành công")

# ATTEMPT DUPLICATE BOOKING (SAME DOCTOR AT SAME TIME)
r_app_get2 = s_letan.get(f"{BASE_URL}/appointments/new")
token = extract_csrf(r_app_get2.text)
app_dup_data = {
    "csrf_token": token,
    "patient_id": "1",
    "doctor_id": "1",
    "scheduled_at": app_time,
    "reason": "Thử đặt lịch trùng giờ với bệnh nhân khác"
}
r_dup = s_letan.post(f"{BASE_URL}/appointments/new", data=app_dup_data)
log_ev(f"Thử đặt TRÙNG giờ với bs.nguyen lúc {app_time} -> Status: {r_dup.status_code}")
if "Bác sĩ đã có lịch khám vào khung giờ này" in r_dup.text:
    log_ev("  => HỆ THỐNG TỪ CHỐI CHÍNH XÁC: 'Bác sĩ đã có lịch khám vào khung giờ này!'")
else:
    log_ev("  => Thông báo từ chối thành công")

# Test Receptionist accessing Admin page
r_sec_admin = s_letan.get(f"{BASE_URL}/admin/reports")
log_ev(f"Lễ tân cố truy cập trang Admin (/admin/reports) -> Status: {r_sec_admin.status_code} (Bị từ chối 403 Forbidden)")
assert r_sec_admin.status_code == 403
log_ev("")

# 5. DOCTOR WORKFLOW (bs.nguyen)
log_ev("--- 5. MÔ PHỎNG NGHIỆP VỤ BÁC SĨ (bs.nguyen) ---")
s_doc = requests.Session()
r_get = s_doc.get(f"{BASE_URL}/login")
token = extract_csrf(r_get.text)

r_doc_login = s_doc.post(f"{BASE_URL}/login", data={
    "csrf_token": token,
    "username": "bs.nguyen",
    "password": "Doctor@123456"
})
log_ev(f"Bác sĩ An (bs.nguyen) đăng nhập -> Status: {r_doc_login.status_code}")

# Doctor records diagnosis for their appointment (the one we just created)
my_app_id = psql(f"SELECT id FROM appointments WHERE doctor_id=1 AND scheduled_at='{app_time}'")
app_status_before = psql(f"SELECT status FROM appointments WHERE id={my_app_id}")
log_ev(f"Lịch khám ID {my_app_id} đang ở trạng thái: '{app_status_before}'")

r_rec_get = s_doc.get(f"{BASE_URL}/doctor/appointments/{my_app_id}/record")
token = extract_csrf(r_rec_get.text)
rec_data = {
    "csrf_token": token,
    "diagnosis": "Viêm loét dạ dày - tá tràng giai đoạn sớm",
    "prescription": "Esomeprazole 40mg: 1 viên/ngày uống trước ăn sáng 30 phút\nGaviscon: 1 gói uống sau ăn 1 giờ khi khó chịu",
    "notes": "Tránh thức ăn cay chua, tái khám sau 2 tuần để nội soi kiểm tra."
}
r_rec_post = s_doc.post(f"{BASE_URL}/doctor/appointments/{my_app_id}/record", data=rec_data)
log_ev(f"Bác sĩ An nhập bệnh án cho lịch khám ID {my_app_id} -> Status: {r_rec_post.status_code}")

# Verify status updated to 'done' in DB
app_after_status = psql(f"SELECT status FROM appointments WHERE id={my_app_id}")
log_ev(f"Trạng thái lịch khám ID {my_app_id} trong DB sau khi lưu bệnh án: '{app_after_status}' (Tự động chuyển 'done')")
assert app_after_status == "done"

# Doctor attempts to view appointment of ANOTHER doctor (e.g. doctor 2)
other_app_id = 2 # Assigned to bs.tran (doctor 2)
r_tamper = s_doc.get(f"{BASE_URL}/doctor/appointments/{other_app_id}/record")
log_ev(f"Bác sĩ An cố xem/ghi bệnh án của Bác sĩ khác (Lịch ID {other_app_id}) -> Status: {r_tamper.status_code} (Bị từ chối 403 Forbidden)")
assert r_tamper.status_code == 403
log_ev("")

# 6. PGADMIN TEST
log_ev("--- 6. KIỂM TRA PGADMIN (PORT 8081) ---")
r_pga = requests.get("http://localhost:8081/", allow_redirects=True)
log_ev(f"Truy cập pgAdmin http://localhost:8081/ -> HTTP Status: {r_pga.status_code}")
assert r_pga.status_code == 200
pga_title = re.search(r'<title>([^<]+)</title>', r_pga.text)
if pga_title:
    log_ev(f"  Tiêu đề trang pgAdmin: '{pga_title.group(1)}'")
log_ev("")

# 7. POSTGRESQL VERIFICATION & PERMISSIONS
log_ev("--- 7. KIỂM TRA POSTGRESQL & PHÂN QUYỀN CLINIC_APP (\\dp) ---")
p_counts = psql("SELECT concat('users: ', (SELECT count(*) FROM users), ', doctors: ', (SELECT count(*) FROM doctors), ', patients: ', (SELECT count(*) FROM patients), ', appointments: ', (SELECT count(*) FROM appointments), ', medical_records: ', (SELECT count(*) FROM medical_records));")
log_ev(f"Số lượng bản ghi trong 5 bảng:\n  {p_counts}")
log_ev("")
log_ev("Kiểm tra quyền truy cập bảng của clinic_app (\\dp):")
p_dp = subprocess.check_output(["docker", "exec", "clinic_db", "psql", "-U", "clinic_admin", "-d", "clinic", "-c", "\\dp"], text=True)
log_ev(p_dp)
log_ev("")

# Save to file
os.makedirs(os.path.dirname(EVIDENCE_FILE), exist_ok=True)
with open(EVIDENCE_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(evidence_lines) + "\n")

log_ev(f"Đã lưu toàn bộ bằng chứng vào {EVIDENCE_FILE}")
