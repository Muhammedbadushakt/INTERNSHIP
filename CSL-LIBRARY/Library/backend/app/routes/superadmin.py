from functools import wraps
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from app.extension import db
from app.models import Employee, Role

super_admin_bp = Blueprint(
    "super_admin",
    __name__,
    url_prefix="/superadmin-csl",   # non-obvious route — not publicly advertised
)

# ── Hardcoded credentials ──────────────────────────────────────────────────────
_SA_USERNAME = "csl_superadmin"
_SA_PASSWORD = "CSL@SuperAdmin#2025"
_SESSION_KEY = "_sa_auth"


# ── Auth guard ─────────────────────────────────────────────────────────────────
def super_admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get(_SESSION_KEY):
            return redirect(url_for("super_admin.login"))
        return fn(*args, **kwargs)
    return wrapper


# ── Login ──────────────────────────────────────────────────────────────────────
@super_admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get(_SESSION_KEY):
        return redirect(url_for("super_admin.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username == _SA_USERNAME and password == _SA_PASSWORD:
            session[_SESSION_KEY] = True
            session.permanent = False          # expires when browser closes
            return redirect(url_for("super_admin.dashboard"))

        flash("Invalid credentials. Access denied.", "error")

    return render_template("super_admin_login.html")


# ── Logout ─────────────────────────────────────────────────────────────────────
@super_admin_bp.route("/logout")
def logout():
    session.pop(_SESSION_KEY, None)
    return redirect(url_for("super_admin.login"))


# ── Dashboard ──────────────────────────────────────────────────────────────────
@super_admin_bp.route("/")
@super_admin_required
def dashboard():
    employees = Employee.query.order_by(Employee.name).all()

    admin_codes = {
        r.employee_code
        for r in Role.query.filter_by(name="admin").all()
    }

    return render_template(
        "super_admin_dashboard.html",
        employees=employees,
        admin_codes=admin_codes,
    )


# ── Assign admin ───────────────────────────────────────────────────────────────
@super_admin_bp.route("/assign", methods=["POST"])
@super_admin_required
def assign_admin():
    code = request.form.get("employee_code", "").strip()
    emp  = Employee.query.get(code) if code else None

    if not emp:
        flash("Employee not found.", "error")
        return redirect(url_for("super_admin.dashboard"))

    if Role.query.filter_by(employee_code=code, name="admin").first():
        flash(f"{emp.name} already has the admin role.", "info")
    else:
        db.session.add(Role(employee_code=code, name="admin"))
        db.session.commit()
        flash(f"Admin role granted to {emp.name}.", "success")

    return redirect(url_for("super_admin.dashboard"))


# ── Revoke admin ───────────────────────────────────────────────────────────────
@super_admin_bp.route("/revoke", methods=["POST"])
@super_admin_required
def revoke_admin():
    code = request.form.get("employee_code", "").strip()
    role = Role.query.filter_by(employee_code=code, name="admin").first()

    if role:
        db.session.delete(role)
        db.session.commit()
        emp  = Employee.query.get(code)
        name = emp.name if emp else code
        flash(f"Admin role removed from {name}.", "success")
    else:
        flash("That employee does not have the admin role.", "info")

    return redirect(url_for("super_admin.dashboard"))


# ── Activate employee ──────────────────────────────────────────────────────────
@super_admin_bp.route("/activate", methods=["POST"])
@super_admin_required
def activate_employee():
    code = request.form.get("employee_code", "").strip()
    emp  = Employee.query.get(code) if code else None

    if not emp:
        flash("Employee not found.", "error")
    elif emp.status == "ACTIVE":
        flash(f"{emp.name} is already active.", "info")
    else:
        emp.status = "ACTIVE"
        db.session.commit()
        flash(f"{emp.name} has been activated.", "success")

    return redirect(url_for("super_admin.dashboard"))


# ── Deactivate employee ────────────────────────────────────────────────────────
@super_admin_bp.route("/deactivate", methods=["POST"])
@super_admin_required
def deactivate_employee():
    code = request.form.get("employee_code", "").strip()
    emp  = Employee.query.get(code) if code else None

    if not emp:
        flash("Employee not found.", "error")
    elif emp.status != "ACTIVE":
        flash(f"{emp.name} is already inactive.", "info")
    else:
        emp.status = "INACTIVE"
        db.session.commit()
        flash(f"{emp.name} has been deactivated.", "success")

    return redirect(url_for("super_admin.dashboard"))
