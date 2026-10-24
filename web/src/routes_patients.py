from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from .auth import login_required, role_required
from .db import query_all, query_one, execute

patients_bp = Blueprint("patients", __name__, url_prefix="/patients")

@patients_bp.route("")
@login_required
@role_required(["receptionist", "admin"])
def list_patients():
    q = request.args.get("q", "").strip()
    if q:
        search = f"%{q}%"
        patients = query_all(
            """SELECT * FROM patients 
               WHERE patient_code ILIKE %s OR full_name ILIKE %s OR phone ILIKE %s 
               ORDER BY id DESC""",
            (search, search, search)
        )
    else:
        patients = query_all("SELECT * FROM patients ORDER BY id DESC")
    return render_template("patients.html", patients=patients, q=q)

@patients_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(["receptionist", "admin"])
def new_patient():
    if request.method == "POST":
        patient_code = request.form.get("patient_code", "").strip().upper()
        full_name = request.form.get("full_name", "").strip()
        dob = request.form.get("dob", "").strip()
        gender = request.form.get("gender", "O")
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        if not patient_code or not full_name or not dob or not phone:
            flash("Vui lòng điền đầy đủ các trường bắt buộc.", "danger")
            return render_template("patient_form.html", patient=request.form)

        # Check existing code
        existing = query_one("SELECT id FROM patients WHERE patient_code = %s", (patient_code,))
        if existing:
            flash(f"Mã bệnh nhân '{patient_code}' đã tồn tại trên hệ thống!", "danger")
            return render_template("patient_form.html", patient=request.form)

        try:
            execute(
                """INSERT INTO patients (patient_code, full_name, dob, gender, phone, address) 
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (patient_code, full_name, dob, gender, phone, address)
            )
            flash(f"Thêm mới bệnh nhân {full_name} ({patient_code}) thành công!", "success")
            return redirect(url_for("patients.list_patients"))
        except Exception as e:
            flash(f"Lỗi khi thêm bệnh nhân: {e}", "danger")
            return render_template("patient_form.html", patient=request.form)

    return render_template("patient_form.html", patient={})

@patients_bp.route("/<int:id>")
@login_required
@role_required(["receptionist", "admin"])
def patient_detail(id):
    patient = query_one("SELECT * FROM patients WHERE id = %s", (id,))
    if not patient:
        abort(404)

    appointments = query_all(
        """SELECT a.id, a.scheduled_at, a.status, a.reason,
                  u.full_name as doctor_name, d.specialty, d.room,
                  m.diagnosis, m.prescription, m.notes
           FROM appointments a
           JOIN doctors d ON a.doctor_id = d.id
           JOIN users u ON d.user_id = u.id
           LEFT JOIN medical_records m ON a.id = m.appointment_id
           WHERE a.patient_id = %s
           ORDER BY a.scheduled_at DESC""",
        (id,)
    )
    return render_template("patient_detail.html", patient=patient, appointments=appointments)

@patients_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
@role_required(["receptionist", "admin"])
def edit_patient(id):
    patient = query_one("SELECT * FROM patients WHERE id = %s", (id,))
    if not patient:
        abort(404)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        dob = request.form.get("dob", "").strip()
        gender = request.form.get("gender", "O")
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        if not full_name or not dob or not phone:
            flash("Vui lòng điền đầy đủ các trường bắt buộc.", "danger")
            return render_template("patient_form.html", patient=patient, edit=True)

        try:
            execute(
                """UPDATE patients 
                   SET full_name = %s, dob = %s, gender = %s, phone = %s, address = %s 
                   WHERE id = %s""",
                (full_name, dob, gender, phone, address, id)
            )
            flash("Cập nhật thông tin bệnh nhân thành công!", "success")
            return redirect(url_for("patients.patient_detail", id=id))
        except Exception as e:
            flash(f"Lỗi khi cập nhật bệnh nhân: {e}", "danger")

    return render_template("patient_form.html", patient=patient, edit=True)
