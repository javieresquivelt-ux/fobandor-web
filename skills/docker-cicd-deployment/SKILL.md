---
name: docker-cicd-deployment
description: >-
  Guía de CI/CD y despliegue continuo con Docker Multi-Etapa, EasyPanel, Docker Swarm
  y Traefik sobre Hostinger KVM VPS. Incluye el flujo GitHub → EasyPanel → Swarm,
  el entrypoint.sh de auto-provisionamiento, configuración de Traefik SSL, y todos
  los incidentes y hotfixes de producción documentados en FOBANDOR.
  Usar cuando se realiza un despliegue, se configura el entorno de producción,
  se actualiza la infraestructura o se diagnostica un incidente de VPS.
---

# Docker CI/CD Deployment — Lecciones Aprendidas FOBANDOR

## Arquitectura de Despliegue

```
git push origin main
  → EasyPanel (GitHub Webhook Pull)
    → docker build (Multi-Stage Dockerfile)
      → entrypoint.sh (collectstatic → migrate → seeders → gunicorn)
        → Docker Swarm Service (rolling update)
          ← Traefik Edge Proxy (SSL Let's Encrypt, fobandor.com)
            ← Clientes HTTPS
```

---

## Dockerfile Multi-Etapa (Producción)

```dockerfile
# Stage 1: Compilar Tailwind CSS sin inflar imagen final
FROM node:22-alpine AS frontend-builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci                           # ← npm ci, NO npm install (determinista)
COPY tailwind.config.js ./
COPY templates/ ./templates/
COPY fobandor/ ./fobandor/
COPY static/css/input.css ./static/css/input.css
RUN npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --minify

# Stage 2: Runtime Python de producción
FROM python:3.14-slim AS runner
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    PORT=8000                        # ← FIJAR PORT aquí (ver incidente 502)

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/base.txt

COPY . .
COPY --from=frontend-builder /app/static/css/output.css /app/static/css/output.css

RUN useradd -m -u 1000 django && chown -R django:django /app
USER django                          # ← Usuario no-root (OWASP)

EXPOSE 8000
ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
```

---

## Incidente 502 Bad Gateway — EasyPanel PORT

> [!CAUTION]
> EasyPanel inyecta `PORT=80` en el entorno del contenedor por defecto.
> Gunicorn escucha en el PORT env var → Traefik dirige tráfico a :8000 → 502.

**Solución:** Fijar `PORT=8000` **explícitamente** en dos lugares:
1. `ENV PORT=8000` en el `Dockerfile`.
2. En `entrypoint.sh` antes de lanzar Gunicorn:

```bash
# entrypoint.sh
PORT=8000
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT} \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
```

---

## entrypoint.sh — Auto-Provisionamiento Idempotente

```bash
#!/bin/sh
set -e

echo "==> Recolectando archivos estáticos con WhiteNoise (manifest)..."
python manage.py collectstatic --noinput

echo "==> Aplicando migraciones de base de datos..."
python manage.py migrate --noinput

echo "==> Configurando Site oficial en base de datos..."
python manage.py setup_production_site

echo "==> Sembrando contenido inicial y planes oficiales..."
python manage.py seed_initial_content
python manage.py seed_subscription_plans
python manage.py create_rbac_groups

echo "==> Reconciliando órdenes SLA huérfanas..."
python manage.py reconcile_fulfillment_orders || true   # ← || true: no abortar ante 0 órdenes

if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "==> Creando superusuario inicial si no existe..."
    python manage.py createsuperuser --noinput || true  # ← || true: idempotente
fi

PORT=8000
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT} \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
```

**Principio clave:** Todos los seeders deben ser **idempotentes** (`get_or_create`, `update_or_create`).

---

## WhiteNoise — Estáticos sin Nginx Adicional

```python
# settings/base.py
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    }
}
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← Inmediatamente después de Security
    # ...
]
```

**Beneficios validados:**
- Compresión Brotli + Gzip automática.
- Hashes inmutables (`output.abc123.css`) → cache busting perfecto.
- Sin contenedor Nginx adicional (ahorra ~100 MB de RAM en VPS).

---

## Traefik — Configuración de Proxy Inverso

```python
# settings/production.py — Headers para proxy inverso Traefik
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
SECURE_SSL_REDIRECT = True
```

**DNS requerido:**
- Registro A: `@` → `89.117.32.46` (IP del VPS)
- Registro CNAME: `www` → `fobandor.com`

---

## EasyPanel — Configuración del Servicio App

```
Source:    GitHub Repo → rama main → Dockerfile /Dockerfile
Port:      8000
Domains:   fobandor.com, www.fobandor.com → :8000
Mounts:    fobandor_media → /app/media/     ← Volumen persistente para entregables
```

**Variables de Entorno en Swarm (obligatorias):**
```bash
SECRET_KEY=...
DATABASE_URL=postgresql://user:pass@postgres:5432/fobandor_db
ALLOWED_HOSTS=fobandor.com,www.fobandor.com
CSRF_TRUSTED_ORIGINS=https://fobandor.com,https://www.fobandor.com
SITE_DOMAIN=www.fobandor.com
PORT=8000
# SMTP Google Workspace
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=administrator@fobandor.com
EMAIL_HOST_PASSWORD=...             # App Password de 16 caracteres
DEFAULT_FROM_EMAIL=FOBANDOR <admin@fobandor.com>
# Stripe
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
# Formspree
FORMSPREE_ENDPOINT=https://formspree.io/f/mqpqqggk
```

> [!IMPORTANT]
> Las variables de entorno de SMTP deben inyectarse en el Swarm Service, **no** solo en las
> Environment Variables del proyecto en EasyPanel. Verificar con:
> `docker service inspect fobandor_web` → buscar `Env`.

---

## Incidente PostgreSQL — Credencial Autogenerada EasyPanel

> [!WARNING]
> EasyPanel genera una contraseña aleatoria para el DB service distinta a la que
> se configura en DATABASE_URL. Sincronizar manualmente:

```sql
ALTER USER fobandor_user WITH PASSWORD 'nueva_password';
```

Luego actualizar `DATABASE_URL` en las env vars del Swarm.

---

## Incidente Google OAuth — Allauth Auto-Connect

**Síntoma:** "An account already exists with this email address" al login OAuth.

**Causa:** Allauth no vincula automáticamente cuentas sociales a usuarios locales por defecto.

**Solución:**
```python
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_LOGIN_ON_GET = True
```

---

## Checklist de Despliegue

- [ ] Verificar `PORT=8000` en Dockerfile y entrypoint.sh.
- [ ] Confirmar variables SMTP inyectadas en Swarm (`docker service inspect fobandor_web`).
- [ ] Verificar volumen `fobandor_media` montado en `/app/media/`.
- [ ] Confirmar webhook Stripe apuntando al dominio HTTPS productivo.
- [ ] Comprobar certificados Let's Encrypt activos (`https://fobandor.com`).
- [ ] Ejecutar `pytest` localmente antes de cada `git push`.
- [ ] Verificar `flake8 config fobandor scripts` sin errores.
- [ ] Correr `docker service ps fobandor_web` tras el deploy para confirmar convergencia.

## Referencias

- [memory.md §12-14 — Etapa 4 Producción e Incidentes](../../memory.md)
- [Dockerfile](../../Dockerfile)
- [entrypoint.sh](../../entrypoint.sh)
- [spec.md §8 — CI/CD Methodology](../../spec.md)
