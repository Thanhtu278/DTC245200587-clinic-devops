from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from .auth import login_required, role_required
from .db import query_all, query_one, get_db_connection

doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")

@doctor_bp.route("/appointments")
@login_required
@role_required(["doctor"])
def appointments():
    doctor_id = session.get("doctor_id")
    if not doctor_id:
        doc = query_one("SELECT id FROM doctors WHERE user_id = %s", (session.get("user_id"),))
        if doc:
            session["doctor_id"] = doc["id"]
            doctor_id = doc["id"]
        else:
            abort(403)

    appointments = query_all(
        """SELECT a.id, a.scheduled_at, a.status, a.reason,
                  p.id as patient_id, p.patient_code, p.full_name as patient_name, p.dob, p.gender, p.phone,
                  m.id as record_id, m.diagnosis, m.prescription, m.notes
           FROM appointments a
           JOIN patients p ON a.patient_id = p.id
           LEFT JOIN medical_records m ON a.id = m.appointment_id
           WHERE a.doctor_id = %s
           ORDER BY a.scheduled_at ASC""",
        (doctor_id,)
    )
    return render_template("doctor_appointments.html", appointments=appointments)

@doctor_bp.route("/appointments/<int:id>/record", methods=["GET", "POST"])
@login_required
@role_required(["doctor"])
def medical_record(id):
    doctor_id = session.get("doctor_id")
    appointment = query_one(
        """SELECT a.*, 
                  p.patient_code, p.full_name as patient_name, p.dob, p.gender, p.phone, p.address
           FROM appointments a
           JOIN patients p ON a.patient_id = p.id
           WHERE a.id = %s""",
        (id,)
    )

    if not appointment:
        abort(404)

    # Security check: Doctor CAN ONLY view their own appointment!
    if appointment["doctor_id"] != doctor_id:
        abort(403)

    record = query_one("SELECT * FROM medical_records WHERE appointment_id = %s", (id,))

    if request.method == "POST":
        if appointment["status"] not in ("booked", "confirmed"):
            flash("Lịch khám này đã hoàn thành hoặc đã bị hủy, không thể sửa bệnh án.", "warning")
            return redirect(url_for("doctor.appointments"))

        diagnosis = request.form.get("diagnosis", "").strip()
        prescription = request.form.get("prescription", "").strip()
        notes = request.form.get("notes", "").strip()

        if not diagnosis:
            flash("Chẩn đoán y khoa là bắt buộc.", "danger")
            return render_template("medical_record_form.html", appointment=appointment, record=request.form)

        # Single transaction: save medical record AND update appointment to 'done'
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO medical_records (appointment_id, diagnosis, prescription, notes)
                           VALUES (%s, %s, %s, %s)""",
                        (id, diagnosis, prescription, notes)
                    )
                    cur.execute(
                        """UPDATE appointments SET status = 'done' WHERE id = %s""",
                        (id,)
                    )
                conn.commit()

            flash("Đã ghi bệnh án và chuyển trạng thái lịch khám sang 'Đã khám' (done) thành công!", "success")
            return redirect(url_for("doctor.appointments"))
        except Exception as e:
            flash(f"Lỗi khi lưu bệnh án: {e}", "danger")
            return render_template("medical_record_form.html", appointment=appointment, record=request.form)

    return render_template("medical_record_form.html", appointment=appointment, record=record)
