from werkzeug.security import generate_password_hash
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from .auth import login_required, role_required
from .db import query_all, query_one, execute, get_db_connection

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/users")
@login_required
@role_required(["admin"])
def list_users():
    users = query_all("""
        SELECT u.id, u.username, u.full_name, u.role, u.is_active, u.created_at,
               d.specialty, d.room, d.phone as doctor_phone
        FROM users u
        LEFT JOIN doctors d ON u.id = d.user_id
        ORDER BY u.id ASC
    """)
    return render_template("admin_users.html", users=users)

@admin_bp.route("/users/new", methods=["GET", "POST"])
@login_required
@role_required(["admin"])
def new_user():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "").strip()
        role = request.form.get("role", "receptionist")

        specialty = request.form.get("specialty", "").strip()
        room = request.form.get("room", "").strip()
        phone = request.form.get("phone", "").strip()

        if not username or not password or not full_name:
            flash("Vui lòng điền đầy đủ tên đăng nhập, mật khẩu và họ tên.", "danger")
            return render_template("admin_user_form.html", user=request.form)

        existing = query_one("SELECT id FROM users WHERE username = %s", (username,))
        if existing:
            flash(f"Tên đăng nhập '{username}' đã tồn tại!", "danger")
            return render_template("admin_user_form.html", user=request.form)

        pw_hash = generate_password_hash(password)

        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO users (username, password_hash, full_name, role, is_active)
                           VALUES (%s, %s, %s, %s, true) RETURNING id""",
                        (username, pw_hash, full_name, role)
                    )
                    user_id = cur.fetchone()["id"]

                    if role == "doctor":
                        cur.execute(
                            """INSERT INTO doctors (user_id, specialty, room, phone)
                               VALUES (%s, %s, %s, %s)""",
                            (user_id, specialty or "Đa khoa", room or "Phòng 101", phone or "Chưa cập nhật")
                        )
                conn.commit()

            flash(f"Tạo người dùng '{username}' thành công!", "success")
            return redirect(url_for("admin.list_users"))
        except Exception as e:
            flash(f"Lỗi khi tạo người dùng: {e}", "danger")

    return render_template("admin_user_form.html", user={})

@admin_bp.route("/users/<int:id>/toggle-active", methods=["POST"])
@login_required
@role_required(["admin"])
def toggle_active(id):
    if id == session.get("user_id"):
        flash("Bạn không thể tự khóa tài khoản của chính mình!", "warning")
        return redirect(url_for("admin.list_users"))

    user = query_one("SELECT is_active, full_name FROM users WHERE id = %s", (id,))
    if not user:
        abort(404)

    new_status = not user["is_active"]
    execute("UPDATE users SET is_active = %s WHERE id = %s", (new_status, id))
    msg = f"Đã mở khóa tài khoản {user['full_name']}." if new_status else f"Đã khóa tài khoản {user['full_name']}."
    flash(msg, "info")
    return redirect(url_for("admin.list_users"))

@admin_bp.route("/users/<int:id>/reset-password", methods=["POST"])
@login_required
@role_required(["admin"])
def reset_password(id):
    new_pw = request.form.get("new_password", "").strip()
    if not new_pw:
        flash("Mật khẩu mới không được để trống.", "danger")
        return redirect(url_for("admin.list_users"))

    pw_hash = generate_password_hash(new_pw)
    execute("UPDATE users SET password_hash = %s WHERE id = %s", (pw_hash, id))
    flash("Đặt lại mật khẩu thành công!", "success")
    return redirect(url_for("admin.list_users"))

@admin_bp.route("/reports")
@login_required
@role_required(["admin"])
def reports():
    date_filter = request.args.get("date_filter", "all")

    date_clause = ""
    if date_filter == "today":
        date_clause = "WHERE DATE(scheduled_at) = CURRENT_DATE"
    elif date_filter == "week":
        date_clause = "WHERE scheduled_at >= CURRENT_DATE - INTERVAL '7 days'"
    elif date_filter == "month":
        date_clause = "WHERE scheduled_at >= CURRENT_DATE - INTERVAL '30 days'"

    # Overview stats
    stats = query_one(f"""
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE status = 'booked') as booked,
            COUNT(*) FILTER (WHERE status = 'confirmed') as confirmed,
            COUNT(*) FILTER (WHERE status = 'done') as done,
            COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled
        FROM appointments
        {date_clause}
    """)

    total_patients = query_one("SELECT COUNT(*) as cnt FROM patients")["cnt"]
    total_doctors = query_one("SELECT COUNT(*) as cnt FROM doctors")["cnt"]

    # Stats by doctor
    doc_stats = query_all(f"""
        SELECT u.full_name as doctor_name, d.specialty, d.room,
               COUNT(a.id) as total,
               COUNT(a.id) FILTER (WHERE a.status = 'done') as done,
               COUNT(a.id) FILTER (WHERE a.status = 'booked') as booked,
               COUNT(a.id) FILTER (WHERE a.status = 'confirmed') as confirmed,
               COUNT(a.id) FILTER (WHERE a.status = 'cancelled') as cancelled
        FROM doctors d
        JOIN users u ON d.user_id = u.id
        LEFT JOIN appointments a ON d.id = a.doctor_id {date_clause.replace('WHERE', 'AND')}
        GROUP BY u.full_name, d.specialty, d.room
        ORDER BY total DESC
    """)

    return render_template(
        "admin_reports.html",
        stats=stats,
        total_patients=total_patients,
        total_doctors=total_doctors,
        doc_stats=doc_stats,
        date_filter=date_filter
    )
