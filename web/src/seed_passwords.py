import os
import psycopg
from werkzeug.security import generate_password_hash

def seed_passwords():
    db_host = os.getenv("DB_HOST", "db")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "clinic")
    db_user = os.getenv("APP_DB_USER", "clinic_app")
    db_pass = os.getenv("APP_DB_PASSWORD", "")

    admin_pass = os.getenv("APP_ADMIN_PASSWORD", "")
    letan_pass = os.getenv("APP_LETAN_PASSWORD", "")
    doctor_pass = os.getenv("APP_DOCTOR_PASSWORD", "")

    if not all([admin_pass, letan_pass, doctor_pass, db_pass]):
        print("[!] Thiếu biến môi trường mật khẩu trong .env, bỏ qua seed.")
        return

    admin_h = generate_password_hash(admin_pass)
    letan_h = generate_password_hash(letan_pass)
    doc_h = generate_password_hash(doctor_pass)

    conn = psycopg.connect(
        host=db_host,
        port=db_port,
        dbname=db_name,
        user=db_user,
        password=db_pass
    )

    with conn.cursor() as cur:
        cur.execute("UPDATE users SET password_hash = %s WHERE username = 'admin'", (admin_h,))
        cur.execute("UPDATE users SET password_hash = %s WHERE username = 'letan01'", (letan_h,))
        cur.execute("UPDATE users SET password_hash = %s WHERE role = 'doctor'", (doc_h,))
    conn.commit()
    conn.close()
    print("[✓] Passwords updated successfully in PostgreSQL database!")

if __name__ == "__main__":
    seed_passwords()
