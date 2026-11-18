"""
Django settings for tracks4u project.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
if DEBUG:
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "django-insecure-3v=056ulzjhnly3-fn4_41s^gh^n#!qcu77%mvinm#t1j!#(-c",
    )
else:
    SECRET_KEY = os.environ["SECRET_KEY"]

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]
CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "http://localhost").split(",")
    if o.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "users",
    "tracks",
    "playlists",
    "payment",
    "telemetry",
    "rest_framework",
    "charts",
    "sistema_client",
]

AUTH_USER_MODEL = "users.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "300/min",
        "user": "600/min",
    },
}

ROOT_URLCONF = "tracks4u.urls"
LOGIN_URL = "/users/login/"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "tracks4u.wsgi.application"

# Database — Amazon RDS PostgreSQL
_use_admin = os.environ.get("DB_USE_ADMIN") == "1" and bool(
    os.environ.get("DB_ADMIN_USER", "").strip()
)
_db_user = (
    os.environ.get("DB_ADMIN_USER", "").strip()
    if _use_admin
    else os.environ.get("DB_USER", "tracks4u_app")
)
_db_password = (
    os.environ.get("DB_ADMIN_PASSWORD", "")
    if _use_admin
    else os.environ.get("DB_PASSWORD", "")
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "tracks4u"),
        "USER": _db_user,
        "PASSWORD": _db_password,
        "HOST": os.environ.get(
            "DB_HOST",
            "tracks4u-postgres-dev.c4qkjciamuny.us-east-1.rds.amazonaws.com",
        ),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "sslmode": os.environ.get("DB_SSLMODE", "require"),
            "connect_timeout": int(os.environ.get("DB_CONNECT_TIMEOUT", "5")),
        },
    }
}

SCHEMA_SQL_PATH = os.environ.get("SCHEMA_SQL_PATH") or str(
    BASE_DIR.parent / "database" / "schema.sql"
)

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
USE_I18N = True
LANGUAGE_CODE = "es"
LANGUAGES = [("es", "Español"), ("en", "English")]
LOCALE_PATHS = [os.path.join(BASE_DIR, "locale")]

TIME_ZONE = "UTC"
USE_TZ = True

from celery.schedules import crontab

# Celery
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = "America/Bogota"
CELERY_ENABLE_UTC = True
CELERY_BEAT_SCHEDULE = {
    "purge-acked-telemetry": {
        "task": "telemetry.purge_acked_events",
        "schedule": crontab(hour=3, minute=0),
    },
}

# Telemetría
TELEMETRY_DRAIN_TOKEN = os.environ.get("TELEMETRY_DRAIN_TOKEN", "")
TELEMETRY_SETTLE_SECONDS = int(os.environ.get("TELEMETRY_SETTLE_SECONDS", "5"))
TELEMETRY_RETENTION_DAYS = int(os.environ.get("TELEMETRY_RETENTION_DAYS", "7"))
TELEMETRY_DRAIN_MAX_LIMIT = int(os.environ.get("TELEMETRY_DRAIN_MAX_LIMIT", "1000"))

# Static files & S3 Media Storage
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

STORAGES = {
    "default": {"BACKEND": "storages.backends.s3.S3Storage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "us-east-1")
AWS_QUERYSTRING_AUTH = True
AWS_QUERYSTRING_EXPIRE = 3600
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
if os.environ.get("AWS_ACCESS_KEY_ID", "").strip():
    AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"].strip()
if os.environ.get("AWS_SECRET_ACCESS_KEY", "").strip():
    AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"].strip()

# Notificaciones
NOTIFICATION_MODE = os.environ.get("NOTIFICATION_MODE", "MOCK")

if NOTIFICATION_MODE == "REAL":
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "sandbox.smtp.mailtrap.io"
    EMAIL_PORT = 2525
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.environ.get("MAILTRAP_USER", "tu_mailtrap_user")
    EMAIL_HOST_PASSWORD = os.environ.get("MAILTRAP_PASSWORD", "tu_mailtrap_password")
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_FROM_EMAIL = "doriangui63@gmail.com"
ADMIN_EMAIL = "dainishikado@gmail.com"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
