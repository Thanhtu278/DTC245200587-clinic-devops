import os
import psycopg
from werkzeug.security import generate_password_hash

conn = psycopg.connect(
    host=os.getenv("DB_HOST", "db"),
    port=os.getenv("DB_PORT", "5432"),
    dbname=os.getenv("DB_NAME", "clinic"),
    user="clinic_admin",
    password=os.getenv("POSTGRES_PASSWORD", "ClinicAdmin!2026#SecDb")
)

with conn.cursor() as cur:
    admin_h = generate_password_hash("Admin@123456")
    letan_h = generate_password_hash("Letan@123456")
    doc_h = generate_password_hash("Doctor@123456")

    cur.execute("UPDATE users SET password_hash = %s WHERE username = 'admin'", (admin_h,))
    cur.execute("UPDATE users SET password_hash = %s WHERE username = 'letan01'", (letan_h,))
    cur.execute("UPDATE users SET password_hash = %s WHERE role = 'doctor'", (doc_h,))
conn.commit()

print("All passwords hashed and updated successfully!")
print("Admin hash:", admin_h[:25] + "...")
print("Letan hash:", letan_h[:25] + "...")
print("Doctor hash:", doc_h[:25] + "...")
