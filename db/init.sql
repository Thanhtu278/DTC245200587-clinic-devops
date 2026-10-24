#!/bin/bash
set -e

# 1. Create role clinic_app with dynamic password from environment
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-ROLE_SQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${APP_DB_USER:-clinic_app}') THEN
            CREATE ROLE ${APP_DB_USER:-clinic_app} WITH LOGIN PASSWORD '${APP_DB_PASSWORD}';
        ELSE
            ALTER ROLE ${APP_DB_USER:-clinic_app} WITH PASSWORD '${APP_DB_PASSWORD}';
        END IF;
    END
    \$\$;
ROLE_SQL

# 2. Schema and Seed with quoted heredoc (DO NOT expand $ in password hashes)
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" << 'EOSQL'
    -- 2. Users Table
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        full_name VARCHAR(100) NOT NULL,
        role VARCHAR(20) NOT NULL CHECK (role IN ('admin','receptionist','doctor')),
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- 3. Doctors Table
    CREATE TABLE IF NOT EXISTS doctors (
        id SERIAL PRIMARY KEY,
        user_id INT UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        specialty VARCHAR(100) NOT NULL,
        room VARCHAR(50) NOT NULL,
        phone VARCHAR(20) NOT NULL
    );

    -- 4. Patients Table
    CREATE TABLE IF NOT EXISTS patients (
        id SERIAL PRIMARY KEY,
        patient_code VARCHAR(20) UNIQUE NOT NULL,
        full_name VARCHAR(100) NOT NULL,
        dob DATE NOT NULL,
        gender CHAR(1) NOT NULL CHECK (gender IN ('M','F','O')),
        phone VARCHAR(20) NOT NULL,
        address TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- 5. Appointments Table
    CREATE TABLE IF NOT EXISTS appointments (
        id SERIAL PRIMARY KEY,
        patient_id INT NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
        doctor_id INT NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
        scheduled_at TIMESTAMPTZ NOT NULL,
        status VARCHAR(20) NOT NULL CHECK (status IN ('booked','confirmed','done','cancelled')) DEFAULT 'booked',
        reason TEXT,
        created_by INT REFERENCES users(id),
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- Partial unique index to prevent duplicate appointment for same doctor at same scheduled time
    CREATE UNIQUE INDEX IF NOT EXISTS uq_doctor_appointment 
        ON appointments (doctor_id, scheduled_at) 
        WHERE status <> 'cancelled';

    -- 6. Medical Records Table
    CREATE TABLE IF NOT EXISTS medical_records (
        id SERIAL PRIMARY KEY,
        appointment_id INT UNIQUE NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
        diagnosis TEXT NOT NULL,
        prescription TEXT,
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );

    -- 7. Grant minimal privileges to clinic_app
    REVOKE ALL ON SCHEMA public FROM PUBLIC;
    GRANT USAGE ON SCHEMA public TO clinic_app;
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO clinic_app;
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO clinic_app;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO clinic_app;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO clinic_app;

    -- 8. Seed Demo Users
    -- admin (Admin@123456)
    -- letan01 (Letan@123456)
    -- bs.nguyen, bs.tran, bs.le, bs.pham (Doctor@123456)
    INSERT INTO users (username, password_hash, full_name, role, is_active) VALUES
    ('admin', 'scrypt:32768:8:1$R3eFmdmzcgi706uB$4ab08ef875e36fcbb089f8bd359f5f80bcc0a7c618b4eae6682288f91af2908b35f91ccb6a66cc1960f946324894ded192612f099426f3868e9ffb01b265cefb', 'Quản Trị Viên Hệ Thống', 'admin', true),
    ('letan01', 'scrypt:32768:8:1$ab1xuQ36SDpUbhQK$c81621a3c93fc34a4ffcc66164561b45156fa000055e64906e52f2381be6d37b7a7ce7b6bbff91be998e430e43b57385a2cacd25ba6c703fa62fdbbe2e37c382', 'Lễ Tân Nguyễn Thị Mai', 'receptionist', true),
    ('bs.nguyen', 'scrypt:32768:8:1$JM2f1AKau8072aqj$1a2e3b6398703b566e0767560d07b3688156fe402e96e9676eaf220678ab80730d4ea2b00a78c647d69c491939afa13fbf3375e72639cbeb1d561938892a40cf', 'BS.CKI Nguyễn Văn An', 'doctor', true),
    ('bs.tran', 'scrypt:32768:8:1$JM2f1AKau8072aqj$1a2e3b6398703b566e0767560d07b3688156fe402e96e9676eaf220678ab80730d4ea2b00a78c647d69c491939afa13fbf3375e72639cbeb1d561938892a40cf', 'ThS.BS Trần Thị Bích', 'doctor', true),
    ('bs.le', 'scrypt:32768:8:1$JM2f1AKau8072aqj$1a2e3b6398703b566e0767560d07b3688156fe402e96e9676eaf220678ab80730d4ea2b00a78c647d69c491939afa13fbf3375e72639cbeb1d561938892a40cf', 'BS. Lê Hoàng Cường', 'doctor', true),
    ('bs.pham', 'scrypt:32768:8:1$JM2f1AKau8072aqj$1a2e3b6398703b566e0767560d07b3688156fe402e96e9676eaf220678ab80730d4ea2b00a78c647d69c491939afa13fbf3375e72639cbeb1d561938892a40cf', 'BS. Phạm Thu Dung', 'doctor', true)
    ON CONFLICT (username) DO UPDATE 
        SET password_hash = EXCLUDED.password_hash,
            full_name = EXCLUDED.full_name,
            role = EXCLUDED.role,
            is_active = EXCLUDED.is_active;

    -- 9. Seed Doctors
    INSERT INTO doctors (user_id, specialty, room, phone) VALUES
    ((SELECT id FROM users WHERE username='bs.nguyen'), 'Nội tổng quát', 'Phòng 101 (Tầng 1)', '0912345601'),
    ((SELECT id FROM users WHERE username='bs.tran'), 'Nhi khoa', 'Phòng 102 (Tầng 1)', '0912345602'),
    ((SELECT id FROM users WHERE username='bs.le'), 'Tai - Mũi - Họng', 'Phòng 201 (Tầng 2)', '0912345603'),
    ((SELECT id FROM users WHERE username='bs.pham'), 'Da liễu', 'Phòng 202 (Tầng 2)', '0912345604')
    ON CONFLICT (user_id) DO UPDATE 
        SET specialty = EXCLUDED.specialty,
            room = EXCLUDED.room,
            phone = EXCLUDED.phone;

    -- 10. Seed 12 Fake Patients
    INSERT INTO patients (patient_code, full_name, dob, gender, phone, address) VALUES
    ('BN001', 'Hoàng Văn Dũng', '1985-04-12', 'M', '0981112233', 'Tổ 5, P. Tân Thịnh, TP. Thái Nguyên'),
    ('BN002', 'Vũ Thị Hoa', '1992-08-23', 'F', '0982223344', 'Số 12, Đ. Lương Ngọc Quyến, TP. Thái Nguyên'),
    ('BN003', 'Đỗ Quang Hưng', '2015-11-05', 'M', '0983334455', 'Xã Quyết Thắng, TP. Thái Nguyên'),
    ('BN004', 'Bùi Lan Anh', '1978-02-19', 'F', '0984445566', 'P. Gia Sàng, TP. Thái Nguyên'),
    ('BN005', 'Ngô Quốc Khánh', '1999-07-30', 'M', '0985556677', 'P. Đồng Quang, TP. Thái Nguyên'),
    ('BN006', 'Dương Thị Yến', '2003-12-14', 'F', '0986667788', 'P. Phan Đình Phùng, TP. Thái Nguyên'),
    ('BN007', 'Lý Thành Long', '1965-06-25', 'M', '0987778899', 'P. Chùa Hang, TP. Thái Nguyên'),
    ('BN008', 'Chu Mai Linh', '2018-09-02', 'F', '0988889900', 'Xã Thịnh Đức, TP. Thái Nguyên'),
    ('BN009', 'Đặng Đức Nam', '1990-01-18', 'M', '0989990011', 'P. Quang Trung, TP. Thái Nguyên'),
    ('BN010', 'Trịnh Thúy Nga', '1988-05-22', 'F', '0910001122', 'P. Túc Duyên, TP. Thái Nguyên'),
    ('BN011', 'Phan Văn Phong', '1972-10-10', 'M', '0911112233', 'P. Hương Sơn, TP. Thái Nguyên'),
    ('BN012', 'Tạ Minh Phương', '2000-03-15', 'F', '0912223344', 'Xã Cao Ngạn, TP. Thái Nguyên')
    ON CONFLICT (patient_code) DO NOTHING;

    -- 11. Seed 10 Appointments
    -- Past appointments (done, cancelled)
    INSERT INTO appointments (id, patient_id, doctor_id, scheduled_at, status, reason, created_by) VALUES
    (1, 1, 1, NOW() - INTERVAL '3 days' + INTERVAL '8 hours', 'done', 'Khám sức khỏe tổng quát định kỳ', 2),
    (2, 2, 2, NOW() - INTERVAL '2 days' + INTERVAL '9 hours', 'done', 'Sốt nhẹ, ho khan có đờm', 2),
    (3, 3, 3, NOW() - INTERVAL '1 day' + INTERVAL '10 hours', 'done', 'Đau rát họng, nghẹt mũi', 2),
    (4, 4, 4, NOW() - INTERVAL '1 day' + INTERVAL '14 hours', 'cancelled', 'Nổi mẩn ngứa - Bệnh nhân bận việc đột xuất xin hủy', 2),
    -- Future appointments (booked, confirmed)
    (5, 5, 1, NOW() + INTERVAL '1 day' + INTERVAL '8 hours', 'confirmed', 'Tái khám huyết áp và xét nghiệm mỡ máu', 2),
    (6, 6, 2, NOW() + INTERVAL '1 day' + INTERVAL '9 hours', 'booked', 'Tiêm chủng và kiểm tra dinh dưỡng', 2),
    (7, 7, 3, NOW() + INTERVAL '2 days' + INTERVAL '10 hours', 'booked', 'Ù tai kéo dài 3 ngày', 2),
    (8, 8, 4, NOW() + INTERVAL '2 days' + INTERVAL '14 hours', 'confirmed', 'Viêm da cơ địa tái phát', 2),
    (9, 9, 1, NOW() + INTERVAL '3 days' + INTERVAL '15 hours', 'booked', 'Đau tức vùng thượng vị sau ăn', 2),
    (10, 10, 2, NOW() + INTERVAL '3 days' + INTERVAL '16 hours', 'booked', 'Trẻ biếng ăn, quấy khóc đêm', 2)
    ON CONFLICT (id) DO NOTHING;
    SELECT setval('appointments_id_seq', (SELECT COALESCE(MAX(id), 1) FROM appointments));

    -- 12. Seed 3 Medical Records
    INSERT INTO medical_records (appointment_id, diagnosis, prescription, notes) VALUES
    (1, 'Huyết áp bình thường, trào ngược dạ dày thực quản nhẹ', 'Omeprazole 20mg: 1 viên/ngày (uống sáng trước ăn 30p)\nVitamin 3B: 2 viên/ngày (chia sáng - chiều sau ăn)', 'Ăn uống đúng giờ, kiêng đồ chua cay và cà phê. Tái khám sau 1 tháng nếu còn khó chịu.'),
    (2, 'Viêm họng cấp tính do thời tiết', 'Augmentin 250mg: 2 gói/ngày (uống sau ăn)\nParacetamol 250mg: 1 gói khi sốt trên 38.5 độ (cách nhau 4-6 giờ)', 'Uống nhiều nước ấm, súc miệng nước muối, tái khám sau 3 ngày.'),
    (3, 'Viêm mũi xoang cấp mủ', 'Cefixime 200mg: 2 viên/ngày (chia 2 lần sau ăn)\nXịt mũi Otrivin 0.05%: Xịt 1 nhát mỗi bên trước khi ngủ', 'Xịt rửa mũi bằng nước muối sinh lý 0.9% 3 lần/ngày.')
    ON CONFLICT (appointment_id) DO NOTHING;
    SELECT setval('medical_records_id_seq', (SELECT COALESCE(MAX(id), 1) FROM medical_records));
EOSQL
