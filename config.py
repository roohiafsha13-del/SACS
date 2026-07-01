"""
config.py — Application Configuration
Smart Campus Attendance System
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration shared by all environments."""

    # ── Security ──────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-fallback-secret-key')
    WTF_CSRF_ENABLED = True

    # ── Database ──────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///scas.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False          # Set True to log all SQL queries

    # ── Campus GPS Boundary ───────────────────────────────────
    CAMPUS_LAT    = float(os.environ.get('CAMPUS_LAT',    17.4492))
    CAMPUS_LON    = float(os.environ.get('CAMPUS_LON',    78.3915))
    CAMPUS_RADIUS = float(os.environ.get('CAMPUS_RADIUS_METRES', 100))  # metres

    # ── Session ───────────────────────────────────────────────
    SESSION_COOKIE_SECURE   = False   # Set True in production (HTTPS only)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds

    # ── Pagination ────────────────────────────────────────────
    RECORDS_PER_PAGE = 25


class DevelopmentConfig(Config):
 
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """Production — MySQL, debug off, secure cookies."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Testing — in-memory SQLite, CSRF disabled."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# ── Config selector ───────────────────────────────────────────
config_map = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'testing':     TestingConfig,
}

def get_config():
    env = os.environ.get('FLASK_ENV', 'development')
    return config_map.get(env, DevelopmentConfig)