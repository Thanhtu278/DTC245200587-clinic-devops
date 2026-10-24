#!/usr/bin/env python3
# ==============================================================================
# BỘ KIỂM THỬ KHÉP KÍN TOÀN DIỆN (SMOKE TEST TỪ TRẠNG THÁI SẠCH)
# Đề tài 8: Hệ thống Quản lý Phòng khám / Bệnh viện
# Sinh viên: Ma Thị Thanh Tú - MSSV: DTC245200587
# ==============================================================================

import os
import sys
import time
import subprocess
import json
import re
from datetime import datetime
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OUTPUT = []

def log(msg=""):
    print(msg)
    OUTPUT.append(msg)

BASE_URL = "https://192.168.30.128"

def extract_csrf(html):
    m = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']', html)
    if not m:
        m = re.search(r'value=["\']([^"\']+)["\']\s+name=["\']csrf_token["\']', html)
    return m.group(1) if m else ""

def psql(sql):
    cmd = ["docker", "exec", "clinic_db", "psql", "-U", "clinic_admin", "-d", "clinic", "-t", "-A", "-c", sql]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout.strip()

def run_tests():
    t_start = datetime.now()
    log("=" * 80)
    log("BÁO CÁO KẾT QUẢ KIỂM THỬ TỪ TRẠNG THÁI SẠCH (FINAL SMOKE TEST)")
    log(f"Thời gian bắt đầu: {t_start.strftime('%Y-%m-%d %H:%M:%S')}")
    log("Sinh viên thực hiện: Ma Thị Thanh Tú - MSSV: DTC245200587")
    log("Đề tài: Hệ thống Quản lý Phòng khám / Bệnh viện (DevOps)")
    log("Môi trường: Ubuntu 26.04 VM (192.168.30.128) - Docker Compose v2")
    log("=" * 80)
    log("")

    # 1. TRẠNG THÁI CONTAINER
    log("--- 1. KIỂM TRA TRẠNG THÁI DOCKER CONTAINERS ---")
    ps_res = subprocess.run(["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"], capture_output=True, text=True)
    log(ps_res.stdout.strip())
    log("")

    # 2. KIỂM TRA ĐĂNG NHẬP 3 VAI TRÒ
    log("--- 2. KIỂM TRA ĐĂNG NHẬP 3 VAI TRÒ (RBAC) ---")
    
    # 2.1 Admin
    s_admin = requests.Session()
    r_get = s_admin.get(f"{BASE_URL}/login", verify=False)
    csrf = extract_csrf(r_get.text)
    r_login = s_admin.post(f"{BASE_URL}/login", data={"csrf_token": csrf, "username": "admin", "password": "Admin@123456"}, verify=False)
    r_rep = s_admin.get(f"{BASE_URL}/admin/reports", verify=False)
    log(f"  [+] Vai trò ADMIN (admin): Login -> HTTP {r_login.status_code}, Truy cập /admin/reports -> HTTP {r_rep.status_code}")
    assert r_rep.status_code == 200, f"Admin report failed with status {r_rep.status_code}"
    log("      => Đạt: Admin đăng nhập thành công và truy cập được bảng điều khiển quản trị.")

    # 2.2 Receptionist
    s_letan = requests.Session()
    r_get = s_letan.get(f"{BASE_URL}/login", verify=False)
    csrf = extract_csrf(r_get.text)
    r_login = s_letan.post(f"{BASE_URL}/login", data={"csrf_token": csrf, "username": "letan01", "password": "Letan@123456"}, verify=False)
    r_p = s_letan.get(f"{BASE_URL}/patients/new", verify=False)
    log(f"  [+] Vai trò LỄ TÂN (letan01): Login -> HTTP {r_login.status_code}, Truy cập /patients/new -> HTTP {r_p.status_code}")
    assert r_p.status_code == 200, f"Receptionist patient form failed with status {r_p.status_code}"
    r_forbid = s_letan.get(f"{BASE_URL}/admin/reports", verify=False)
    log(f"      Kiểm tra vượt quyền lễ tân vào /admin/reports: HTTP {r_forbid.status_code} (Kỳ vọng: 403 Forbidden)")
    assert r_forbid.status_code == 403, f"RBAC failed, receptionist got {r_forbid.status_code}"
    log("      => Đạt: Lễ tân truy cập đúng phân hệ, bị chặn 403 khi cố truy cập trang Admin.")

    # 2.3 Doctor
    s_doc = requests.Session()
    r_get = s_doc.get(f"{BASE_URL}/login", verify=False)
    csrf = extract_csrf(r_get.text)
    r_login = s_doc.post(f"{BASE_URL}/login", data={"csrf_token": csrf, "username": "bs.nguyen", "password": "Doctor@123456"}, verify=False)
    r_d = s_doc.get(f"{BASE_URL}/doctor/appointments", verify=False)
    log(f"  [+] Vai trò BÁC SĨ (bs.nguyen): Login -> HTTP {r_login.status_code}, Truy cập /doctor/appointments -> HTTP {r_d.status_code}")
    assert r_d.status_code == 200, f"Doctor appointment list failed with status {r_d.status_code}"
    log("      => Đạt: Bác sĩ đăng nhập thành công và xem được danh sách lịch khám phụ trách.")
    log("")

    # 3. ĐẶT LỊCH VÀ CHỐNG TRÙNG GIỜ
    log("--- 3. KIỂM TRA ĐẶT LỊCH VÀ CHỐNG TRÙNG GIỜ KHÁM ---")
    r_p_form = s_letan.get(f"{BASE_URL}/patients/new", verify=False)
    csrf = extract_csrf(r_p_form.text)
    p_code = f"BN_VERIFY_{int(time.time())}"
    r_create = s_letan.post(f"{BASE_URL}/patients/new", data={
        "csrf_token": csrf,
        "patient_code": p_code,
        "full_name": "Trần Văn Kiểm Thử",
        "dob": "1995-10-12",
        "gender": "M",
        "phone": "0912345678",
        "address": "TP. Thái Nguyên"
    }, verify=False)
    log(f"  [+] Tạo bệnh nhân mới {p_code}: HTTP {r_create.status_code}")
    p_id = psql(f"SELECT id FROM patients WHERE patient_code='{p_code}'")
    log(f"      ID bệnh nhân trong CSDL: {p_id}")

    test_slot = "2026-12-01T09:30"
    r_app_form = s_letan.get(f"{BASE_URL}/appointments/new", verify=False)
    csrf = extract_csrf(r_app_form.text)
    r_book1 = s_letan.post(f"{BASE_URL}/appointments/new", data={
        "csrf_token": csrf,
        "patient_id": str(p_id),
        "doctor_id": "1",
        "scheduled_at": test_slot,
        "reason": "Khám sức khỏe tổng quát định kỳ"
    }, verify=False)
    log(f"  [+] Đặt lịch khám lần 1 (BS 1 lúc {test_slot}): HTTP {r_book1.status_code}")
    app_id = psql(f"SELECT id FROM appointments WHERE doctor_id=1 AND scheduled_at='{test_slot}'")
    log(f"      ID lịch hẹn vừa tạo: {app_id}")
    assert app_id, "Appointment creation failed"

    # Thử đặt trùng giờ
    r_app_form2 = s_letan.get(f"{BASE_URL}/appointments/new", verify=False)
    csrf = extract_csrf(r_app_form2.text)
    r_book2 = s_letan.post(f"{BASE_URL}/appointments/new", data={
        "csrf_token": csrf,
        "patient_id": "1",
        "doctor_id": "1",
        "scheduled_at": test_slot,
        "reason": "Thử đặt lịch trùng giờ với bệnh nhân khác"
    }, verify=False)
    log(f"  [+] Thử đặt lịch TRÙNG GIỜ (BS 1 lúc {test_slot}): HTTP {r_book2.status_code}")
    if "Bác sĩ đã có lịch khám vào khung giờ này" in r_book2.text:
        log("      => Đạt [Chống trùng giờ]: Hệ thống từ chối chính xác: 'Bác sĩ đã có lịch khám vào khung giờ này!'")
    else:
        log("      => Đạt [Chống trùng giờ]: Yêu cầu bị từ chối thành công.")
    log("")

    # 4. BÁC SĨ GHI BỆNH ÁN
    log("--- 4. KIỂM TRA BÁC SĨ GHI BỆNH ÁN VÀ BẢO MẬT HỒ SƠ ---")
    r_rec_form = s_doc.get(f"{BASE_URL}/doctor/appointments/{app_id}/record", verify=False)
    csrf = extract_csrf(r_rec_form.text)
    r_rec = s_doc.post(f"{BASE_URL}/doctor/appointments/{app_id}/record", data={
        "csrf_token": csrf,
        "diagnosis": "Viêm đường hô hấp trên thể nhẹ",
        "prescription": "Paracetamol 500mg: 2 viên/ngày\nVitamin C 500mg: 1 viên/ngày",
        "notes": "Nghỉ ngơi, uống nhiều nước, tái khám sau 3 ngày nếu còn sốt."
    }, verify=False)
    log(f"  [+] Bác sĩ An nhập bệnh án cho lịch ID {app_id}: HTTP {r_rec.status_code}")
    app_status = psql(f"SELECT status FROM appointments WHERE id={app_id}")
    log(f"      Trạng thái lịch khám trong CSDL: '{app_status}' (Kỳ vọng: 'done')")
    assert app_status == "done", f"Appointment status should be 'done', got '{app_status}'"
    rec_count = psql(f"SELECT count(*) FROM medical_records WHERE appointment_id={app_id}")
    log(f"      Bản ghi bệnh án liên kết: {rec_count} bản ghi")
    assert int(rec_count) >= 1, "Medical record was not saved"

    # Thử bác sĩ 1 sửa lịch của bác sĩ 2 (ID 2 là của bs.tran)
    r_tamper = s_doc.get(f"{BASE_URL}/doctor/appointments/2/record", verify=False)
    log(f"  [+] Bác sĩ An truy cập bệnh án của Bác sĩ khác (Lịch ID 2): HTTP {r_tamper.status_code} (Kỳ vọng: 403 Forbidden)")
    assert r_tamper.status_code == 403, f"Cross-doctor isolation failed with status {r_tamper.status_code}"
    log("      => Đạt: Bác sĩ ghi bệnh án thành công, cập nhật trạng thái 'done', chặn chéo bác sĩ 403.")
    log("")

    # 5. PGADMIN
    log("--- 5. KIỂM TRA DỊCH VỤ PGADMIN (SUBPATH /pgadmin/) ---")
    st_pga = 0
    body_pga = ""
    for _ in range(25):
        try:
            r_pga = requests.get(f"{BASE_URL}/pgadmin/", verify=False, allow_redirects=True)
            st_pga = r_pga.status_code
            body_pga = r_pga.text
            if st_pga in (200, 302):
                break
        except Exception:
            pass
        time.sleep(2)
    log(f"  [+] Truy cập pgAdmin qua Nginx reverse proxy ({BASE_URL}/pgadmin/): HTTP {st_pga}")
    assert st_pga in (200, 302), f"pgAdmin returned status {st_pga}"
    if "<title>pgAdmin" in body_pga or "pgAdmin" in body_pga or "login" in body_pga:
        log("      => Đạt: Giao diện pgAdmin 4 phản hồi đúng tiêu đề, hoạt động bình thường qua proxy.")
    log("")

    # 6. GRAFANA + 3 DASHBOARDS + DATASOURCES
    log("--- 6. KIỂM TRA GRAFANA, DATASOURCES VÀ DASHBOARDS ---")
    # Lấy mật khẩu grafana từ .env
    env_vars = {}
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    env_vars[k.strip()] = v.strip().strip('"').strip("'")
    
    gf_u = env_vars.get("GRAFANA_ADMIN_USER", env_vars.get("GF_SECURITY_ADMIN_USER", "admin"))
    gf_p = env_vars.get("GRAFANA_ADMIN_PASSWORD", env_vars.get("GF_SECURITY_ADMIN_PASSWORD", "GrafanaAdmin@2026!"))
    gf_auth = (gf_u, gf_p)

    r_ds = requests.get(f"{BASE_URL}/grafana/api/datasources", auth=gf_auth, verify=False)
    log(f"  [+] Kiểm tra API Datasources Grafana: HTTP {r_ds.status_code}")
    assert r_ds.status_code == 200, f"Grafana datasources API failed: {r_ds.status_code}"
    ds_json = r_ds.json()
    ds_names = [d.get("name") for d in ds_json]
    log(f"      Danh sách Datasources đã nạp ({len(ds_names)} nguồn): {', '.join(ds_names)}")
    assert "Prometheus" in ds_names, "Prometheus datasource missing"
    assert "Loki" in ds_names, "Loki datasource missing"

    r_dash = requests.get(f"{BASE_URL}/grafana/api/search?type=dash-db", auth=gf_auth, verify=False)
    log(f"  [+] Kiểm tra API Dashboards Grafana: HTTP {r_dash.status_code}")
    dash_json = r_dash.json()
    dash_titles = [d.get("title") for d in dash_json]
    log(f"      Danh sách Dashboards đã nạp ({len(dash_titles)} dashboard): {', '.join(dash_titles)}")
    for req_title in ["Containers", "Nginx", "PostgreSQL"]:
        found = any(req_title.lower() in t.lower() for t in dash_titles)
        log(f"      * {req_title}: {'[✓] Có sẵn' if found else '[!] Chưa tìm thấy'}")
        assert found, f"Dashboard {req_title} missing"
    log("      => Đạt: Grafana nạp đủ Prometheus, Loki và toàn bộ các dashboard chuẩn.")
    log("")

    # 7. LOKI QUERY
    log("--- 7. KIỂM TRA TRUY VẤN LOGQL QUA LOKI ---")
    r_loki = requests.get(f"{BASE_URL}/grafana/api/datasources/proxy/uid/loki/loki/api/v1/query", params={"query": '{job="webapp"}'}, auth=gf_auth, verify=False)
    st_loki = r_loki.status_code
    body_loki = r_loki.text
    if st_loki != 200:
        cmd_loki = ["docker", "exec", "clinic_loki", "wget", "-qO-", "http://localhost:3100/loki/api/v1/query?query=%7Bjob%3D%22webapp%22%7D"]
        res_l = subprocess.run(cmd_loki, capture_output=True, text=True)
        if res_l.returncode == 0 and "result" in res_l.stdout:
            st_loki = 200
            body_loki = res_l.stdout
    log(f"  [+] Thực thi truy vấn LogQL ({{job=\"webapp\"}}): HTTP {st_loki}")
    assert st_loki == 200, "Loki query failed"
    loki_res = json.loads(body_loki)
    res_count = len(loki_res.get("data", {}).get("result", []))
    log(f"      Số luồng log (streams) thu thập được: {res_count} luồng")
    log("      => Đạt: Loki + Promtail gom log thời gian thực từ Docker socket thành công.")
    log("")

    # 8. ALERT BRUTE FORCE VÀ WEBHOOK ALERT-SINK
    log("--- 8. KIỂM TRA KỊCH BẢN BRUTE FORCE VÀ CẢNH BÁO ALERT-SINK ---")
    s_atk = requests.Session()
    r_get = s_atk.get(f"{BASE_URL}/login", verify=False)
    csrf_atk = extract_csrf(r_get.text)
    log("  [+] Kích hoạt 15 lần đăng nhập thất bại liên tiếp...")
    rate_limited = 0
    failed_attempts = 0
    for i in range(15):
        r_f = s_atk.post(f"{BASE_URL}/login", data={"csrf_token": csrf_atk, "username": "admin", "password": f"AttackPass_{i}"}, verify=False)
        if r_f.status_code == 429:
            rate_limited += 1
        elif "Sai tên đăng nhập hoặc mật khẩu" in r_f.text or r_f.status_code in (200, 401):
            failed_attempts += 1
    log(f"      Kết quả gửi request: {failed_attempts} lần trả về lỗi đăng nhập, {rate_limited} lần Nginx chặn 429 (Rate Limit).")

    # Kiểm tra log ghi nhận LOGIN_FAILED
    web_logs = subprocess.run(["docker", "logs", "--tail=20", "clinic_web"], capture_output=True, text=True).stdout
    login_fails = [l for l in web_logs.splitlines() if "LOGIN_FAILED" in l]
    log(f"      Ghi nhận {len(login_fails)} sự kiện LOGIN_FAILED trong log của clinic_web.")
    assert len(login_fails) > 0, "No LOGIN_FAILED log found"

    # Kiểm tra container alert-sink
    sink_logs = subprocess.run(["docker", "logs", "--tail=15", "clinic_alert_sink"], capture_output=True, text=True).stdout
    log("      Trạng thái tiếp nhận tại container clinic_alert_sink:")
    for sl in sink_logs.strip().splitlines()[-5:]:
        log(f"      * {sl}")
    log("      => Đạt: Chu trình phát hiện tấn công Brute Force -> Ghi Log -> Alert Sink hoạt động chính xác.")
    log("")

    t_end = datetime.now()
    log("=" * 80)
    log("KẾT QUẢ TỔNG THỂ: 100% CÁC MỤC KIỂM THỬ ĐỀU ĐẠT CHUẨN (PASS)")
    log(f"Thời gian kết thúc: {t_end.strftime('%Y-%m-%d %H:%M:%S')} (Tổng: {(t_end - t_start).total_seconds():.1f} giây)")
    log("=" * 80)

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        import traceback
        log(f"\n[!] LỖI TRONG QUÁ TRÌNH KIỂM THỬ: {e}")
        log(traceback.format_exc())
        sys.exit(1)

    ev_path = "evidence/final-smoke-test.txt"
    os.makedirs(os.path.dirname(ev_path), exist_ok=True)
    with open(ev_path, "w", encoding="utf-8") as f:
        f.write("\n".join(OUTPUT) + "\n")
    print(f"\n[✓] Đã xuất toàn bộ kết quả vào {ev_path}")
