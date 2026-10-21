from flask import Blueprint, request, redirect, url_for, render_template, jsonify, make_response
from app.extension import db
from app.models import Employee, Role, User, GuestUser
import random, string
from datetime import datetime, timedelta, timezone
from app.utils import get_ldap_connection
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
)
from ldap3 import Server, Connection,SUBTREE,SIMPLE, Tls
from app.config import Config
import ssl

OTP_EXPIRES = timedelta(minutes=10)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

def authenticate_ldap(username,password):
    tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)
    server = Server(Config.LDAP_SERVER,use_ssl=True, port=636, tls=tls_config)
    try:
        with Connection(server,
                        user=f'{Config.AD_DOMAIN}\\{username}',
                        password=password,
                        authentication=SIMPLE,
                        check_names=True,
                        raise_exceptions=True) as conn:
                            return True,None
    except Exception as e:
        msg = f'Authentication Failed {e}'
        return False,msg

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────


def _make_tokens_response(redirect_url: str, employee_code: str, role: str):
    """
    Creates a redirect response and attaches JWT access + refresh tokens
    as HttpOnly cookies. This is the correct way to use JWT with
    server-rendered Jinja templates.
    """
    access_token  = create_access_token(
        identity=employee_code,
        additional_claims={"role": role}
    )
    refresh_token = create_refresh_token(identity=employee_code)

    response = make_response(redirect(redirect_url))
    set_access_cookies(response, access_token)    # sets cookie: access_token_cookie
    set_refresh_cookies(response, refresh_token)  # sets cookie: refresh_token_cookie
    return response


def _get_employee_role(employee_code: str) -> str | None:
    """Returns the highest role for an employee, or None if not found."""
    roles = [
        r.name.lower()
        for r in Role.query.filter_by(employee_code=employee_code).all()
    ]
    # Priority: admin > employee
    if "admin" in roles:
        return "admin"
    if "employee" in roles:
        return "employee"
    return roles[0] if roles else None


# ─────────────────────────────────────────────
#  HOME
# ─────────────────────────────────────────────

@auth_bp.route("/")
def home():
    return render_template("Home.html")


# ─────────────────────────────────────────────
#  REGISTER
# ─────────────────────────────────────────────

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # Pass existing employee codes to template so the form can show a datalist
    # or validate that the code doesn't already exist

    if request.method == "POST":
        fields = {
            "employee_code":  request.form.get("employee_code", "").strip(),
            "name":           request.form.get("name", "").strip(),
            "department":     request.form.get("department", "").strip(),
            "designation":    request.form.get("designation", "").strip(),
            "gmail_id":       request.form.get("gmail_id", "").strip(),
            "contact_number": request.form.get("contact_number", "").strip(),
        }
        # ── validation ──────────────────────────────
        if not all(fields.values()):
            return render_template("Regist.html",
                                   error="All fields are required.")
        with get_ldap_connection() as conn:
            print(conn.bind())
            print(conn.result)
            search_filter = f'(sAMAccountName={fields["employee_code"]})'
            conn.search(search_base=Config.SEARCH_BASE,
                        search_filter=search_filter)
            if conn.entries:
                emp = True
            else:
                emp = False
        if not emp:
            return(render_template("Regist.html",error="Username not found"))
        # ── save ────────────────────────────────────
        try:
            employee = Employee(
                employee_code  = fields["employee_code"].lower() ,
                name           = fields["name"],
                department     = fields["department"],
                designation    = fields["designation"],
                gmail_id       = fields["gmail_id"],
                contact_number = fields["contact_number"],
                status         = "INACTIVE",   # admin must activate
            )
            db.session.add(employee)

            role = Role(
                employee_code = fields["employee_code"],
                name          = "employee",
            )
            db.session.add(role)

            db.session.commit()
            return redirect(url_for("auth.login"))

        except Exception as exc:
            db.session.rollback()
            return render_template("Regist.html",
                                   error=f"Registration failed: {exc}")

    return render_template("Regist.html")


# ─────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        employee_code = request.form.get("employee_code").lower()
        password      = request.form.get("password", "").strip()
        role_input    = request.form.get("role", "").strip().lower()

        # ── fetch user ──────────────────────────────
        user = Employee.query.filter_by(employee_code=employee_code).first()
        if not user:
            return render_template("login.html", error="Invalid employee code.")
        access,msg = authenticate_ldap(employee_code,password)
        if not access:
            return render_template("login.html",error=msg)
        


        # ── check employee is active ─────────────────
        employee = Employee.query.get(employee_code)
        if employee and employee.status.upper() == "INACTIVE":
            return render_template("login.html",
                                   error="Your account is pending admin activation.")

        # ── verify role ──────────────────────────────
        allowed_roles = [r.name.lower() for r in Role.query.filter_by(
                             employee_code=employee_code).all()]
        if role_input not in allowed_roles:
            return render_template("login.html",
                                   error=f"Role '{role_input}' not assigned to your account.")

        # ── build JWT response ───────────────────────
        destinations = {
            "employee": "employee.dashboard",
            "admin":    "admin.dashboard",
        }
        dest = destinations.get(role_input, "auth.home")
        return _make_tokens_response(url_for(dest), employee_code, role_input)

    return render_template("login.html")


# ─────────────────────────────────────────────
#  LOGOUT
# ─────────────────────────────────────────────

@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    response = make_response(redirect(url_for("auth.login")))
    unset_jwt_cookies(response)   # clears both cookies
    return response


# ─────────────────────────────────────────────
#  GUEST REGISTRATION
# ─────────────────────────────────────────────

@auth_bp.route("/guest", methods=["GET", "POST"])
def guest():
    """
    Guest users must provide:
      - Their own name
      - Contact number
      - The employee code of a registered, active employee who is sponsoring them
    A GuestUser record is created and a short-lived guest JWT is issued.
    """
    error = None

    if request.method == "POST":
        guest_name      = request.form.get("guest_name", "").strip()
        contact_number  = request.form.get("contact_number", "").strip()
        sponsor_code    = request.form.get("sponsor_employee_code", "").strip()

        # ── validation ──────────────────────────────
        if not all([guest_name, contact_number, sponsor_code]):
            error = "All fields are required."
            return render_template("guest/guest.html", error=error)

        sponsor = Employee.query.filter_by(
            employee_code=sponsor_code.lower(),
            status="ACTIVE"
        ).first()
        if not sponsor:
            error = "Sponsor employee code not found or account is inactive."
            return render_template("guest/guest.html", error=error)

        # ── save guest record ────────────────────────
        try:
            guest_user = GuestUser(
                name           = guest_name,
                employee_code  = sponsor_code,
                contact_number = contact_number,
            )
            db.session.add(guest_user)
            db.session.commit()

            # Short-lived guest token (24 hrs), role = guest
            access_token = create_access_token(
                identity    = str(guest_user.id),
                additional_claims = {
                    "role":         "guest",
                    "guest_name":   guest_name,
                    "sponsor_code": sponsor_code,
                },
                expires_delta = timedelta(hours=24),
            )
            response = make_response(redirect(url_for("guest.dashboard")))
            set_access_cookies(response, access_token)
            return response

        except Exception as exc:
            db.session.rollback()
            error = f"Could not register guest: {exc}"

    return render_template("guest/guest.html", error=error)


# ─────────────────────────────────────────────
#  TOKEN REFRESH  (silent refresh endpoint)
# ─────────────────────────────────────────────

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """
    Called automatically when the access token expires.
    The browser sends the refresh_token_cookie and gets a new access_token_cookie.
    """
    identity = get_jwt_identity()
    role     = _get_employee_role(identity)

    new_access = create_access_token(
        identity          = identity,
        additional_claims = {"role": role},
    )
    response = make_response(jsonify({"refreshed": True}))
    set_access_cookies(response, new_access)
    return response
