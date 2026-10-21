from flask import Flask, request, make_response
from .extension import db,jwt
from flask_jwt_extended import (
    create_access_token,
    set_access_cookies,
    verify_jwt_in_request,
    get_jwt,
    get_jwt_identity,
    get_csrf_token,
)
from flask_migrate import Migrate
migrate = Migrate()
print("LOADED:", __file__)
def create_app():
    app = Flask(
        __name__,
        template_folder="../../frontend/templates",
        static_folder="../../frontend/storage",
        static_url_path="/storage"
    )
    migrate.init_app(app, db)
    from .config import Config
    app.config.from_object(Config)
    from .config import Config
    app.config.from_object(Config)

    print("CONFIG URI =", app.config.get("SQLALCHEMY_DATABASE_URI"))
    db.init_app(app)
    jwt.init_app(app)

    # IMPORTANT: import models before db.create_all()
    from app import models

    with app.app_context():
        db.create_all()

    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.employee import employee_bp
    from app.routes.guest import guest_bp

    from app.routes.superadmin import super_admin_bp
    app.register_blueprint(super_admin_bp)


    app.register_blueprint(employee_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(guest_bp)

    @app.context_processor
    def inject_current_user():
        try:
            verify_jwt_in_request(locations=["cookies"], optional=True)
            claims = get_jwt()
            return {
                "current_user": {
                    "employee_code": get_jwt_identity(),
                    "role": claims.get("role"),
                }
            }
        except Exception:
            return {"current_user": None}

    @app.context_processor
    def inject_csrf_token():
        """Injects csrf_token variable into every template for use in POST forms."""
        token_cookie = request.cookies.get("access_token_cookie")
        if token_cookie:
            try:
                return {"csrf_token": get_csrf_token(token_cookie)}
            except Exception:
                pass
        return {"csrf_token": ""}

    @app.after_request
    def auto_refresh(response):
        try:
            verify_jwt_in_request(locations=["cookies"], optional=True)
            claims = get_jwt()

            from datetime import datetime, timezone

            exp = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
            now = datetime.now(tz=timezone.utc)

            if (exp - now).total_seconds() < 600:
                identity = get_jwt_identity()
                new_token = create_access_token(
                    identity=identity,
                    additional_claims={"role": claims.get("role")},
                )
                set_access_cookies(response, new_token)

        except Exception:
            pass

        return response

    return app