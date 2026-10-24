import os
import secrets
from datetime import timedelta
from flask import Flask, redirect, url_for, session, render_template, request, abort
from werkzeug.middleware.proxy_fix import ProxyFix
from .db import get_db_connection
from .auth import auth_bp
from .routes_patients import patients_bp
from .routes_appointments import appointments_bp
from .routes_doctor import doctor_bp
from .routes_admin import admin_bp

def create_app():
    app = Flask(__name__)
    # Cấu hình ProxyFix tin cậy headers từ Nginx (X-Forwarded-For, X-Forwarded-Proto, X-Forwarded-Host)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-clinic-2026")
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=60)
    app.config["SESSION_COOKIE_NAME"] = "clinic_session"

    @app.after_request
    def remove_server_headers(response):
        response.headers.pop("Server", None)
        response.headers.pop("X-Powered-By", None)
        return response

    # Healthcheck endpoint
    @app.route("/health")
    def health():
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            return "OK", 200
        except Exception as e:
            return f"ERROR: {e}", 500

    # Ensure CSRF token in session for any request
    @app.before_request
    def csrf_middleware():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(24)

        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            if request.path == "/health":
                return
            token = session.get("csrf_token")
            req_token = request.form.get("csrf_token") or request.headers.get("X-CSRFToken")
            if not req_token or req_token != token:
                abort(400, description="CSRF token không hợp lệ hoặc đã hết hạn.")

    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=session.get("csrf_token", ""))

    # Root redirect
    @app.route("/")
    def index():
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        role = session.get("role")
        if role == "doctor":
            return redirect(url_for("doctor.appointments"))
        elif role == "receptionist":
            return redirect(url_for("patients.list_patients"))
        else:
            return redirect(url_for("admin.reports"))

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(admin_bp)

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("base.html", error_title="403 - Không Có Quyền Truy Cập", error_msg="Bạn không có quyền thực hiện thao tác này hoặc xem tài nguyên của người khác."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("base.html", error_title="404 - Không Tìm Thấy Trang", error_msg="Trang hoặc tài nguyên bạn yêu cầu không tồn tại."), 404

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8000, debug=True)
