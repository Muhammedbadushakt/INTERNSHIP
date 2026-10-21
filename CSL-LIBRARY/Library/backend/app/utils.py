from functools import wraps
from flask import redirect, url_for, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
from app.config import Config

def _jwt_guard(required_role: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                # looks for the cookie named 'access_token_cookie'
                verify_jwt_in_request(locations=["cookies"])
            except Exception:
                # token missing, expired, or invalid → back to login
                return redirect(url_for("auth.login"))

            claims = get_jwt()
            role   = claims.get("role", "")

            # admin can access employee routes too (superset)
            allowed = (role == required_role) or (role == "admin")
            if not allowed:
                return redirect(url_for("auth.login"))

            # make identity & claims available as g.current_user
            g.current_user = {
                "employee_code": get_jwt_identity(),
                "role":          role,
                "claims":        claims,
            }
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ── public decorators ────────────────────────────────────────────────────────

employee_required = _jwt_guard("employee")
admin_required    = _jwt_guard("admin")


def guest_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request(locations=["cookies"])
        except Exception:
            return redirect(url_for("auth.guest"))

        claims = get_jwt()
        if claims.get("role") != "guest":
            return redirect(url_for("auth.guest"))

        g.current_user = {
            "guest_id":     get_jwt_identity(),
            "guest_name":   claims.get("guest_name"),
            "sponsor_code": claims.get("sponsor_code"),
            "role":         "guest",
        }
        return fn(*args, **kwargs)
    return wrapper


def get_current_user():
    """
    Helper to read g.current_user inside a view or template context processor.

    In a route:
        @employee_required
        def my_view():
            user = get_current_user()
            print(user["employee_code"])

    In __init__.py register a context processor so every template gets it:
        @app.context_processor
        def inject_user():
            from app.utils.decorators import get_current_user
            return {"current_user": get_current_user()}
    """
    from flask import g
    return getattr(g, "current_user", None)

from ldap3 import Server, Connection, Tls
import ssl
def get_ldap_connection():
    tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)
    server = Server(Config.LDAP_SERVER, port=636,use_ssl=True,tls=tls_config)
    return Connection(server,
                        user="cn=SERVICE ACCOUNT DSK,ou=SERVICE-ACCOUNTS,dc=design,dc=cochinshipyard,dc=in",
                        password="Est@te2026csl",
                        auto_bind=True, raise_exceptions=False)
