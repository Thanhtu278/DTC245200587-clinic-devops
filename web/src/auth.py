import sys
import secrets
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import check_password_hash, generate_password_hash
from .db import query_one

auth_bp = Blueprint("auth", __name__)

def get_client_ip():
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "127.0.0.1"

def log_login_failed(ip, username, reason):
    sys.stderr.write(f"LOGIN_FAILED ip={ip} user={username} reason={reason}\n")
    sys.stderr.flush()

def log_login_success(ip, username):
    sys.stderr.write(f"LOGIN_SUCCESS ip={ip} user={username}\n")
    sys.stderr.flush()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Vui lòng đăng nhập để tiếp tục.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                flash("Vui lòng đăng nhập để tiếp tục.", "warning")
                return redirect(url_for("auth.login", next=request.path))
            user_role = session.get("role")
            if user_role not in allowed_roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        ip = get_client_ip()

        if not username or not password:
            flash("Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.", "danger")
            log_login_failed(ip, username or "none", "unknown_user")
            return render_template("login.html"), 401

        user = query_one(
            "SELECT id, username, password_hash, full_name, role, is_active FROM users WHERE username = %s",
            (username,)
        )

        if not user:
            log_login_failed(ip, username, "unknown_user")
            flash("Tên đăng nhập hoặc mật khẩu không chính xác.", "danger")
            return render_template("login.html"), 401

        if not user["is_active"]:
            log_login_failed(ip, username, "inactive")
            flash("Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên.", "danger")
            return render_template("login.html"), 403

        if not check_password_hash(user["password_hash"], password):
            log_login_failed(ip, username, "wrong_password")
            flash("Tên đăng nhập hoặc mật khẩu không chính xác.", "danger")
            return render_template("login.html"), 401

        # Success: populate session
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["full_name"] = user["full_name"]
        session["role"] = user["role"]
        session["csrf_token"] = secrets.token_hex(24)

        if user["role"] == "doctor":
            doc = query_one("SELECT id FROM doctors WHERE user_id = %s", (user["id"],))
            session["doctor_id"] = doc["id"] if doc else None

        log_login_success(ip, username)
        flash(f"Xin chào {user['full_name']}! Bạn đã đăng nhập thành công.", "success")

        next_url = request.args.get("next")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)

        if user["role"] == "doctor":
            return redirect(url_for("doctor.appointments"))
        elif user["role"] == "receptionist":
            return redirect(url_for("patients.list_patients"))
        else:
            return redirect(url_for("admin.reports"))

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Bạn đã đăng xuất thành công.", "info")
    return redirect(url_for("auth.login"))
