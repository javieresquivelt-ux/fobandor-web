# TASK.MD: Plan de Ejecución Atómica — Etapa 1: Cimientos, Branding y UI Base

> **Gobernanza Multi-Agente:**  
> * **Diseñado y Validado por:** Antigravity-IDE (Arquitecto de Software Senior)  
> * **Agente Ejecutor:** OpenCode (DeepSeek V4 Pro / TDD & Clean Architecture)  
> * **Estado Actual:** FASE 4: EJECUTADA Y VALIDADA por Antigravity-IDE. Criterio de Aceptación de la Etapa 1 CUMPLIDO. Listo para inicio de Etapa 2.

---

## 1. Resumen y Alcance de la Etapa 1
Establecer los cimientos limpios de la plataforma FOBANDOR en `localhost` bajo estándar 12-Factor en Linux Ubuntu:
1. Instalación de Docker Engine + Compose en el host (prerrequisito para PostgreSQL 16 local).
2. Inicialización de entorno virtual Python 3.12+ (runtime 3.14.4) y Django 5.2 LTS desacoplado (`config/settings/`).
3. Definición del modelo `CustomUser` (`fobandor.users.models.User`) con `AUTH_USER_MODEL = 'users.User'` y `UserManager` personalizado, antes de la migración inicial.
4. Orquestación de PostgreSQL 16 con `docker-compose.yml` y configuración `DATABASE_URL` (fallback SQLite de emergencia controlado).
5. Pipeline de Frontend **Zero External CDN**: Fuentes **Montserrat WOFF2** locales, scripts locales de **HTMX 2.x** y **Alpine.js 3.x** en `static/js/vendor/` y compilación local de Tailwind CSS con la paleta oficial de FOBANDOR.
6. Procesamiento del isotipo `instructions/logo-fobandor.jpg` para generar favicons e iconos multiplataforma con Pillow.
7. Plantillas DTL modulares con Dark/Light mode persistente en `localStorage` vía Alpine.js y soporte i18n nativo (Español por defecto / Inglés) mediante `LocaleMiddleware` e `i18n_patterns`.
8. Maquetación del Hero Section y showcase de las 4 líneas de negocio en `http://localhost:8000`.

---

## 2. Árbol de Archivos Objetivo (Estructura Limpia)

```text
fobandor/
├── .env.example
├── .env
├── .gitignore
├── docker-compose.yml
├── manage.py
├── package.json
├── tailwind.config.js
├── requirements/
│   ├── base.txt
│   └── local.txt
├── config/
│   ├── __init__.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── settings/
│       ├── __init__.py
│       ├── base.py
│       ├── local.py
│       └── production.py
├── fobandor/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── urls.py
│   │   └── views.py
│   └── users/
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── models.py
│       └── tests/
├── static/
│   ├── css/
│   │   ├── input.css
│   │   └── output.css
│   ├── fonts/
│   │   └── montserrat/
│   ├── js/
│   │   └── vendor/
│   │       ├── htmx.min.js
│   │       └── alpine.min.js
│   └── images/
│       └── favicons/
├── media/
└── templates/
    ├── base.html
    ├── partials/
    │   ├── navbar.html
    │   └── footer.html
    └── pages/
        └── home.html
```

---

## 3. Desglose de Tareas Atómicas para OpenCode (DeepSeek V4 Pro)

### Tarea 1.0: Prerrequisito — Instalar Docker Engine y Docker Compose
- [x] Instalar Docker Engine + Compose plugin en Ubuntu:
  ```bash
  sudo apt-get update
  sudo apt-get install -y ca-certificates curl
  sudo install -m 0755 -d /etc/apt/keyrings
  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  sudo chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  sudo systemctl enable --now docker
  sudo usermod -aG docker "$USER"
  ```
- [x] Verificar: `docker compose version` y `docker info` (cerrar/reabrir sesión para que aplique el grupo `docker`).

### Tarea 1.1: Entorno Virtual, Gitignore y Dependencias Modulares
- [x] Crear `.gitignore` en la raíz (ignorar `.venv/`, `*.pyc`, `__pycache__/`, `db.sqlite3`, `.env`, `node_modules/`, `media/`, `staticfiles/`, `static/css/output.css`).
- [x] Definir `requirements/base.txt`:
  ```text
  Django>=5.2,<5.3
  django-environ>=0.11.2
  psycopg[binary]>=3.2.3
  Pillow>=10.4.0
  ```
- [x] Definir `requirements/local.txt`:
  ```text
  -r base.txt
  pytest>=8.3.0
  pytest-django>=4.9.0
  flake8>=7.1.0
  ```
- [x] Crear `.env.example` y `.env` con variables mínimas:
  ```env
  DEBUG=True
  SECRET_KEY=django-insecure-fobandor-local-dev-key-change-in-prod  # ¡cambiar en producción!
  ALLOWED_HOSTS=localhost,127.0.0.1
  TIME_ZONE=America/New_York
  LANGUAGE_CODE=es
  DATABASE_URL=postgres://fobandor_user:fobandor_secret@localhost:5432/fobandor_db
  ```

### Tarea 1.2: Configuración 12-Factor y Núcleo Django
- [x] Crear `manage.py` apuntando a `DJANGO_SETTINGS_MODULE=config.settings.local`.
- [x] Crear `config/settings/base.py`:
  - Leer entorno con `environ.Env()` y cargar archivo: `environ.Env.read_env(BASE_DIR / ".env")`.
  - Definir `BASE_DIR = Path(__file__).resolve().parent.parent.parent`.
  - `INSTALLED_APPS`: apps nativas + `'fobandor.users.apps.UsersConfig'`, `'fobandor.core.apps.CoreConfig'`.
  - `MIDDLEWARE`: incluir **`django.middleware.locale.LocaleMiddleware`** entre `SessionMiddleware` y `CommonMiddleware`.
  - Configurar `AUTH_USER_MODEL = 'users.User'`.
  - Configurar internacionalización: `USE_I18N = True`, `USE_TZ = True`, `LANGUAGE_CODE = env("LANGUAGE_CODE", default="es")`, `TIME_ZONE = env("TIME_ZONE", default="America/New_York")`, `LANGUAGES = [('es', 'Español'), ('en', 'English')]`.
  - Configurar directorios: `STATIC_URL = '/static/'`, `STATICFILES_DIRS = [BASE_DIR / 'static']`, `STATIC_ROOT = BASE_DIR / 'staticfiles'`, `MEDIA_URL = '/media/'`, `MEDIA_ROOT = BASE_DIR / 'media'`.
  - Configurar DTL: `DIRS = [BASE_DIR / 'templates']`.
- [x] Crear `config/settings/local.py`:
  - `from .base import *`
  - Conexión a base de datos con fallback SQLite de emergencia:
    ```python
    DATABASES = {
        'default': env.db('DATABASE_URL', default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
    }
    ```
  - `EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"` (para desarrollo).
- [x] Crear `config/settings/production.py` como stub:
  ```python
  from .base import *  # noqa
  ```
- [x] Crear `config/urls.py` con `i18n_patterns`, `set_language` (`/i18n/setlang/`), admin y core:
  ```python
  from django.conf.urls.i18n import i18n_patterns
  from django.contrib import admin
  from django.urls import path, include

  urlpatterns = [
      path("i18n/", include("django.conf.urls.i18n")),
  ]

  urlpatterns += i18n_patterns(
      path("admin/", admin.site.urls),
      path("", include("fobandor.core.urls")),
  )
  ```

### Tarea 1.3: Modelo CustomUser Inicial (con UserManager obligatorio)
- [x] Crear `fobandor/users/apps.py` (`name = 'fobandor.users'`, `label = 'users'`).
- [x] Implementar `fobandor/users/models.py`:
  ```python
  from django.contrib.auth.models import AbstractUser, BaseUserManager
  from django.core.validators import RegexValidator
  from django.db import models


  class UserManager(BaseUserManager):
      use_in_migrations = True

      def _create_user(self, email, password, **extra_fields):
          if not email:
              raise ValueError("El correo electrónico es obligatorio.")
          email = self.normalize_email(email)
          user = self.model(email=email, **extra_fields)
          user.set_password(password)
          user.save(using=self._db)
          return user

      def create_user(self, email, password=None, **extra_fields):
          extra_fields.setdefault("is_staff", False)
          extra_fields.setdefault("is_superuser", False)
          return self._create_user(email, password, **extra_fields)

      def create_superuser(self, email, password=None, **extra_fields):
          extra_fields.setdefault("is_staff", True)
          extra_fields.setdefault("is_superuser", True)
          if extra_fields.get("is_staff") is not True:
              raise ValueError("El superusuario debe tener is_staff=True.")
          if extra_fields.get("is_superuser") is not True:
              raise ValueError("El superusuario debe tener is_superuser=True.")
          return self._create_user(email, password, **extra_fields)


  class User(AbstractUser):
      username = None
      email = models.EmailField('Correo Electrónico', unique=True)
      phone = models.CharField(
          'Teléfono', max_length=16, blank=True,
          validators=[RegexValidator(regex=r'^\+[1-9]\d{1,14}$',
                      message='Formato E.164 requerido (ej. +14075551234).')],
      )
      preferred_language = models.CharField(
          max_length=5, choices=[('es', 'Español'), ('en', 'English')], default='es')
      is_email_verified = models.BooleanField(default=False)
      company_name = models.CharField('Empresa / Marca', max_length=150, blank=True)
      social_handle = models.CharField('Red Social / Arroba', max_length=100, blank=True)
      tax_id = models.CharField('Tax ID / EIN / NIF', max_length=50, blank=True)
      billing_address_line1 = models.CharField('Dirección Línea 1', max_length=255, blank=True)
      billing_address_line2 = models.CharField('Dirección Línea 2', max_length=255, blank=True)
      billing_city = models.CharField('Ciudad', max_length=100, blank=True)
      billing_state = models.CharField('Estado / Provincia', max_length=100, blank=True)
      billing_postal_code = models.CharField('Código Postal', max_length=20, blank=True)
      billing_country = models.CharField(
          'País (ISO-2)', max_length=2, blank=True,
          validators=[RegexValidator(regex=r'^[A-Z]{2}$',
                      message='Código ISO 3166-1 alpha-2 (ej. US).')],
      )
      stripe_customer_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
      terms_accepted_at = models.DateTimeField(null=True, blank=True)
      marketing_consent = models.BooleanField(default=False)

      objects = UserManager()

      USERNAME_FIELD = 'email'
      REQUIRED_FIELDS = []

      class Meta:
          verbose_name = 'Usuario'
          verbose_name_plural = 'Usuarios'

      def __str__(self):
          return self.email
  ```
- [x] Registrar modelo en `fobandor/users/admin.py` con `UserAdmin` estándar (compatible con `USERNAME_FIELD = 'email'`).

### Tarea 1.4: Orquestación Docker para PostgreSQL 16
- [x] Crear `docker-compose.yml`:
  ```yaml
  services:
    db:
      image: postgres:16-alpine
      container_name: fobandor_postgres
      environment:
        POSTGRES_DB: ${POSTGRES_DB:-fobandor_db}
        POSTGRES_USER: ${POSTGRES_USER:-fobandor_user}
        POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-fobandor_secret}
      ports:
        - "5432:5432"
      volumes:
        - postgres_data:/var/lib/postgresql/data
      restart: unless-stopped
      healthcheck:
        test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-fobandor_user} -d ${POSTGRES_DB:-fobandor_db}"]
        interval: 5s
        timeout: 5s
        retries: 5

  volumes:
    postgres_data:
  ```
- [x] Levantar el contenedor: `docker compose up -d` y verificar salud (`docker compose ps`).
- [x] Ejecutar migraciones iniciales: `python manage.py makemigrations users && python manage.py migrate`.

### Tarea 1.5: Assets Locales ("Zero External CDN") y Tailwind CSS
- [x] Descargar fuentes **Montserrat** en formato `.woff2` (Regular 400, Medium 500, SemiBold 600, Bold 700) en `static/fonts/montserrat/`.
- [x] Descargar `htmx.min.js` (2.x) y `alpine.min.js` (3.x) en `static/js/vendor/`.
- [x] Configurar `package.json` con Tailwind CSS:
  ```json
  {
    "name": "fobandor",
    "private": true,
    "scripts": {
      "build:css": "npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --minify",
      "watch:css": "npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --watch"
    },
    "devDependencies": {
      "tailwindcss": "^3.4.14"
    }
  }
  ```
- [x] Configurar `tailwind.config.js`:
  ```javascript
  module.exports = {
    darkMode: 'class',
    content: [
      './templates/**/*.html',
      './fobandor/**/*.py',
    ],
    theme: {
      extend: {
        colors: {
          'fobandor-orange': '#FF6A00',
          'fobandor-blue': '#2563EB',
          'fobandor-cyan': '#06B6D4',
          'fobandor-dark': '#0D1117',
          'fobandor-light': '#F3F4F6',
        },
        fontFamily: {
          montserrat: ['Montserrat', 'sans-serif'],
        },
      },
    },
    plugins: [],
  };
  ```
- [x] Crear `static/css/input.css` con las directivas `@font-face` locales y directivas `@tailwind base; @tailwind components; @tailwind utilities;`.
- [x] Compilar CSS inicial: `npm run build:css`.

### Tarea 1.6: Procesamiento de Favicons e Iconos Corporativos
- [x] Script Python con `Pillow` para procesar `instructions/logo-fobandor.jpg` y exportar a `static/images/favicons/`:
  - `favicon.ico` (16x16, 32x32, 48x48)
  - `favicon-16x16.png`
  - `favicon-32x32.png`
  - `apple-touch-icon.png` (180x180)
  - `site.webmanifest`

### Tarea 1.7: Plantillas Base con Dark/Light Mode e i18n
- [x] Implementar `templates/base.html`:
  - Inclusión de favicons, `output.css`, `static/js/vendor/htmx.min.js`, `static/js/vendor/alpine.min.js`.
  - Script inicial Alpine.js para aplicar clase `dark` desde `localStorage` sin parpadeo.
- [x] Implementar `templates/partials/navbar.html`:
  - Logotipo oficial con "F" estilizada.
  - Enlaces de navegación: Inicio, Servicios, Proyectos, Precios, Nosotros, Contacto.
  - Switcher de idioma (ES / EN) mediante llamada a `set_language`.
  - Botón toggle de Dark/Light mode con iconos sol/luna gestionado con Alpine.js.
  - Botón CTA *"Comenzar"* hacia el catálogo.
- [x] Implementar `templates/partials/footer.html`:
  - Redes sociales oficiales (`fobandor.ai` en Instagram, TikTok, X, YouTube, Facebook).
  - Indicación de Orlando, Florida, EE.UU.

### Tarea 1.8: Home Hero y Showcase de las 4 Líneas de Negocio
- [x] Crear aplicación `fobandor.core` con vista `home_view`.
- [x] Maquetar `templates/pages/home.html`:
  - **Hero Section:** Titular *"Ideas, código y creatividad impulsados por IA"*, eslogan *"BUILD. ADVERTISE. ENTERTAIN. WITH AI."*, badges con acentos neón `#FF6A00` y `#2563EB`, botón CTA *"Comencemos"*.
  - **Grid de las 4 Líneas de Negocio:**
    1. *Desarrollo Web con IA*
    2. *Desarrollo de Apps con IA*
    3. *Publicidad con IA*
    4. *Fobandor Studios (Producción Audiovisual con IA)*

### Tarea 1.9: Verificación de Aceptación Técnica
- [x] Ejecutar chequeo de Django: `python manage.py check`.
- [x] Verificar el `UserManager`: `python manage.py createsuperuser` (usando un email como login).
- [x] Verificar migraciones pendientes: `python manage.py makemigrations --check --dry-run`.
- [x] Levantar servidor local: `python manage.py runserver 8000`.
- [x] Verificar en navegador:
  - Carga correcta de `http://localhost:8000/`.
  - Cero dependencias externas en la pestaña Network (todo servido desde localhost).
  - Cambio fluido de Dark Mode a Light Mode y persistencia tras F5.
  - Cambio de idioma ES / EN.
  - Carga de favicons y favicon 32x32.

---

## 4. Planificación de Próximas Etapas (Roadmap Anticipado)

### Etapa 2 — Identidad, RBAC y Backoffice CMS
- Modelos dinámicos del CMS (4 líneas de servicio, proyectos, nosotros, enlaces oficiales de RRSS).
- Sistema RBAC interno para staff (`is_staff = True`: Superadmin, Editor de Contenido, Operador de Entregas).
- Backoffice modular en `/backoffice/` con DTL + HTMX + Tailwind.

### Etapa 3 — Registro de Clientes, Autenticación Gmail, Stripe Checkout y SLA 7 Días
- Flujo de registro de clientes con autenticación híbrida:
  - Formulario estándar de Email + Contraseña segura con verificación por correo.
  - **Social Login con Cuentas Gmail (Google OAuth 2.0 / `django-allauth`):** Acceso en 1 clic con verificación automática inmediata (`is_email_verified = True`).
  - Formulario de Onboarding AVS (dirección completa y teléfono E.164 para Stripe).
  - *(Nota de Arquitectura: Google Workspace SSO para dominios `@fobandor.com` queda documentado pero fuera del plan de ejecución actual)*.
- Integración de Stripe Checkout en modo suscripción (3 planes mensuales + cupones de descuento).
  - **Pendiente de definición (requiere aprobación de negocio):** catálogo exacto de los 3 planes (nombre, precio, features) y mapeo de `FulfillmentOrder.order_type` a las 4 líneas de servicio.
- Webhook listener criptográfico (`/stripe/webhook/`) y motor de órdenes `FulfillmentOrder` (SLA 7 días).
  - **Pendiente de definición:** mecanismo de detección de `VENCIDA` (recomendación ADR-009: `management command` + cron en VPS).
- Portal de Autoservicio del Cliente (`/mi-cuenta/`) y acceso al Stripe Customer Portal.

### Etapa 4 — SEO Técnico, Auditoría OWASP y Empaquetado Producción
- Metadatos dinámicos, Open Graph, sitemap bilingüe y `robots.txt`.
- Suite de pruebas automatizadas con `pytest` y `pytest-django`.
- Auditoría OWASP y verificación `check --deploy`.
- Empaquetado Docker para VPS (Hostinger u otro proveedor agnóstico).
