import os
from datetime import timedelta
from dotenv import load_dotenv
 
load_dotenv()
from dotenv import find_dotenv
print("ENV FILE:", find_dotenv())
print("DATABASE_URL =", os.getenv("DATABASE_URL"))
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY is not set!")
 
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL is not set!")
    
 
    SQLALCHEMY_TRACK_MODIFICATIONS = False
 
    # ── JWT ─────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY            = os.getenv("JWT_SECRET_KEY", "super-secret-jwt-key")
    JWT_TOKEN_LOCATION        = ["cookies"]
    JWT_ACCESS_COOKIE_NAME    = "access_token_cookie"
    JWT_REFRESH_COOKIE_NAME   = "refresh_token_cookie"
    JWT_ACCESS_CSRF_HEADER_NAME = "X-CSRF-TOKEN"
    JWT_CSRF_IN_COOKIES         = True
    JWT_CSRF_CHECK_FORM         = True          # ← add this
    JWT_ACCESS_CSRF_FIELD_NAME  = "csrf_token"
    JWT_COOKIE_CSRF_PROTECT     = True
    JWT_COOKIE_SECURE           = os.getenv("FLASK_ENV") == "production"
    JWT_COOKIE_SAMESITE         = "Lax"
    # Token lifetimes
    JWT_ACCESS_TOKEN_EXPIRES  = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
 
    #LDAP SETTINGS
    LDAP_USER = os.getenv("LDAP_USER")
    LDAP_PASS = os.getenv("LDAP_PASS")
    LDAP_SERVER = os.getenv("LDAP_SERVER")
    LDAP_PORT = os.getenv("LDAP_PORT")
    AD_DOMAIN = os.getenv('AD_DOMAIN')
    SEARCH_BASE = os.getenv('SEARCH_BASE')
    print (os.getenv("LDAP_USER"))
    print (os.getenv("LDAP_PASS"))
    print (os.getenv("LDAP_SERVER"))
    print (os.getenv("LDAP_PORT"))
    print (os.getenv("AD_DOMAIN"))
    print (os.getenv("SEARCH_BASE"))
