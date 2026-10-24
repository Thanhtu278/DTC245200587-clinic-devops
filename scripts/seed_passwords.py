import os
import psycopg
from werkzeug.security import generate_password_hash

# Đọc cấu hình từ .env nếu biến môi trường chưa có
env_vars = {}
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip()

db_host = os.getenv("DB_HOST", env_vars.get("DB_HOST", "db"))
db_port = os.getenv("DB_PORT", env_vars.get("DB_PORT", "5432"))
db_name = os.getenv("DB_NAME", env_vars.get("POSTGRES_DB", "clinic"))
db_user = os.getenv("POSTGRES_USER", env_vars.get("POSTGRES_USER", "clinic_admin"))
db_pass = os.getenv("POSTGRES_PASSWORD", env_vars.get("POSTGRES_PASSWORD", ""))

admin_pass = os.getenv("APP_ADMIN_PASSWORD", env_vars.get("APP_ADMIN_PASSWORD", ""))
letan_pass = os.getenv("APP_LETAN_PASSWORD", env_vars.get("APP_LETAN_PASSWORD", ""))
doctor_pass = os.getenv("APP_DOCTOR_PASSWORD", env_vars.get("APP_DOCTOR_PASSWORD", ""))

conn = psycopg.connect(
    host=db_host,
    port=db_port,
    dbname=db_name,
    user=db_user,
    password=db_pass
)

with conn.cursor() as cur:
    if admin_pass:
        admin_h = generate_password_hash(admin_pass)
        cur.execute("UPDATE users SET password_hash = %s WHERE username = 'admin'", (admin_h,))
    if letan_pass:
        letan_h = generate_password_hash(letan_pass)
        cur.execute("UPDATE users SET password_hash = %s WHERE username = 'letan01'", (letan_h,))
    if doctor_pass:
        doc_h = generate_password_hash(doctor_pass)
        cur.execute("UPDATE users SET role = 'doctor' WHERE username = 'bs.nguyen'")
        cur.execute("UPDATE users SET password_hash = %s WHERE role = 'doctor'", (doc_h,))
conn.commit()

print("All user passwords hashed and updated successfully from .env!")
