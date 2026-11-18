"""Configuración de producción (FOBANDOR) — Seguridad OWASP y WhiteNoise."""
from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

SECRET_KEY = env("SECRET_KEY")

DATABASES = {
    "default": env.db("DATABASE_URL"),
}

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=["fobandor.com", "www.fobandor.com", "89.117.32.46", "localhost", "127.0.0.1"],
)

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=["https://fobandor.com", "https://www.fobandor.com"],
)

# Configuración para proxy inverso Traefik
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_REFERRER_POLICY = "same-origin"

# WhiteNoise: servicio eficiente de archivos estáticos compilados
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Blindaje de cookies y sesiones (CSRF_COOKIE_HTTPONLY=False requerido para HTMX)
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False  # Permite lectura por HTMX/JS para envío de token CSRF
CSRF_COOKIE_SAMESITE = "Lax"

# Cabeceras de seguridad HTTP (OWASP)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)  # Activar tras validar SSL

# Email en producción (SMTP configurable con fallback seguro)
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="FOBANDOR <noreply@fobandor.com>")

# Verificación de email con SMTP Google Workspace activo (ADR-021)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)
ACCOUNT_EMAIL_VERIFICATION = env("ACCOUNT_EMAIL_VERIFICATION", default="mandatory")
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = "email"
