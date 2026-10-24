from datetime import datetime, timezone
import psycopg
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from .auth import login_required, role_required
from .db import query_all, query_one, execute

appointments_bp = Blueprint("appointments", __name__, url_prefix="/appointments")

@appointments_bp.route("")
@login_required
@role_required(["receptionist", "admin"])
def list_appointments():
    date_filter = request.args.get("date", "").strip()
    doctor_filter = request.args.get("doctor_id", "").strip()
    status_filter = request.args.get("status", "").strip()

    sql = """
        SELECT a.id, a.scheduled_at, a.status, a.reason,
               p.id as patient_id, p.patient_code, p.full_name as patient_name, p.phone as patient_phone,
               u.full_name as doctor_name, d.id as doctor_id, d.specialty, d.room,
               creator.full_name as creator_name
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN users u ON d.user_id = u.id
        LEFT JOIN users creator ON a.created_by = creator.id
        WHERE 1=1
    """
    params = []

    if date_filter:
        sql += " AND DATE(a.scheduled_at) = %s"
        params.append(date_filter)
    if doctor_filter:
        sql += " AND a.doctor_id = %s"
        params.append(doctor_filter)
    if status_filter:
        sql += " AND a.status = %s"
        params.append(status_filter)

    sql += " ORDER BY a.scheduled_at DESC"
    appointments = query_all(sql, tuple(params))

    doctors = query_all("""
        SELECT d.id, u.full_name, d.specialty, d.room 
        FROM doctors d 
        JOIN users u ON d.user_id = u.id 
        WHERE u.is_active = true 
        ORDER BY u.full_name
    """)

    return render_template(
        "appointments.html",
        appointments=appointments,
        doctors=doctors,
        date_filter=date_filter,
        doctor_filter=doctor_filter,
        status_filter=status_filter
    )

@appointments_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(["receptionist", "admin"])
def new_appointment():
    patients = query_all("SELECT id, patient_code, full_name, phone FROM patients ORDER BY full_name")
    doctors = query_all("""
        SELECT d.id, u.full_name, d.specialty, d.room 
        FROM doctors d 
        JOIN users u ON d.user_id = u.id 
        WHERE u.is_active = true 
        ORDER BY u.full_name
    """)

    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        doctor_id = request.form.get("doctor_id")
        scheduled_at_str = request.form.get("scheduled_at", "").strip()
        reason = request.form.get("reason", "").strip()

        if not patient_id or not doctor_id or not scheduled_at_str:
            flash("Vui lòng chọn đầy đủ bệnh nhân, bác sĩ và thời gian khám.", "danger")
            return render_template("appointment_form.html", patients=patients, doctors=doctors, form=request.form)

        # 1. Check past appointment
        try:
            # Format expected from datetime-local input: YYYY-MM-DDTHH:MM
            dt = datetime.fromisoformat(scheduled_at_str)
            now = datetime.now()
            if dt <= now:
                flash("Không thể đặt lịch khám trong quá khứ! Vui lòng chọn thời gian từ hiện tại trở đi.", "danger")
                return render_template("appointment_form.html", patients=patients, doctors=doctors, form=request.form)
        except ValueError:
            flash("Định dạng ngày giờ không hợp lệ.", "danger")
            return render_template("appointment_form.html", patients=patients, doctors=doctors, form=request.form)

        # 2. Check doctor overlapping appointment
        existing = query_one(
            """SELECT id FROM appointments 
               WHERE doctor_id = %s AND scheduled_at = %s AND status <> 'cancelled'""",
            (doctor_id, scheduled_at_str)
        )
        if existing:
            flash("Bác sĩ đã có lịch khám vào khung giờ này! Vui lòng chọn giờ khác hoặc chọn bác sĩ khác.", "danger")
            return render_template("appointment_form.html", patients=patients, doctors=doctors, form=request.form)

        # 3. Insert with unique constraint handling
        try:
            execute(
                """INSERT INTO appointments (patient_id, doctor_id, scheduled_at, status, reason, created_by)
                   VALUES (%s, %s, %s, 'booked', %s, %s)""",
                (patient_id, doctor_id, scheduled_at_str, reason, session.get("user_id"))
            )
            flash("Đặt lịch khám thành công!", "success")
            return redirect(url_for("appointments.list_appointments"))
        except psycopg.errors.UniqueViolation:
            flash("Bác sĩ đã có lịch khám vào khung giờ này! Vui lòng chọn giờ khác.", "danger")
            return render_template("appointment_form.html", patients=patients, doctors=doctors, form=request.form)
        except Exception as e:
            flash(f"Lỗi khi đặt lịch khám: {e}", "danger")
            return render_template("appointment_form.html", patients=patients, doctors=doctors, form=request.form)

    preselect_patient = request.args.get("patient_id")
    return render_template("appointment_form.html", patients=patients, doctors=doctors, preselect_patient=preselect_patient, form={})

@appointments_bp.route("/<int:id>/confirm", methods=["POST"])
@login_required
@role_required(["receptionist", "admin"])
def confirm_appointment(id):
    app = query_one("SELECT status FROM appointments WHERE id = %s", (id,))
    if not app:
        abort(404)
    if app["status"] != "booked":
        flash("Chỉ có thể xác nhận lịch khám đang ở trạng thái 'Đã đặt' (booked).", "warning")
    else:
        execute("UPDATE appointments SET status = 'confirmed' WHERE id = %s", (id,))
        flash("Xác nhận lịch khám thành công!", "success")
    return redirect(url_for("appointments.list_appointments"))

@appointments_bp.route("/<int:id>/cancel", methods=["POST"])
@login_required
@role_required(["receptionist", "admin"])
def cancel_appointment(id):
    app = query_one("SELECT status FROM appointments WHERE id = %s", (id,))
    if not app:
        abort(404)
    if app["status"] == "done":
        flash("Không thể hủy lịch khám đã hoàn thành (done)!", "danger")
    else:
        execute("UPDATE appointments SET status = 'cancelled' WHERE id = %s", (id,))
        flash("Đã hủy lịch khám thành công.", "info")
    return redirect(url_for("appointments.list_appointments"))
