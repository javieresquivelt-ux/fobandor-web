# Etapa 1: Compilación de Tailwind CSS
FROM node:22-alpine AS frontend-builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY tailwind.config.js ./
COPY templates/ ./templates/
COPY fobandor/ ./fobandor/
COPY static/css/input.css ./static/css/input.css
RUN npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --minify

# Etapa 2: Runtime de Python y Django
FROM python:3.14-slim AS runner
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    PORT=8000

WORKDIR /app

# Instalar dependencias del sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/base.txt

# Copiar código fuente
COPY . .

# Copiar el CSS compilado desde la etapa 1
COPY --from=frontend-builder /app/static/css/output.css /app/static/css/output.css

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 django && \
    chown -R django:django /app
USER django

EXPOSE 8000

ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
