"""Configuración de desarrollo local (FOBANDOR)."""
from .base import *  # noqa: F401,F403
from .base import BASE_DIR, env, ALLOWED_HOSTS

DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Soporte para Django Test Client y Pytest
ALLOWED_HOSTS = list(ALLOWED_HOSTS) + ["testserver"] if "testserver" not in ALLOWED_HOSTS else ALLOWED_HOSTS
