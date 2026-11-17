#!/bin/sh
set -e

echo "==> Recolectando archivos estáticos con WhiteNoise (manifest)..."
python manage.py collectstatic --noinput

echo "==> Aplicando migraciones de base de datos..."
python manage.py migrate --noinput

echo "==> Configurando Site oficial en base de datos (www.fobandor.com)..."
python manage.py setup_production_site

echo "==> Sembrando contenido inicial y planes oficiales..."
python manage.py seed_initial_content
python manage.py seed_subscription_plans
python manage.py create_rbac_groups

if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "==> Creando superusuario inicial si no existe..."
    python manage.py createsuperuser --noinput || true
fi

PORT=8000
echo "==> Iniciando servidor Gunicorn en el puerto ${PORT}..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT} \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
