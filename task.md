# TASK.MD: Plan de Ejecución Atómica y Hoja de Ruta — FOBANDOR

> **Gobernanza Multi-Agente:**  
> * **Diseñado y Validado por:** Antigravity-IDE (Arquitecto de Software Senior)  
> * **Agente Ejecutor:** OpenCode (DeepSeek V4 Pro / TDD & Clean Architecture)  
> * **Estado Actual:** FASE 3: APROBAR (Tarea 4.8 — Integración de Formspree Real para Diagnóstico Comercial en /precios/). En espera de visto bueno del Desarrollador Líder.

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

## 4. Etapa 2 — Identidad, RBAC y Backoffice CMS

> **Gobernanza Multi-Agente:**
> * **Diseñado y Validado por:** Antigravity-IDE (Arquitecto de Software Senior)
> * **Agente Ejecutor:** OpenCode (DeepSeek V4 Pro / TDD & Clean Architecture)
> * **Estado Actual:** FASE 4: EJECUTADA Y VALIDADA por Antigravity-IDE. Criterio de Aceptación de la Etapa 2 CUMPLIDO. Listo para inicio de Etapa 3.

---

### Resumen de Alcance (Etapa 2)

1. Nueva aplicación `fobandor.cms` con modelos bilingües (ES/EN) para contenido dinámico.
2. Sistema RBAC con grupos Django (`Content_Editors`, `Fulfillment_Operators`).
3. Backoffice en `/backoffice/` protegido con `StaffRequiredMixin` (DTL + HTMX + Tailwind).
4. Integración de datos CMS en la Home pública (servicios y redes sociales dinámicos).
5. Suite de pruebas automatizadas y verificación de aceptación técnica.

---

### Árbol de Archivos Objetivo (Etapa 2 — Incremental)

```text
fobandor/
├── fobandor/
│   ├── cms/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── migrations/
│   │   │   └── 0001_initial.py
│   │   ├── management/
│   │   │   └── commands/
│   │   │       └── seed_initial_content.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_models.py
│   └── backoffice/
│       ├── __init__.py
│       ├── apps.py
│       ├── mixins.py
│       ├── urls.py
│       ├── views.py
│       └── tests/
│           ├── __init__.py
│           └── test_views.py
└── templates/
    └── backoffice/
        ├── base_backoffice.html
        ├── dashboard.html
        └── cms/
            ├── service_list.html
            ├── service_form.html
            ├── service_confirm_delete.html
            ├── project_list.html
            ├── project_form.html
            ├── project_confirm_delete.html
            ├── social_link_list.html
            ├── social_link_form.html
            └── company_profile_form.html
```

---

### Tarea 2.0: Nueva Aplicación `fobandor.cms`

- [x] Crear `fobandor/cms/__init__.py` (vacío).
- [x] Crear `fobandor/cms/apps.py`:
  ```python
  from django.apps import AppConfig

  class CmsConfig(AppConfig):
      default_auto_field = 'django.db.models.BigAutoField'
      name = 'fobandor.cms'
      label = 'cms'
      verbose_name = 'CMS'
  ```
- [x] Registrar en `config/settings/base.py` → `INSTALLED_APPS`:
  ```python
  'fobandor.cms.apps.CmsConfig',
  ```

---

### Tarea 2.1: Modelos CMS Bilingües (`fobandor/cms/models.py`)

- [x] Implementar los siguientes modelos (todos con `created_at = auto_now_add`, `updated_at = auto_now`):

  ```python
  from django.db import models


  class ServiceCategory(models.Model):
      """4 líneas de negocio: Desarrollo Web, Apps, Publicidad, Studios."""
      slug = models.SlugField(max_length=60, unique=True)
      title_es = models.CharField('Título (ES)', max_length=120)
      title_en = models.CharField('Title (EN)', max_length=120)
      icon = models.CharField('Ícono (SVG/emoji)', max_length=100, blank=True)
      order = models.PositiveSmallIntegerField('Orden', default=0)
      is_active = models.BooleanField('Activo', default=True)
      created_at = models.DateTimeField(auto_now_add=True)
      updated_at = models.DateTimeField(auto_now=True)

      class Meta:
          ordering = ['order']
          verbose_name = 'Categoría de Servicio'
          verbose_name_plural = 'Categorías de Servicio'

      def __str__(self):
          return self.title_es


  class ServiceItem(models.Model):
      """Ítem de servicio anidado bajo una categoría."""
      category = models.ForeignKey(
          ServiceCategory, on_delete=models.CASCADE, related_name='items')
      title_es = models.CharField('Título (ES)', max_length=200)
      title_en = models.CharField('Title (EN)', max_length=200)
      desc_es = models.TextField('Descripción (ES)', blank=True)
      desc_en = models.TextField('Description (EN)', blank=True)
      order = models.PositiveSmallIntegerField('Orden', default=0)
      is_active = models.BooleanField('Activo', default=True)
      created_at = models.DateTimeField(auto_now_add=True)
      updated_at = models.DateTimeField(auto_now=True)

      class Meta:
          ordering = ['order']
          verbose_name = 'Ítem de Servicio'
          verbose_name_plural = 'Ítems de Servicio'

      def __str__(self):
          return f'{self.category.title_es} → {self.title_es}'


  class Project(models.Model):
      """Portafolio de proyectos realizados."""
      title_es = models.CharField('Título (ES)', max_length=200)
      title_en = models.CharField('Title (EN)', max_length=200)
      desc_es = models.TextField('Descripción (ES)', blank=True)
      desc_en = models.TextField('Description (EN)', blank=True)
      client_name = models.CharField('Cliente', max_length=150, blank=True)
      category = models.ForeignKey(
          ServiceCategory, on_delete=models.SET_NULL, null=True, blank=True,
          related_name='projects')
      image = models.ImageField('Imagen', upload_to='projects/', blank=True)
      url = models.URLField('URL del proyecto', blank=True)
      is_featured = models.BooleanField('Destacado', default=False)
      order = models.PositiveSmallIntegerField('Orden', default=0)
      tags = models.CharField('Etiquetas (CSV)', max_length=200, blank=True)
      created_at = models.DateTimeField(auto_now_add=True)
      updated_at = models.DateTimeField(auto_now=True)

      class Meta:
          ordering = ['order', '-created_at']
          verbose_name = 'Proyecto'
          verbose_name_plural = 'Proyectos'

      def __str__(self):
          return self.title_es


  class CompanyProfile(models.Model):
      """Singleton: datos institucionales de FOBANDOR (misión, visión, valores)."""
      mission_es = models.TextField('Misión (ES)', blank=True)
      mission_en = models.TextField('Mission (EN)', blank=True)
      vision_es = models.TextField('Visión (ES)', blank=True)
      vision_en = models.TextField('Vision (EN)', blank=True)
      values_es = models.TextField('Valores (ES)', blank=True)
      values_en = models.TextField('Values (EN)', blank=True)
      founded_year = models.PositiveSmallIntegerField('Año de fundación', null=True, blank=True)
      location = models.CharField('Ubicación', max_length=200, blank=True,
                                  default='Orlando, Florida, EE.UU.')
      website_url = models.URLField('URL del sitio web', blank=True,
                                    default='https://www.fobandor.com')
      created_at = models.DateTimeField(auto_now_add=True)
      updated_at = models.DateTimeField(auto_now=True)

      class Meta:
          verbose_name = 'Perfil de la Empresa'
          verbose_name_plural = 'Perfil de la Empresa'

      def __str__(self):
          return 'FOBANDOR — Perfil Corporativo'

      def save(self, *args, **kwargs):
          """Garantiza el patrón singleton: solo puede existir un registro."""
          self.pk = 1
          super().save(*args, **kwargs)

      @classmethod
      def load(cls):
          obj, _ = cls.objects.get_or_create(pk=1)
          return obj


  class OfficialSocialLink(models.Model):
      """Redes sociales oficiales de FOBANDOR."""
      PLATFORM_CHOICES = [
          ('instagram', 'Instagram'),
          ('tiktok', 'TikTok'),
          ('x', 'X (Twitter)'),
          ('youtube', 'YouTube'),
          ('facebook', 'Facebook'),
      ]
      platform = models.CharField('Plataforma', max_length=20,
                                  choices=PLATFORM_CHOICES, unique=True)
      url = models.URLField('URL')
      handle = models.CharField('Handle / @', max_length=100, blank=True)
      is_active = models.BooleanField('Activo', default=True)
      order = models.PositiveSmallIntegerField('Orden', default=0)
      created_at = models.DateTimeField(auto_now_add=True)
      updated_at = models.DateTimeField(auto_now=True)

      class Meta:
          ordering = ['order']
          verbose_name = 'Red Social Oficial'
          verbose_name_plural = 'Redes Sociales Oficiales'

      def __str__(self):
          return f'{self.get_platform_display()} → {self.handle}'


  class ContactInquiry(models.Model):
      """Consultas entrantes desde el formulario de contacto público."""
      STATUS_CHOICES = [
          ('NEW', 'Nueva'),
          ('READ', 'Leída'),
          ('REPLIED', 'Respondida'),
      ]
      name = models.CharField('Nombre', max_length=150)
      email = models.EmailField('Correo')
      phone = models.CharField('Teléfono', max_length=20, blank=True)
      message = models.TextField('Mensaje')
      service_interest = models.ForeignKey(
          ServiceCategory, on_delete=models.SET_NULL, null=True, blank=True,
          related_name='inquiries', verbose_name='Servicio de interés')
      status = models.CharField('Estado', max_length=10,
                                choices=STATUS_CHOICES, default='NEW')
      created_at = models.DateTimeField(auto_now_add=True)
      updated_at = models.DateTimeField(auto_now=True)

      class Meta:
          ordering = ['-created_at']
          verbose_name = 'Consulta de Contacto'
          verbose_name_plural = 'Consultas de Contacto'

      def __str__(self):
          return f'{self.name} <{self.email}> [{self.status}]'
  ```

---

### Tarea 2.2: Admin CMS (`fobandor/cms/admin.py`)

- [x] Registrar todos los modelos con la API `ModelAdmin`:

  ```python
  from django.contrib import admin
  from .models import (
      ServiceCategory, ServiceItem, Project,
      CompanyProfile, OfficialSocialLink, ContactInquiry,
  )


  class ServiceItemInline(admin.TabularInline):
      model = ServiceItem
      extra = 1
      fields = ('title_es', 'title_en', 'order', 'is_active')


  @admin.register(ServiceCategory)
  class ServiceCategoryAdmin(admin.ModelAdmin):
      list_display = ('title_es', 'slug', 'order', 'is_active')
      list_editable = ('order', 'is_active')
      search_fields = ('title_es', 'title_en', 'slug')
      prepopulated_fields = {'slug': ('title_es',)}
      inlines = [ServiceItemInline]
      fieldsets = (
          ('Español', {'fields': ('slug', 'title_es', 'icon', 'order', 'is_active')}),
          ('English', {'fields': ('title_en',)}),
      )


  @admin.register(Project)
  class ProjectAdmin(admin.ModelAdmin):
      list_display = ('title_es', 'category', 'is_featured', 'order', 'created_at')
      list_filter = ('category', 'is_featured')
      search_fields = ('title_es', 'title_en', 'client_name', 'tags')
      list_editable = ('order', 'is_featured')
      fieldsets = (
          ('Español', {'fields': ('title_es', 'desc_es')}),
          ('English', {'fields': ('title_en', 'desc_en')}),
          ('Metadata', {'fields': ('category', 'client_name', 'image', 'url',
                                   'is_featured', 'order', 'tags')}),
      )


  @admin.register(CompanyProfile)
  class CompanyProfileAdmin(admin.ModelAdmin):
      fieldsets = (
          ('Español', {'fields': ('mission_es', 'vision_es', 'values_es')}),
          ('English', {'fields': ('mission_en', 'vision_en', 'values_en')}),
          ('Datos Generales', {'fields': ('founded_year', 'location', 'website_url')}),
      )

      def has_add_permission(self, request):
          """Bloquea agregar si ya existe el registro singleton."""
          return not CompanyProfile.objects.exists()

      def has_delete_permission(self, request, obj=None):
          return False


  @admin.register(OfficialSocialLink)
  class OfficialSocialLinkAdmin(admin.ModelAdmin):
      list_display = ('platform', 'handle', 'url', 'is_active', 'order')
      list_editable = ('is_active', 'order')


  @admin.register(ContactInquiry)
  class ContactInquiryAdmin(admin.ModelAdmin):
      list_display = ('name', 'email', 'service_interest', 'status', 'created_at')
      list_filter = ('status', 'service_interest')
      search_fields = ('name', 'email', 'message')
      readonly_fields = ('name', 'email', 'phone', 'message',
                         'service_interest', 'created_at')

      def has_add_permission(self, request):
          return False
  ```

---

### Tarea 2.3: Management Command `seed_initial_content`

- [x] Crear `fobandor/cms/management/__init__.py` y `fobandor/cms/management/commands/__init__.py` (vacíos).
- [x] Crear `fobandor/cms/management/commands/seed_initial_content.py`:

  ```python
  from django.core.management.base import BaseCommand
  from fobandor.cms.models import (
      ServiceCategory, ServiceItem, OfficialSocialLink, CompanyProfile,
  )


  CATEGORIES = [
      {
          'slug': 'desarrollo-web',
          'title_es': 'Desarrollo Web con IA',
          'title_en': 'AI-Powered Web Development',
          'icon': '🌐',
          'order': 1,
      },
      {
          'slug': 'desarrollo-apps',
          'title_es': 'Desarrollo de Apps con IA',
          'title_en': 'AI-Powered App Development',
          'icon': '📱',
          'order': 2,
      },
      {
          'slug': 'publicidad',
          'title_es': 'Publicidad con IA',
          'title_en': 'AI-Powered Advertising',
          'icon': '📢',
          'order': 3,
      },
      {
          'slug': 'fobandor-studios',
          'title_es': 'Fobandor Studios',
          'title_en': 'Fobandor Studios',
          'icon': '🎬',
          'order': 4,
      },
  ]

  SOCIAL_LINKS = [
      {'platform': 'instagram', 'url': 'https://www.instagram.com/fobandor.ai',
       'handle': '@fobandor.ai', 'order': 1},
      {'platform': 'tiktok', 'url': 'https://www.tiktok.com/@fobandor',
       'handle': '@fobandor', 'order': 2},
      {'platform': 'x', 'url': 'https://x.com/fobandor',
       'handle': '@fobandor', 'order': 3},
      {'platform': 'youtube', 'url': 'https://www.youtube.com/@fobandor',
       'handle': '@fobandor', 'order': 4},
      {'platform': 'facebook', 'url': 'https://www.facebook.com/share/1EAAc7Qw6x/',
       'handle': 'fobandor', 'order': 5},
  ]

  SERVICE_ITEMS = {
      'desarrollo-web': [
          ('Sitios web corporativos', 'Corporate websites'),
          ('E-commerce', 'E-commerce'),
          ('Landing pages', 'Landing pages'),
          ('Chatbots y asistentes IA', 'AI chatbots and assistants'),
          ('Automatización de procesos', 'Process automation'),
      ],
      'desarrollo-apps': [
          ('Apps iOS / Android', 'iOS / Android apps'),
          ('Aplicaciones web', 'Web applications'),
          ('Apps con asistentes IA', 'Apps with AI assistants'),
          ('Sistemas personalizados', 'Custom systems'),
          ('Integración de APIs y automatizaciones', 'API integrations and automations'),
      ],
      'publicidad': [
          ('Campañas publicitarias', 'Advertising campaigns'),
          ('Videos para redes sociales', 'Social media videos'),
          ('Creatividades con IA', 'AI creatives'),
          ('Avatares y personajes', 'Avatars and characters'),
          ('Copywriting y conceptos', 'Copywriting and concepts'),
          ('Automatización de marketing', 'Marketing automation'),
      ],
      'fobandor-studios': [
          ('Series', 'Series'),
          ('Películas', 'Films'),
          ('Podcasts', 'Podcasts'),
          ('Trailers', 'Trailers'),
          ('Cortometrajes', 'Short films'),
          ('Videoclips', 'Music videos'),
          ('Contenido para YouTube y redes', 'YouTube and social content'),
      ],
  }

  class Command(BaseCommand):
      help = 'Siembra el contenido inicial del CMS (idempotente — usa get_or_create).'

      def handle(self, *args, **options):
          self.stdout.write('Sembrando categorías de servicio...')
          for data in CATEGORIES:
              obj, created = ServiceCategory.objects.get_or_create(
                  slug=data['slug'], defaults=data)
              status = 'CREADA' if created else 'YA EXISTE'
              self.stdout.write(f'  [{status}] {obj.title_es}')

          self.stdout.write('Sembrando ítems de servicio...')
          for slug, items in SERVICE_ITEMS.items():
              category = ServiceCategory.objects.filter(slug=slug).first()
              if not category:
                  self.stdout.write(f'  [OMITIDA] Categoría no encontrada: {slug}')
                  continue
              for order, (title_es, title_en) in enumerate(items, start=1):
                  obj, created = ServiceItem.objects.get_or_create(
                      category=category,
                      title_es=title_es,
                      defaults={'title_en': title_en, 'order': order})
                  status = 'CREADO' if created else 'YA EXISTE'
                  self.stdout.write(f'  [{status}] {category.title_es} → {obj.title_es}')

          self.stdout.write('Sembrando redes sociales oficiales...')
          for data in SOCIAL_LINKS:
              obj, created = OfficialSocialLink.objects.get_or_create(
                  platform=data['platform'], defaults=data)
              status = 'CREADA' if created else 'YA EXISTE'
              self.stdout.write(f'  [{status}] {obj.get_platform_display()} → {obj.handle}')

          self.stdout.write('Sembrando perfil corporativo...')
          profile = CompanyProfile.load()
          if not profile.location:
              profile.location = 'Orlando, Florida, EE.UU.'
              profile.website_url = 'https://www.fobandor.com'
              profile.save()
              self.stdout.write('  [CREADO] FOBANDOR — Perfil Corporativo')
          else:
              self.stdout.write('  [YA EXISTE] FOBANDOR — Perfil Corporativo')

          self.stdout.write(self.style.SUCCESS('✅ seed_initial_content completado.'))
  ```

---

### Tarea 2.4: Migraciones y Seed

- [x] Generar migración inicial del CMS:
  ```bash
  python manage.py makemigrations cms
  ```
- [x] Aplicar todas las migraciones:
  ```bash
  python manage.py migrate
  ```
- [x] Ejecutar el seed de contenido inicial:
  ```bash
  python manage.py seed_initial_content
  ```
- [x] Verificar que no queden migraciones pendientes:
  ```bash
  python manage.py makemigrations --check --dry-run
  ```

---

### Tarea 2.5: Sistema RBAC — Grupos Django

- [x] Crear `fobandor/users/management/__init__.py` y `fobandor/users/management/commands/__init__.py` (vacíos).
- [x] Crear management command `fobandor/users/management/commands/create_rbac_groups.py`:

  ```python
  from django.contrib.auth.models import Group, Permission
  from django.contrib.contenttypes.models import ContentType
  from django.core.management.base import BaseCommand
  from fobandor.cms.models import (
      ServiceCategory, ServiceItem, Project,
      CompanyProfile, OfficialSocialLink, ContactInquiry,
  )


  class Command(BaseCommand):
      help = 'Crea los grupos RBAC de FOBANDOR (idempotente).'

      def handle(self, *args, **options):
          # --- Content_Editors ---
          editors_group, _ = Group.objects.get_or_create(name='Content_Editors')
          cms_models = [ServiceCategory, ServiceItem, Project,
                        CompanyProfile, OfficialSocialLink, ContactInquiry]
          editor_perms = []
          for model in cms_models:
              ct = ContentType.objects.get_for_model(model)
              for action in ('add', 'change', 'view'):
                  perm = Permission.objects.get(
                      codename=f'{action}_{model._meta.model_name}',
                      content_type=ct)
                  editor_perms.append(perm)
          editors_group.permissions.set(editor_perms)
          self.stdout.write(f'  [OK] Grupo Content_Editors configurado.')

          # --- Fulfillment_Operators ---
          # Se asignarán permisos sobre FulfillmentOrder en Etapa 3
          ops_group, created = Group.objects.get_or_create(name='Fulfillment_Operators')
          status = 'CREADO' if created else 'YA EXISTE'
          self.stdout.write(f'  [{status}] Grupo Fulfillment_Operators (permisos de Etapa 3).')

          self.stdout.write(self.style.SUCCESS('✅ Grupos RBAC configurados.'))
  ```

- [x] Ejecutar el command:
  ```bash
  python manage.py create_rbac_groups
  ```

---

### Tarea 2.6: Aplicación `fobandor.backoffice`

- [x] Crear `fobandor/backoffice/__init__.py` (vacío).
- [x] Crear `fobandor/backoffice/apps.py`:
  ```python
  from django.apps import AppConfig

  class BackofficeConfig(AppConfig):
      default_auto_field = 'django.db.models.BigAutoField'
      name = 'fobandor.backoffice'
      label = 'backoffice'
      verbose_name = 'Backoffice'
  ```
- [x] Registrar en `config/settings/base.py` → `INSTALLED_APPS`:
  ```python
  'fobandor.backoffice.apps.BackofficeConfig',
  ```
- [x] Crear `fobandor/backoffice/mixins.py`:
  ```python
  from django.contrib.auth.mixins import AccessMixin
  from django.shortcuts import redirect
  from django.urls import reverse


  class StaffRequiredMixin(AccessMixin):
      """Permite el acceso solo a usuarios autenticados con is_staff=True."""

      def dispatch(self, request, *args, **kwargs):
          if not request.user.is_authenticated:
              return self.handle_no_permission()
          if not request.user.is_staff:
              return redirect(reverse('core:home'))
          return super().dispatch(request, *args, **kwargs)
  ```
- [x] Crear `fobandor/backoffice/urls.py`:
  ```python
  from django.urls import path
  from . import views

  app_name = 'backoffice'

  urlpatterns = [
      path('', views.DashboardView.as_view(), name='dashboard'),
      # Servicios
      path('servicios/', views.ServiceCategoryListView.as_view(), name='service-list'),
      path('servicios/nuevo/', views.ServiceCategoryCreateView.as_view(), name='service-create'),
      path('servicios/<int:pk>/editar/', views.ServiceCategoryUpdateView.as_view(), name='service-update'),
      path('servicios/<int:pk>/eliminar/', views.ServiceCategoryDeleteView.as_view(), name='service-delete'),
      # Proyectos
      path('proyectos/', views.ProjectListView.as_view(), name='project-list'),
      path('proyectos/nuevo/', views.ProjectCreateView.as_view(), name='project-create'),
      path('proyectos/<int:pk>/editar/', views.ProjectUpdateView.as_view(), name='project-update'),
      path('proyectos/<int:pk>/eliminar/', views.ProjectDeleteView.as_view(), name='project-delete'),
      # Redes Sociales
      path('redes-sociales/', views.OfficialSocialLinkListView.as_view(), name='social-list'),
      path('redes-sociales/<int:pk>/editar/', views.OfficialSocialLinkUpdateView.as_view(), name='social-update'),
      # Perfil Corporativo (singleton)
      path('empresa/', views.CompanyProfileUpdateView.as_view(), name='company-profile'),
  ]
  ```
- [x] Registrar en `config/urls.py` bajo `i18n_patterns`, **antes** de `fobandor.core.urls`:
  ```python
  urlpatterns += i18n_patterns(
      path("admin/", admin.site.urls),
      path("backoffice/", include("fobandor.backoffice.urls", namespace="backoffice")),
      path("", include("fobandor.core.urls")),
  )
  ```

---

### Tarea 2.7: Vistas del Backoffice (`fobandor/backoffice/views.py`)

- [x] Implementar todas las vistas usando `StaffRequiredMixin` + `LoginRequiredMixin` + CBVs genéricas:

  ```python
  from django.contrib.auth.mixins import LoginRequiredMixin
  from django.urls import reverse_lazy
  from django.views.generic import (
      ListView, CreateView, UpdateView, DeleteView, TemplateView,
  )
  from fobandor.cms.models import (
      ServiceCategory, Project, OfficialSocialLink, CompanyProfile,
  )
  from .mixins import StaffRequiredMixin


  class BackofficeMixin(LoginRequiredMixin, StaffRequiredMixin):
      """Mixin base para todas las vistas del backoffice."""
      pass


  # --- Dashboard ---

  class DashboardView(BackofficeMixin, TemplateView):
      template_name = 'backoffice/dashboard.html'

      def get_context_data(self, **kwargs):
          ctx = super().get_context_data(**kwargs)
          from django.contrib.auth import get_user_model
          User = get_user_model()
          ctx['total_users'] = User.objects.count()
          ctx['total_services'] = ServiceCategory.objects.filter(is_active=True).count()
          ctx['total_projects'] = Project.objects.count()
          return ctx


  # --- Servicios ---

  class ServiceCategoryListView(BackofficeMixin, ListView):
      model = ServiceCategory
      template_name = 'backoffice/cms/service_list.html'
      context_object_name = 'services'
      ordering = ['order']


  class ServiceCategoryCreateView(BackofficeMixin, CreateView):
      model = ServiceCategory
      template_name = 'backoffice/cms/service_form.html'
      fields = ['slug', 'title_es', 'title_en', 'icon', 'order', 'is_active']
      success_url = reverse_lazy('backoffice:service-list')


  class ServiceCategoryUpdateView(BackofficeMixin, UpdateView):
      model = ServiceCategory
      template_name = 'backoffice/cms/service_form.html'
      fields = ['slug', 'title_es', 'title_en', 'icon', 'order', 'is_active']
      success_url = reverse_lazy('backoffice:service-list')


  class ServiceCategoryDeleteView(BackofficeMixin, DeleteView):
      model = ServiceCategory
      template_name = 'backoffice/cms/service_confirm_delete.html'
      success_url = reverse_lazy('backoffice:service-list')


  # --- Proyectos ---

  class ProjectListView(BackofficeMixin, ListView):
      model = Project
      template_name = 'backoffice/cms/project_list.html'
      context_object_name = 'projects'
      ordering = ['order', '-created_at']


  class ProjectCreateView(BackofficeMixin, CreateView):
      model = Project
      template_name = 'backoffice/cms/project_form.html'
      fields = ['title_es', 'title_en', 'desc_es', 'desc_en',
                'client_name', 'category', 'image', 'url',
                'is_featured', 'order', 'tags']
      success_url = reverse_lazy('backoffice:project-list')


  class ProjectUpdateView(BackofficeMixin, UpdateView):
      model = Project
      template_name = 'backoffice/cms/project_form.html'
      fields = ['title_es', 'title_en', 'desc_es', 'desc_en',
                'client_name', 'category', 'image', 'url',
                'is_featured', 'order', 'tags']
      success_url = reverse_lazy('backoffice:project-list')


  class ProjectDeleteView(BackofficeMixin, DeleteView):
      model = Project
      template_name = 'backoffice/cms/project_confirm_delete.html'
      success_url = reverse_lazy('backoffice:project-list')


  # --- Redes Sociales ---

  class OfficialSocialLinkListView(BackofficeMixin, ListView):
      model = OfficialSocialLink
      template_name = 'backoffice/cms/social_link_list.html'
      context_object_name = 'social_links'


  class OfficialSocialLinkUpdateView(BackofficeMixin, UpdateView):
      model = OfficialSocialLink
      template_name = 'backoffice/cms/social_link_form.html'
      fields = ['url', 'handle', 'is_active', 'order']
      success_url = reverse_lazy('backoffice:social-list')


  # --- Perfil Corporativo (Singleton) ---

  class CompanyProfileUpdateView(BackofficeMixin, UpdateView):
      model = CompanyProfile
      template_name = 'backoffice/cms/company_profile_form.html'
      fields = ['mission_es', 'mission_en', 'vision_es', 'vision_en',
                'values_es', 'values_en', 'founded_year', 'location', 'website_url']
      success_url = reverse_lazy('backoffice:company-profile')

      def get_object(self, queryset=None):
          """Siempre retorna el singleton (pk=1), creándolo si no existe."""
          return CompanyProfile.load()
  ```

---

### Tarea 2.8: Plantillas del Backoffice

#### `templates/backoffice/base_backoffice.html`

- [x] Layout base con sidebar Tailwind + HTMX:
  - Sidebar izquierdo con enlaces: Dashboard, Servicios, Proyectos, Redes Sociales, Empresa.
  - Header con nombre de usuario y botón de logout.
  - Área de contenido principal con `{% block content %}`.
  - Incluir `static/css/output.css` y `static/js/vendor/htmx.min.js`.
  - Paleta FOBANDOR: fondo sidebar `fobandor-dark`, acentos `fobandor-orange`.

#### `templates/backoffice/dashboard.html`

- [x] Extiende `base_backoffice.html`.
- [x] Tarjetas de resumen:
  - **Total Usuarios** → `{{ total_users }}`
  - **Servicios Activos** → `{{ total_services }}`
  - **Proyectos** → `{{ total_projects }}`
  - **Órdenes Pendientes** → "Disponible en Etapa 3" (placeholder visual)
- [x] Accesos rápidos a secciones del CMS.

#### Plantillas CMS (mínimas funcionales)

- [x] `templates/backoffice/cms/service_list.html` — tabla con columnas: Título ES, Título EN, Orden, Activo, Acciones (Editar / Eliminar). Botón "Nuevo Servicio".
- [x] `templates/backoffice/cms/service_form.html` — formulario bilingüe con pestañas Alpine.js (tab ES / tab EN). Botones Guardar / Cancelar.
- [x] `templates/backoffice/cms/service_confirm_delete.html` — confirmación de eliminación con nombre del servicio.
- [x] `templates/backoffice/cms/project_list.html` — tabla: Título, Categoría, Destacado, Orden, Acciones.
- [x] `templates/backoffice/cms/project_form.html` — formulario con pestañas Alpine.js ES/EN + campos de metadata.
- [x] `templates/backoffice/cms/project_confirm_delete.html` — confirmación de eliminación.
- [x] `templates/backoffice/cms/social_link_list.html` — lista de plataformas con URL, handle y toggle activo.
- [x] `templates/backoffice/cms/social_link_form.html` — formulario de edición de red social.
- [x] `templates/backoffice/cms/company_profile_form.html` — formulario singleton con pestañas ES/EN.

---

### Tarea 2.9: Integración CMS en la Home Pública

- [x] Crear `fobandor/core/context_processors.py` con el context processor global de redes sociales:
  ```python
  from fobandor.cms.models import OfficialSocialLink


  def social_links(request):
      """Inyecta las redes sociales oficiales activas en todas las plantillas."""
      return {
          'social_links': OfficialSocialLink.objects.filter(is_active=True).order_by('order'),
      }
  ```
- [x] Registrar el context processor en `config/settings/base.py` → `TEMPLATES[...]['OPTIONS']['context_processors']`:
  ```python
  'fobandor.core.context_processors.social_links',
  ```
- [x] Actualizar `fobandor/core/views.py` → `home_view` para pasar solo `services`:
  ```python
  from fobandor.cms.models import ServiceCategory

  def home_view(request):
      services = ServiceCategory.objects.filter(is_active=True).order_by('order')
      return render(request, 'pages/home.html', {'services': services})
  ```
- [x] Actualizar `templates/pages/home.html` — sección "4 Líneas de Negocio" (usar `LANGUAGE_CODE` del context processor i18n, ya disponible):
  ```html
  {% for service in services %}
  <div class="...">
      <span>{{ service.icon }}</span>
      <h3>{% if LANGUAGE_CODE == 'es' %}{{ service.title_es }}{% else %}{{ service.title_en }}{% endif %}</h3>
  </div>
  {% endfor %}
  ```
- [x] Actualizar `templates/partials/footer.html` — redes sociales dinámicas (desde el context processor global):
  ```html
  {% for link in social_links %}
  <a href="{{ link.url }}" target="_blank" rel="noopener noreferrer">
      {{ link.get_platform_display }}
  </a>
  {% endfor %}
  ```

---

### Tarea 2.10: Pruebas Automatizadas

- [x] Crear `fobandor/cms/tests/__init__.py` (vacío).
- [x] Crear `fobandor/cms/tests/test_models.py`:

  ```python
  import pytest
  from fobandor.cms.models import ServiceCategory, OfficialSocialLink, CompanyProfile


  @pytest.mark.django_db
  def test_service_category_creation():
      cat = ServiceCategory.objects.create(
          slug='test-web', title_es='Web', title_en='Web', order=1)
      assert str(cat) == 'Web'
      assert cat.is_active is True


  @pytest.mark.django_db
  def test_official_social_link_creation():
      link = OfficialSocialLink.objects.create(
          platform='instagram',
          url='https://www.instagram.com/fobandor.ai',
          handle='@fobandor.ai',
          order=1)
      assert 'Instagram' in str(link)


  @pytest.mark.django_db
  def test_company_profile_singleton():
      p1 = CompanyProfile.load()
      p2 = CompanyProfile.load()
      assert p1.pk == p2.pk == 1


  @pytest.mark.django_db
  def test_seed_initial_content_idempotent():
      from django.core.management import call_command
      call_command('seed_initial_content', verbosity=0)
      count_before = ServiceCategory.objects.count()
      call_command('seed_initial_content', verbosity=0)
      count_after = ServiceCategory.objects.count()
      assert count_before == count_after == 4
  ```

- [x] Crear `fobandor/backoffice/tests/__init__.py` (vacío).
- [x] Crear `fobandor/backoffice/tests/test_views.py`:

  ```python
  import pytest
  from django.urls import reverse


  @pytest.mark.django_db
  def test_dashboard_anonymous_redirects(client):
      url = reverse('backoffice:dashboard')
      response = client.get(url, follow=False)
      assert response.status_code in (302, 301)


  @pytest.mark.django_db
  def test_dashboard_staff_access(client, django_user_model):
      user = django_user_model.objects.create_user(
          email='staff@fobandor.com', password='Test1234!', is_staff=True)
      client.force_login(user)
      url = reverse('backoffice:dashboard')
      response = client.get(url)
      assert response.status_code == 200


  @pytest.mark.django_db
  def test_dashboard_non_staff_redirects(client, django_user_model):
      user = django_user_model.objects.create_user(
          email='client@example.com', password='Test1234!', is_staff=False)
      client.force_login(user)
      url = reverse('backoffice:dashboard')
      response = client.get(url, follow=False)
      assert response.status_code in (302, 301)
  ```

---

### Tarea 2.11: Verificación de Aceptación Técnica (Etapa 2)

- [x] `python manage.py check` → 0 issues.
- [x] `python manage.py makemigrations --check --dry-run` → sin cambios pendientes.
- [x] `pytest` → todos los tests pasando (mínimo: 3 de Etapa 1 + 4 de CMS + 3 de Backoffice).
- [x] `flake8 config/ fobandor/ scripts/` → limpio (0 errores).
- [x] `python manage.py runserver 0.0.0.0:8000` → sin errores en consola.
- [x] Verificar en navegador:
  - `http://localhost:8000/es/backoffice/` → redirige a login (anónimo).
  - Login como `admin@fobandor.com` / `ChangeMe123!` → accede a dashboard.
  - Dashboard muestra tarjetas de resumen con datos reales de la BD.
  - `http://localhost:8000/es/backoffice/servicios/` → lista las 4 categorías sembradas.
  - `http://localhost:8000/es/` → Home muestra servicios dinámicos desde la BD.
  - Footer muestra las 5 redes sociales dinámicas.
  - Cambio ES/EN funciona correctamente.
- [x] Compilar CSS con nuevas clases Tailwind del backoffice:
  ```bash
  npm run build:css
  ```
- [x] Commit y push al repositorio:
  ```bash
  git add .
  git commit -m "feat(etapa-2): identidad, rbac y backoffice cms"
  git push origin main
  ```

---

## 5. Etapa 3 — Registro de Clientes, Autenticación Gmail, Stripe Checkout y SLA 7 Días

> **Gobernanza Multi-Agente:**
> * **Diseñado y Validado por:** Antigravity-IDE (Arquitecto de Software Senior)
> * **Agente Ejecutor:** OpenCode (DeepSeek V4 Pro / TDD & Clean Architecture)
> * **Estado Actual:** FASE 4: EJECUTADA Y VALIDADA por Antigravity-IDE. Criterio de Aceptación de la Etapa 3 CUMPLIDO. Listo para inicio de Etapa 4.

---

### Notas de Corrección (revisión técnica OpenCode, aplicadas)

1. **Adapter social:** sobrescribir `save_user` (no `pre_social_login`) para persistir `is_email_verified`.
2. **Webhook:** `invoice.paid` es la única fuente que crea/renueva `FulfillmentOrder` (idempotente por `stripe_invoice_id` único); `checkout.session.completed` solo activa `CustomerSubscription` y vincula `User.stripe_customer_id`.
3. **`allauth.urls`** registrado fuera de `i18n_patterns` para callback estable de Google.
4. **`SubscriptionPlan.order_type`** (decisión: 1 orden por suscripción) define el `order_type` de la orden.
5. **`FulfillmentOrder.stripe_invoice_id`** con `unique=True` para idempotencia.
6. **`LOGIN_URL = "account_login"`** (reemplaza el `admin:login` temporal de Etapa 2).
7. **`stripe_customer_id`** vive solo en `User` (eliminado de `CustomerSubscription`).
8. **URLs absolutas** en `success_url`/`cancel_url` (`build_absolute_uri`).
9. **`features_es/en`** con `default=list` (JSONField).
10. **Señal `email_confirmed`** → marca `User.is_email_verified = True` para registro Email/Password.
11. **Site** de `django.contrib.sites` con dominio `localhost:8000` (seed/creación).

---

### Resumen de Alcance (Etapa 3)

1. **Autenticación Híbrida y Social Login con Gmail:**
   - Autenticación tradicional Email + Contraseña con verificación por correo.
   - Social Login con cuentas Gmail (Google OAuth 2.0 / `django-allauth`) con auto-verificación instantánea (`is_email_verified = True`).
   - Gate de seguridad: ningún cliente accede a Stripe Checkout sin verificación previa (ADR-006).
   - Formulario de Onboarding AVS (dirección completa y teléfono E.164 para Stripe AVS).
2. **Infraestructura de Pagos Stripe (`fobandor.billing`):**
   - Catálogo de 3 planes de suscripción mensual con soporte de cupones de descuento.
   - Integración de sesiones seguras de Stripe Checkout en modo suscripción.
   - Integración de Stripe Customer Portal para autogestión de tarjetas y suscripciones.
   - Webhook listener criptográfico (`/stripe/webhook/`) firmado con HMAC-SHA256 (`checkout.session.completed`, `invoice.paid`, etc.).
3. **Motor de Entregas y SLA de 7 Días (`fobandor.fulfillment`):**
   - Creación automática de `FulfillmentOrder` al confirmar pago en Stripe con `due_date = paid_at + 7 días`.
   - Management command `check_overdue_orders` para marcar automáticamente órdenes `VENCIDA` (ADR-009).
   - Gestión en `/backoffice/entregas/` con badges semafóricos de SLA y permisos para `Fulfillment_Operators`.
4. **Portal del Cliente (`/mi-cuenta/`):**
   - Vista de autoservicio para clientes con estado de plan, barra de progreso del SLA de 7 días, historial de entregables digitales y botón al Customer Portal.
5. **Suite de Pruebas Automatizadas y Verificación:**
   - Cobertura con `pytest-django` para flujos de pago, webhook signature, SLA y permisos.

---

### Árbol de Archivos Objetivo (Etapa 3 — Incremental)

```text
fobandor/
├── fobandor/
│   ├── users/
│   │   ├── adapters.py
│   │   ├── forms.py
│   │   └── views.py
│   ├── billing/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── services.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── management/
│   │   │   └── commands/
│   │   │       └── seed_subscription_plans.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_models.py
│   │       └── test_webhooks.py
│   ├── fulfillment/
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── admin.py
│   │   ├── models.py
│   │   ├── services.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   ├── management/
│   │   │   └── commands/
│   │   │       └── check_overdue_orders.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       └── test_sla.py
│   └── portal/
│       ├── __init__.py
│       ├── apps.py
│       ├── urls.py
│       ├── views.py
│       └── tests/
│           ├── __init__.py
│           └── test_portal.py
└── templates/
    ├── account/
    │   ├── login.html
    │   ├── signup.html
    │   ├── email_confirm.html
    │   └── password_reset.html
    ├── billing/
    │   ├── pricing.html
    │   └── checkout_redirect.html
    ├── portal/
    │   ├── dashboard.html
    │   └── onboarding_avs.html
    └── backoffice/
        └── fulfillment/
            ├── order_list.html
            └── order_detail.html
```

---

### Tarea 3.0: Dependencias y Variables de Entorno

- [x] Añadir a `requirements/base.txt`:
  ```text
  stripe>=10.0.0
  django-allauth[socialaccount]>=65.0.0
  ```
- [x] Instalar en el entorno virtual:
  ```bash
  pip install -r requirements/base.txt
  ```
- [x] Agregar variables en `.env.example` y `.env`:
  ```env
  # Stripe API Keys (Modo Test en desarrollo)
  STRIPE_PUBLIC_KEY=pk_test_placeholder
  STRIPE_SECRET_KEY=sk_test_placeholder
  STRIPE_WEBHOOK_SECRET=whsec_placeholder

  # Google OAuth 2.0 (Social Login Gmail)
  GOOGLE_OAUTH_CLIENT_ID=placeholder_client_id.apps.googleusercontent.com
  GOOGLE_OAUTH_CLIENT_SECRET=placeholder_client_secret
  ```

---

### Tarea 3.1: Configuración de Django-Allauth y Social Login Gmail

- [x] Configurar `config/settings/base.py`:
  - En `INSTALLED_APPS` agregar:
    ```python
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'fobandor.billing.apps.BillingConfig',
    'fobandor.fulfillment.apps.FulfillmentConfig',
    'fobandor.portal.apps.PortalConfig',
    ```
  - Configurar `SITE_ID = 1`.
  - Configurar `AUTHENTICATION_BACKENDS`:
    ```python
    AUTHENTICATION_BACKENDS = [
        'django.contrib.auth.backends.ModelBackend',
        'allauth.account.auth_backends.AuthenticationBackend',
    ]
    ```
  - Directivas de Allauth:
    ```python
    ACCOUNT_USER_MODEL_USERNAME_FIELD = None
    ACCOUNT_EMAIL_REQUIRED = True
    ACCOUNT_USERNAME_REQUIRED = False
    ACCOUNT_AUTHENTICATION_METHOD = 'email'
    ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
    ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
    ACCOUNT_ADAPTER = 'fobandor.users.adapters.CustomAccountAdapter'
    SOCIALACCOUNT_ADAPTER = 'fobandor.users.adapters.CustomSocialAccountAdapter'
    LOGIN_REDIRECT_URL = '/mi-cuenta/'
    LOGOUT_REDIRECT_URL = '/'
    ```
  - Proveedor Google:
    ```python
    SOCIALACCOUNT_PROVIDERS = {
        'google': {
            'SCOPE': ['profile', 'email'],
            'AUTH_PARAMS': {'access_type': 'online'},
            'APP': {
                'client_id': env('GOOGLE_OAUTH_CLIENT_ID', default=''),
                'secret': env('GOOGLE_OAUTH_CLIENT_SECRET', default=''),
                'key': '',
            }
        }
    }
    ```
- [x] Implementar `fobandor/users/adapters.py`:
  ```python
  from allauth.account.adapter import DefaultAccountAdapter
  from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


  class CustomAccountAdapter(DefaultAccountAdapter):
      def is_open_for_signup(self, request):
          return True


  class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
      """Auto-verifica cuentas conectadas vía Google OAuth 2.0 (ADR-008)."""
      def pre_social_login(self, request, sociallogin):
          user = sociallogin.user
          if sociallogin.account.provider == 'google':
              user.is_email_verified = True
  ```

---

### Tarea 3.2: Gate de Seguridad AVS y Verificación de Email

- [x] Crear mixin `EmailVerifiedGateMixin` en `fobandor/users/mixins.py`:
  ```python
  from django.contrib.auth.mixins import AccessMixin
  from django.shortcuts import redirect
  from django.contrib import messages
  from django.utils.translation import gettext_lazy as _


  class EmailVerifiedRequiredMixin(AccessMixin):
      """Bloquea el acceso a Checkout si el usuario no tiene email verificado (ADR-006)."""
      def dispatch(self, request, *args, **kwargs):
          if not request.user.is_authenticated:
              return self.handle_no_permission()
          if not request.user.is_email_verified:
              messages.warning(request, _('Debes verificar tu correo antes de contratar un plan.'))
              return redirect('account_email')
          return super().dispatch(request, *args, **kwargs)
  ```
- [x] Crear formulario de Onboarding AVS en `fobandor/users/forms.py`:
  - Campos: `billing_address_line1`, `billing_address_line2`, `billing_city`, `billing_state`, `billing_postal_code`, `billing_country`, `phone`.
  - Validación de teléfono E.164 y país ISO-2.

---

### Tarea 3.3: Módulo `fobandor.billing` (Modelos y Admin)

- [x] Crear `fobandor/billing/apps.py` (`name='fobandor.billing'`, `label='billing'`).
- [x] Implementar `fobandor/billing/models.py`:
  - `SubscriptionPlan`:
    - `slug` (unique: `starter`, `pro`, `enterprise`)
    - `name_es`, `name_en`
    - `desc_es`, `desc_en`
    - `price_usd` (DecimalField)
    - `stripe_price_id` (CharField)
    - `features_es`, `features_en` (JSONField)
    - `order` (PositiveSmallIntegerField)
    - `is_active` (BooleanField, default=True)
    - `is_highlighted` (BooleanField, default=False)
  - `CustomerSubscription`:
    - `user` (FK to `users.User`, related_name='subscriptions')
    - `plan` (FK to `SubscriptionPlan`)
    - `stripe_subscription_id` (CharField, unique=True)
    - `stripe_customer_id` (CharField)
    - `status` (choices: `active`, `past_due`, `canceled`, `unpaid`, `trialing`)
    - `current_period_start`, `current_period_end` (DateTimeField)
    - `cancel_at_period_end` (BooleanField, default=False)
  - `BillingInvoice`:
    - `user` (FK to `users.User`)
    - `stripe_invoice_id` (CharField, unique=True)
    - `amount_paid` (DecimalField)
    - `currency` (CharField, default='usd')
    - `paid_at` (DateTimeField)
    - `invoice_pdf_url` (URLField, blank=True)
- [x] Registrar en `fobandor/billing/admin.py` con `list_display`, filtros y búsquedas.
- [x] Crear management command `seed_subscription_plans.py` con 3 planes mensuales base:
  - **Plan Starter:** $199 USD/mes (Desarrollo Web & Contenido base).
  - **Plan Pro:** $499 USD/mes (Web + Apps + Publicidad IA mensual).
  - **Plan Enterprise:** $999 USD/mes (Solución Full Stack + Fobandor Studios).

---

### Tarea 3.4: Pasarela Stripe Checkout y Customer Portal (`fobandor.billing`)

- [x] Implementar `fobandor/billing/services.py`:
  - `get_or_create_stripe_customer(user) -> str`: vincula y persiste `stripe_customer_id`.
  - `create_checkout_session(user, plan, success_url, cancel_url) -> str`: genera la sesión de Stripe Checkout con `mode='subscription'`, `allow_promotion_codes=True` y metadata (`user_id`, `plan_id`).
  - `create_customer_portal_session(user, return_url) -> str`: genera la sesión del Stripe Customer Portal para gestionar tarjetas y cancelación.
- [x] Implementar vistas en `fobandor/billing/views.py`:
  - `PricingCatalogView`: renderiza la tabla comparativa de los 3 planes (`/precios/`).
  - `CreateCheckoutSessionView`: protegida con `LoginRequiredMixin` + `EmailVerifiedRequiredMixin`.
  - `StripeCustomerPortalView`: redirige al portal de Stripe.

---

### Tarea 3.5: Webhook Listener Criptográfico (`/stripe/webhook/`)

- [x] Implementar vista `StripeWebhookView` en `fobandor/billing/views.py`:
  - Marcar con `@csrf_exempt` y `@require_POST`.
  - Validar firma criptográfica HMAC con `stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)`.
  - Manejador de eventos:
    - `checkout.session.completed`: activa la suscripción y dispara la creación de la primera `FulfillmentOrder` (SLA 7 días).
    - `invoice.paid`: registra `BillingInvoice` y renueva el ciclo de entrega de 7 días.
    - `customer.subscription.deleted`: actualiza `CustomerSubscription.status = 'canceled'`.
- [x] Registrar ruta `/stripe/webhook/` fuera de `i18n_patterns` en `config/urls.py`.

---

### Tarea 3.6: Motor de Entregas SLA 7 Días (`fobandor.fulfillment`)

- [x] Crear `fobandor/fulfillment/apps.py` (`name='fobandor.fulfillment'`, `label='fulfillment'`).
- [x] Implementar `fobandor/fulfillment/models.py`:
  ```python
  from django.db import models
  from django.utils import timezone
  from datetime import timedelta
  from fobandor.users.models import User
  from fobandor.billing.models import CustomerSubscription


  class FulfillmentOrder(models.Model):
      ORDER_TYPES = [
          ('WEB_DEV', 'Desarrollo Web con IA'),
          ('APP_DEV', 'Desarrollo de Apps con IA'),
          ('ADS_AI', 'Publicidad con IA'),
          ('STUDIOS', 'Fobandor Studios'),
      ]
      STATUS_CHOICES = [
          ('PENDIENTE_PRODUCCION', 'Pendiente de Producción'),
          ('EN_PROCESO', 'En Proceso'),
          ('ENTREGADA', 'Entregada'),
          ('VENCIDA', 'Vencida'),
          ('CANCELADA', 'Cancelada'),
      ]
      user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fulfillment_orders')
      subscription = models.ForeignKey(CustomerSubscription, on_delete=models.SET_NULL, null=True, blank=True)
      order_type = models.CharField(max_length=20, choices=ORDER_TYPES, default='WEB_DEV')
      stripe_invoice_id = models.CharField(max_length=100, blank=True)
      status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='PENDIENTE_PRODUCCION')
      paid_at = models.DateTimeField(default=timezone.now)
      due_date = models.DateTimeField()
      delivered_at = models.DateTimeField(null=True, blank=True)
      deliverable_file = models.FileField(upload_to='deliverables/', blank=True)
      deliverable_url = models.URLField(blank=True)
      internal_notes = models.TextField(blank=True)
      created_at = models.DateTimeField(auto_now_add=True)
      updated_at = models.DateTimeField(auto_now=True)

      def save(self, *args, **kwargs):
          if not self.due_date and self.paid_at:
              self.due_date = self.paid_at + timedelta(days=7)
          super().save(*args, **kwargs)

      @property
      def days_remaining(self):
          if self.status == 'ENTREGADA':
              return 0
          now = timezone.now()
          diff = self.due_date - now
          return max(0, diff.days)
  ```
- [x] Crear management command `fobandor/fulfillment/management/commands/check_overdue_orders.py`:
  - Evalúa órdenes con estado `PENDIENTE_PRODUCCION` o `EN_PROCESO` donde `due_date < timezone.now()`.
  - Actualiza atómicamente a `status = 'VENCIDA'` y registra log.
  - Idempotente.

---

### Tarea 3.7: Backoffice de Órdenes y Entregas (`/backoffice/entregas/`)

- [x] Implementar vistas en `fobandor/backoffice/`:
  - `FulfillmentOrderListView`: tabla de órdenes con filtros por estado, ordenación por `due_date`, y badges semafóricos (Verde: > 3 días, Amarillo: <= 2 días, Rojo: Vencida).
  - `FulfillmentOrderDeliverView`: formulario para subir entregable (`deliverable_file` o `deliverable_url`), ingresar notas y marcar como `ENTREGADA` (registra `delivered_at = timezone.now()`).
- [x] Actualizar `fobandor/users/management/commands/create_rbac_groups.py`:
  - Asignar permisos sobre `FulfillmentOrder` al grupo `Fulfillment_Operators`.
- [x] Integrar enlace "Órdenes SLA" en el sidebar de `templates/backoffice/base_backoffice.html`.

---

### Tarea 3.8: Portal del Cliente (`fobandor.portal` en `/mi-cuenta/`)

- [x] Crear app `fobandor.portal`.
- [x] Implementar `fobandor/portal/views.py`:
  - `CustomerDashboardView`:
    - Resumen de suscripción activa y plan.
    - Barra de progreso del SLA de la orden activa (días transcurridos vs. 7 días límite).
    - Historial de órdenes y enlaces de descarga de entregables completados.
    - Botón de acceso al Stripe Customer Portal.
  - `OnboardingAVSView`: formulario para completar datos fiscales/AVS pendientes.
- [x] Plantillas en `templates/portal/dashboard.html` y `onboarding_avs.html` con Tailwind CSS y Dark/Light Mode.

---

### Tarea 3.9: Migraciones y Seeds

- [x] `python manage.py makemigrations billing fulfillment portal`
- [x] `python manage.py migrate`
- [x] `python manage.py seed_subscription_plans`
- [x] `python manage.py create_rbac_groups`
- [x] `python manage.py makemigrations --check --dry-run`

---

### Tarea 3.10: Pruebas Automatizadas con Pytest

- [x] `fobandor/fulfillment/tests/test_sla.py`:
  - Cálculo estricto de SLA: `due_date` exactamente a 7 días de `paid_at`.
  - Transición a `VENCIDA` mediante `check_overdue_orders`.
  - Marca de entrega con registro de `delivered_at`.
- [x] `fobandor/billing/tests/test_webhooks.py`:
  - Verificación de firma criptográfica válida y rechazo de firmas falsas.
  - Creación automática de suscripción y `FulfillmentOrder` ante evento `checkout.session.completed`.
- [x] `fobandor/users/tests/test_gate.py`:
  - Bloqueo de acceso a Checkout para usuarios con `is_email_verified = False`.
  - Auto-verificación de usuarios autenticados vía Google Social Account.

---

### Tarea 3.11: Verificación de Aceptación Técnica (Etapa 3)

- [x] `python manage.py check` → 0 issues.
- [x] `pytest` → todos los tests pasando (mínimo: 10 previos + 6 nuevos de billing/fulfillment/gate).
- [x] `flake8 config fobandor scripts` → 0 errores.
- [x] Simulación de Checkout y webhook exitoso en entorno local.
- [x] Compilación CSS con `npm run build:css`.
- [x] Commit y push a `main`:
  ```bash
  git add .
  git commit -m "feat(etapa-3): stripe checkout, autenticacion gmail, motor sla 7 dias y portal cliente"
  git push origin main
  ```

---

## 5.1 Refinamiento Comercial: Planes de Acompañamiento y Gestión CMS en Backoffice

> **Gobernanza Multi-Agente:**
> * **Diseñado y Validado por:** Antigravity-IDE (Arquitecto de Software Senior)
> * **Agente Ejecutor:** OpenCode (DeepSeek V4 Pro / TDD & Clean Architecture)
> * **Estado Actual:** FASE 4: EJECUTADA Y VALIDADA por Antigravity-IDE. Criterio de Aceptación del Refinamiento Comercial (3.12–3.16) CUMPLIDO. Listo para inicio de Etapa 4.

---

### Resumen del Refinamiento Comercial
Freddy Obando definió los 3 paquetes comerciales oficiales del negocio (**Planes de Acompañamiento: Marketing Digital & Ventas para negocios locales**). Es requisito crítico que los planes, precios y claves de Stripe puedan ser administrados y actualizados dinámicamente por el staff desde el Backoffice sin tocar código fuente ni desplegar, con integración a Formspree para el diagnóstico de clientes.

---

### Tarea 3.12: Enriquecimiento del Modelo `SubscriptionPlan` (`fobandor/billing/models.py`)

- [x] Incorporar los siguientes campos al modelo `SubscriptionPlan`:
  ```python
  subtitle_es = models.CharField('Subtítulo (ES)', max_length=150, blank=True)
  subtitle_en = models.CharField('Subtitle (EN)', max_length=150, blank=True)
  min_commitment_months = models.PositiveSmallIntegerField(
      'Compromiso Mínimo (Meses)', default=1,
      help_text='Acompañamiento mínimo exigido (ej. 2 o 3 meses).'
  )
  target_audience_es = models.TextField(
      'Público Objetivo (ES)', blank=True,
      help_text='Ideal para negocios que...'
  )
  target_audience_en = models.TextField(
      'Target Audience (EN)', blank=True
  )
  disclaimer_es = models.TextField('Aviso Legal (ES)', blank=True)
  disclaimer_en = models.TextField('Legal Disclaimer (EN)', blank=True)
  formspree_endpoint = models.CharField(
      'Formspree Form ID o URL', max_length=255, blank=True,
      default='https://formspree.io/f/placeholder'
  )
  ```
- [x] Ejecutar migraciones:
  ```bash
  python manage.py makemigrations billing
  python manage.py migrate
  ```

---

### Tarea 3.13: Módulo de Gestión de Planes en Backoffice (`fobandor/backoffice/`)

- [x] Crear vistas CBV en `fobandor/backoffice/views.py`:
  - `SubscriptionPlanListView(BackofficeMixin, ListView)`: listado de planes con orden, precio en USD, `stripe_price_id`, estado activo/destacado y botón de edición.
  - `SubscriptionPlanUpdateView(BackofficeMixin, UpdateView)`: formulario bilingüe con pestañas Alpine.js (Español / Inglés) para editar textos, precios, meses de compromiso y `stripe_price_id`.
- [x] Registrar rutas en `fobandor/backoffice/urls.py`:
  ```python
  path('planes/', views.SubscriptionPlanListView.as_view(), name='plan-list'),
  path('planes/<int:pk>/editar/', views.SubscriptionPlanUpdateView.as_view(), name='plan-update'),
  ```
- [x] Crear plantillas:
  - `templates/backoffice/billing/plan_list.html`
  - `templates/backoffice/billing/plan_form.html`
- [x] Añadir enlace al sidebar en `templates/backoffice/base_backoffice.html`:
  ```html
  <a href="{% url 'backoffice:plan-list' %}" class="...">
      <span>💳</span> {% trans "Planes & Precios" %}
  </a>
  ```

---

### Tarea 3.14: Seeder con los Datos Comerciales Reales de Freddy Obando

- [x] Actualizar `fobandor/billing/management/commands/seed_subscription_plans.py` con los datos exactos de la infografía:
  1. **Plan 1 • Impulso:**
     - `slug`: `impulso`
     - `name_es`: `Plan 1 • Impulso`, `name_en`: `Plan 1 • Momentum`
     - `subtitle_es`: `Genera demanda`, `subtitle_en`: `Generate demand`
     - `price_usd`: `Decimal('697.00')`
     - `min_commitment_months`: `2`
     - `target_audience_es`: `Ideal para negocios que necesitan atraer interesados.`
     - `order_type`: `ADS_AI`
     - 7 bullets reales: Diagnóstico comercial inicial, Definición de oferta, buyer y canal, Revisión de Meta Business Suite, Configuración y lanzamiento de Meta Ads, Testeo de anuncios y creativos, Análisis de resultados y optimización, Recomendación del mejor destino: web, booking, formulario o WhatsApp.
  2. **Plan 2 • Conversión (Recomendado):**
     - `slug`: `conversion`
     - `name_es`: `Plan 2 • Conversión`, `name_en`: `Plan 2 • Conversion`
     - `subtitle_es`: `Convierte oportunidades`, `subtitle_en`: `Convert opportunities`
     - `price_usd`: `Decimal('1297.00')`
     - `min_commitment_months`: `3`
     - `is_highlighted`: `True`
     - `target_audience_es`: `Ideal para negocios que reciben consultas, pero pierden oportunidades.`
     - `order_type`: `ADS_AI`
     - 7 bullets reales: Todo lo del Plan Impulso, Diseño del embudo de conversión, CRM / pipeline comercial básico, Automatización de respuestas y seguimiento, Agenda, confirmaciones y recordatorios, Guión comercial de atención y cierre, Métricas de conversión: citas, show rate, close rate y CAC.
  3. **Plan 3 • Crecimiento:**
     - `slug`: `crecimiento`
     - `name_es`: `Plan 3 • Crecimiento`, `name_en`: `Plan 3 • Growth`
     - `subtitle_es`: `Vende más y fideliza`, `subtitle_en`: `Sell more and retain`
     - `price_usd`: `Decimal('1997.00')`
     - `min_commitment_months`: `3`
     - `target_audience_es`: `Ideal para negocios que ya venden y quieren crecer con su base de clientes.`
     - `order_type`: `STUDIOS`
     - 7 bullets reales: Todo lo del Plan Conversión, Estrategias de recompra y postventa, Reactivación de clientes antiguos, Solicitud de reseñas y referidos, Upsell y cross-sell, Segmentación de base de clientes, Métricas de crecimiento: recompra, LTV y escalamiento.
  - Disclaimer legal común:
    - `disclaimer_es`: `*La inversión publicitaria en Meta Ads y las herramientas de terceros no están incluidas. Los valores base consideran 1 negocio, 1 ubicación y 1 oferta principal.`
- [x] Ejecutar el seeder para actualizar la base de datos:
  ```bash
  python manage.py seed_subscription_plans
  ```

---

### Tarea 3.15: Rediseño de Alta Fidelidad del Catálogo `/precios/` con Formspree

- [x] Actualizar `templates/billing/pricing.html`:
  - Cabecera: *"Planes de Acompañamiento"* / *"Marketing Digital & Ventas para negocios locales"*.
  - Renderizado bilingüe de subtítulos, badges de compromiso (`Acompañamiento mínimo: X meses`) y público objetivo (`Ideal para...`).
  - Badge neón destacado en el Plan 2: *"RECOMENDADO"*.
  - Disclaimer legal al pie de los 3 planes.
  - Banner inferior de diagnóstico:
    - Titular: *"Agenda un diagnóstico y descubre cuál plan necesita tu negocio"*.
    - Botón CTA *"Hablemos hoy"* que abre un modal con formulario conectado a **Formspree.io** (`https://formspree.io/f/...`) o ancla a un formulario limpio.
    - Badges de valor: *Innovación • Creatividad • Resultados • Sin límites*.

---

### Tarea 3.16: Pruebas Automatizadas y Verificación de Aceptación

- [x] Actualizar suite de pruebas en `fobandor/billing/tests/`:
  - Test de creación de `SubscriptionPlan` con campos extendidos.
  - Test de listado y edición de planes en `/backoffice/planes/` para usuarios staff.
  - Test de bloqueo para usuarios anónimos o no-staff.
- [x] Ejecutar suite completa:
  ```bash
  python manage.py check
  pytest
  flake8 config fobandor scripts
  npm run build:css
  ```
- [x] Commit y push:
  ```bash
  git add .
  git commit -m "feat(billing): planes de acompanamiento reales, cms en backoffice y formspree"
  git push origin main
  ```

---

## 6. Etapa 4 — SEO Técnico, Auditoría OWASP, Empaquetado Docker y Despliegue en Producción (Hostinger VPS / EasyPanel)

> **Gobernanza Multi-Agente:**
> * **Diseñado y Validado por:** Antigravity-IDE (Arquitecto de Software Senior)
> * **Agente Ejecutor:** OpenCode (DeepSeek V4 Pro / TDD & Clean Architecture)
> * **Estado Actual:** FASE 4: EJECUTADA Y VALIDADA EN PRODUCCIÓN EN VIVO. Plataforma 100% operativa en `https://fobandor.com/` y `https://www.fobandor.com/` con SSL Traefik/Let's Encrypt. Release `v1.0.0` etiquetado.

---

### Notas de Corrección (revisión técnica OpenCode, aplicadas)

1. **`production.py`** define `DATABASES = {"default": env.db("DATABASE_URL")}` (base.py no lo define).
2. **`collectstatic` se mueve a `entrypoint.sh`** (runtime, settings de producción + env inyectadas); se elimina del Dockerfile (evita fallo en build sin `SECRET_KEY` y estáticos sin manifest).
3. **`Site.domain`** se fija con management command `setup_production_site` (`www.fobandor.com`), ejecutado en `entrypoint.sh` (sitemap y callbacks allauth con URL absoluta válida).
4. **Email diferido:** `ACCOUNT_EMAIL_VERIFICATION = env(..., default='optional')` en producción y SMTP configurable por env. El gate de checkout (`is_email_verified`) se mantiene (verificación manual vía admin o login Google auto-verificado).
5. **`CSRF_COOKIE_HTTPONLY = False`** (requerido para HTMX/JS). Solo `SESSION_COOKIE_HTTPONLY=True`.
6. **`check --deploy` limpio:** `SECURE_SSL_REDIRECT = True`, `SECURE_REFERRER_POLICY = "same-origin"` y `SECURE_HSTS_PRELOAD = False` (hasta validar SSL en vivo). W009 depende de una `SECRET_KEY` real en producción.
7. **`media/`** requiere volumen persistente en EasyPanel (`/app/media/`) para entregables.
8. **`.dockerignore`** añade `static/css/output.css` y `backups/`.
9. **`createsuperuser`** no interactivo (`--noinput` + `DJANGO_SUPERUSER_EMAIL/PASSWORD`).
10. **`FORMSPREE_ENDPOINT`** real en EasyPanel (no placeholder).

---

### Resumen de Alcance (Etapa 4)

1. **SEO Técnico y Metadatos Dinámicos:**
   - Mapa de sitio XML bilingüe (`/sitemap.xml`) con `django.contrib.sitemaps`.
   - Archivo `/robots.txt` optimizado para indexación en motores de búsqueda.
   - Metadatos completos de Open Graph y Twitter Cards (`og:title`, `og:description`, `og:image`, `og:url`) en `templates/base.html`.
2. **Blindaje de Seguridad OWASP y Configuración de Producción:**
   - Módulo `config/settings/production.py` con `DEBUG = False`.
   - Headers de proxy inverso para Traefik: `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`.
   - Servicio de archivos estáticos locales de alta velocidad con **WhiteNoise** (compresión Brotli/Gzip y caché inmutable, cumpliendo estrictamente con *Zero External CDN*).
   - Cookies seguras (`HttpOnly`, `Secure`, `SameSite=Lax`), HSTS a 1 año, protección XSS y Clickjacking (`X_FRAME_OPTIONS = 'DENY'`).
   - Auditoría automatizada con `python manage.py check --deploy`.
3. **Empaquetado Docker Multi-Etapa de Producción:**
   - `Dockerfile` multi-stage: compilación de Tailwind CSS con Node.js + runtime liviano Python 3.14 con usuario no-root `django`.
   - Script de arranque `entrypoint.sh` automatizado: migraciones (`migrate`), seeders (`seed_initial_content`, `seed_subscription_plans`, `create_rbac_groups`) y servidor WSGI Gunicorn (3 workers).
4. **Despliegue en Vivo en Hostinger VPS (`89.117.32.46` / EasyPanel):**
   - Creación del proyecto `fobandor` en EasyPanel con base de datos PostgreSQL 16 y servicio Web conectado a GitHub.
   - Vinculación con los dominios oficiales `fobandor.com` y `www.fobandor.com`.
   - Emisión automática de certificados SSL HTTPS por Traefik (Let's Encrypt).
   - Verificación de aceptación técnica en vivo en la web pública y en el Backoffice.

---

### Árbol de Archivos Objetivo (Etapa 4 — Incremental)

```text
fobandor/
├── Dockerfile
├── .dockerignore
├── entrypoint.sh
├── requirements/
│   └── base.txt                       (añade gunicorn y whitenoise)
├── config/
│   ├── urls.py                        (añade rutas sitemap y robots)
│   └── settings/
│       └── production.py              (configuración de seguridad y WhiteNoise)
├── fobandor/
│   └── core/
│       ├── sitemaps.py                (sitemap bilingüe de vistas públicas)
│       └── tests/
│           └── test_seo.py            (tests de sitemap, robots y headers)
└── templates/
    ├── robots.txt                     (directivas para bots de búsqueda)
    └── base.html                      (metadatos Open Graph y Twitter Cards)
```

---

### Tarea 4.0: Dependencias de Producción y Serving Estático

- [x] Añadir a `requirements/base.txt`:
  ```text
  gunicorn>=22.0.0
  whitenoise[brotli]>=6.6.0
  ```
- [x] Instalar en el entorno virtual:
  ```bash
  pip install -r requirements/base.txt
  ```

---

### Tarea 4.1: SEO Técnico, Open Graph, Sitemap e i18n (`robots.txt`, `sitemap.xml`)

- [x] Crear `fobandor/core/sitemaps.py`:
  ```python
  from django.contrib.sitemaps import Sitemap
  from django.urls import reverse


  class StaticViewSitemap(Sitemap):
      priority = 0.8
      changefreq = 'weekly'

      def items(self):
          return [
              ('core:home', 'es'),
              ('core:home', 'en'),
              ('billing:pricing', 'es'),
              ('billing:pricing', 'en'),
          ]

      def location(self, item):
          view_name, lang = item
          from django.utils import translation
          with translation.override(lang):
              return reverse(view_name)
  ```
- [x] Configurar `django.contrib.sitemaps` en `INSTALLED_APPS` en `config/settings/base.py`.
- [x] Crear vista y plantilla `templates/robots.txt`:
  ```text
  User-agent: *
  Allow: /
  Disallow: /admin/
  Disallow: /backoffice/
  Disallow: /mi-cuenta/
  Disallow: /stripe/

  Sitemap: https://www.fobandor.com/sitemap.xml
  ```
- [x] Registrar rutas `/sitemap.xml` y `/robots.txt` en `config/urls.py` (fuera de `i18n_patterns`):
  ```python
  from django.contrib.sitemaps.views import sitemap
  from django.views.generic import TemplateView
  from fobandor.core.sitemaps import StaticViewSitemap

  sitemaps = {
      'static': StaticViewSitemap,
  }

  urlpatterns = [
      path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
      path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
      path("i18n/", include("django.conf.urls.i18n")),
      path("accounts/", include("allauth.urls")),
      path("stripe/webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
  ]
  ```
- [x] Enriquecer `templates/base.html` con etiquetas Open Graph y Twitter Cards dinámicas:
  - `og:site_name`: "FOBANDOR"
  - `og:title`: "FOBANDOR — Ideas, código y creatividad impulsados por IA"
  - `og:description`: "Build. Advertise. Entertain. With AI. Marketing Digital, Apps y Producción Audiovisual en Orlando, FL."
  - `og:image`: `https://www.fobandor.com/static/images/favicons/apple-touch-icon.png`
  - `og:url`: `https://www.fobandor.com/`
  - `twitter:card`: `summary_large_image`
- [x] Crear suite de pruebas automatizadas en `fobandor/core/tests/test_seo.py`:
  ```python
  import pytest
  from django.urls import reverse


  @pytest.mark.django_db
  def test_robots_txt_status_and_content(client):
      response = client.get("/robots.txt")
      assert response.status_code == 200
      assert "text/plain" in response.headers["content-type"]
      content = response.content.decode()
      assert "User-agent: *" in content
      assert "Allow: /" in content
      assert "Disallow: /admin/" in content
      assert "Disallow: /backoffice/" in content
      assert "Disallow: /mi-cuenta/" in content
      assert "Disallow: /stripe/" in content
      assert "Sitemap: https://www.fobandor.com/sitemap.xml" in content


  @pytest.mark.django_db
  def test_sitemap_xml_status_and_urls(client):
      response = client.get("/sitemap.xml")
      assert response.status_code == 200
      assert "xml" in response.headers["content-type"]
      content = response.content.decode()
      assert "<urlset" in content
      assert "/es/" in content
      assert "/en/" in content
      assert "/es/precios/" in content
      assert "/en/precios/" in content


  @pytest.mark.django_db
  def test_open_graph_meta_tags_rendered(client):
      response = client.get(reverse("core:home"))
      assert response.status_code == 200
      content = response.content.decode()
      assert 'property="og:site_name" content="FOBANDOR"' in content
      assert 'property="og:title"' in content
      assert 'property="og:description"' in content
      assert 'property="og:image"' in content
      assert 'name="twitter:card" content="summary_large_image"' in content
  ```
- [x] Crear management command `fobandor/core/management/commands/setup_production_site.py` para garantizar que `Site.domain` y `Site.name` apunten a `www.fobandor.com` en producción (corrigiendo URLs de sitemap y callbacks de allauth):
  ```python
  from django.core.management.base import BaseCommand
  from django.contrib.sites.models import Site
  from django.conf import settings


  class Command(BaseCommand):
      help = "Configura el dominio del Site oficial para sitemaps, emails y allauth"

      def handle(self, *args, **options):
          site_id = getattr(settings, "SITE_ID", 1)
          domain = "www.fobandor.com"
          name = "FOBANDOR"
          site, created = Site.objects.update_or_create(
              id=site_id,
              defaults={"domain": domain, "name": name}
          )
          action = "creado" if created else "actualizado"
          self.stdout.write(self.style.SUCCESS(f"Site ID {site_id} {action} a {domain} ({name})"))
  ```

---

### Tarea 4.2: Blindaje de Seguridad OWASP y Configuración de Producción (`config/settings/production.py`)

- [x] Implementar `config/settings/production.py`:
  ```python
  from .base import *  # noqa: F403
  from .base import BASE_DIR, env

  DEBUG = False

  SECRET_KEY = env('SECRET_KEY')

  # Base de Datos de Producción (PostgreSQL en EasyPanel)
  DATABASES = {
      'default': env.db('DATABASE_URL')
  }

  ALLOWED_HOSTS = env.list(
      'ALLOWED_HOSTS',
      default=['fobandor.com', 'www.fobandor.com', '89.117.32.46', 'localhost', '127.0.0.1']
  )

  CSRF_TRUSTED_ORIGINS = env.list(
      'CSRF_TRUSTED_ORIGINS',
      default=['https://fobandor.com', 'https://www.fobandor.com']
  )

  # Configuración para proxy inverso Traefik
  SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
  USE_X_FORWARDED_HOST = True
  USE_X_FORWARDED_PORT = True
  SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
  SECURE_REFERRER_POLICY = 'same-origin'

  # WhiteNoise: servicio eficiente de archivos estáticos compilados
  MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')  # noqa: F405
  STORAGES = {
      'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
      'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
  }

  # Blindaje de cookies y sesiones (CSRF_COOKIE_HTTPONLY=False requerido para HTMX)
  SESSION_COOKIE_SECURE = True
  SESSION_COOKIE_HTTPONLY = True
  SESSION_COOKIE_SAMESITE = 'Lax'
  CSRF_COOKIE_SECURE = True
  CSRF_COOKIE_HTTPONLY = False  # Permite lectura por HTMX/JS para envío de token CSRF
  CSRF_COOKIE_SAMESITE = 'Lax'

  # Cabeceras de seguridad HTTP (OWASP)
  SECURE_BROWSER_XSS_FILTER = True
  SECURE_CONTENT_TYPE_NOSNIFF = True
  X_FRAME_OPTIONS = 'DENY'
  SECURE_HSTS_SECONDS = 31536000  # 1 año
  SECURE_HSTS_INCLUDE_SUBDOMAINS = True
  SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=False)  # Activar tras verificar estabilidad

  # Email en producción (SMTP configurable con fallback seguro)
  EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
  EMAIL_HOST = env('EMAIL_HOST', default='')
  EMAIL_PORT = env.int('EMAIL_PORT', default=587)
  EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
  EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
  EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
  DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='FOBANDOR <noreply@fobandor.com>')
  ACCOUNT_EMAIL_VERIFICATION = env('ACCOUNT_EMAIL_VERIFICATION', default='optional')
  ```

---

### Tarea 4.3: Suite de Pruebas de Regresión y Auditoría de Seguridad Automatizada (`pytest`, `flake8`, `check --deploy`)

- [x] Ejecutar suite completa de pruebas unitarias y de integración:
  ```bash
  pytest
  ```
  - Validar que pasen el 100% de las pruebas (mínimo 31/31: 28 existentes + 3 nuevas de SEO/Metadatos).
- [x] Ejecutar auditoría de estilo y sintaxis:
  ```bash
  flake8 config fobandor scripts
  ```
  - Validar 0 errores ni advertencias de estilo.
- [x] Ejecutar chequeo formal de despliegue en entorno local:
  ```bash
  python manage.py check --deploy --settings=config.settings.production
  ```
- [x] Validar que retorne **0 advertencias o errores críticos** de seguridad OWASP.

---

### Tarea 4.4: Empaquetado Docker Multi-Etapa de Producción

- [x] Crear `.dockerignore`:
  ```text
  .git/
  .venv/
  node_modules/
  __pycache__/
  *.pyc
  db.sqlite3
  backups/
  static/css/output.css
  .pytest_cache/
  .coverage
  htmlcov/
  .env
  ```
- [x] Crear `Dockerfile` multi-stage:
  ```dockerfile
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

  COPY entrypoint.sh /app/entrypoint.sh
  ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
  ```
- [x] Crear `entrypoint.sh`:
  ```bash
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

  echo "==> Iniciando servidor Gunicorn en el puerto ${PORT:-8000}..."
  exec gunicorn config.wsgi:application \
      --bind 0.0.0.0:${PORT:-8000} \
      --workers 3 \
      --timeout 120 \
      --access-logfile - \
      --error-logfile -
  ```
- [x] Otorgar permisos de ejecución a `entrypoint.sh`: `chmod +x entrypoint.sh`.

---

### Tarea 4.5: Despliegue en EasyPanel (Hostinger VPS) y Verificación en Vivo

- [x] **Configuración en EasyPanel (`http://89.117.32.46:3000`):**
  1. Entrar al proyecto `fobandor`.
  2. Crear servicio **Database** (`postgres:16`):
     - Base de datos: `fobandor_db`
     - Usuario: `fobandor_user`
     - Contraseña segura generada por EasyPanel: `fsy7cv7fgi0kzedqetiu`.
  3. Crear servicio **App** (`web`):
     - Source: GitHub Repo `https://github.com/javieresquivelt-ux/fobandor-web` (rama `main`).
     - Build: Dockerfile (`/Dockerfile`).
     - Port: `8000`.
     - Domains: `fobandor.com`, `www.fobandor.com` (apuntando al puerto `8000`).
     - **Volumen Persistente (Mounts):**
       - Volumen persistente `fobandor_media` montado en `/app/media/`.
     - Environment Variables:
       - `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `SITE_DOMAIN`, `PORT=8000`, `DJANGO_SUPERUSER_EMAIL=fobandorgcp@gmail.com`.
  4. Presionar **Implementar** y verificar convergencia del servicio Swarm.
- [x] **Verificación de Aceptación Técnica en Vivo (100% CUMPLIDA):**
  - `https://fobandor.com/` → HTTP/2 302 -> `/es/` HTTP/2 200 con candado SSL válido emitido por Let's Encrypt / Traefik.
  - `https://www.fobandor.com/` → HTTP/2 302 -> `/es/` HTTP/2 200 con certificado válido.
  - `https://fobandor.com/robots.txt` → HTTP/2 200 (directivas y sitemap presente).
  - `https://fobandor.com/sitemap.xml` → HTTP/2 200 con `<urlset>` y URLs canónicas bilingües de `www.fobandor.com`.
  - `https://fobandor.com/es/precios/` → HTTP/2 200 muestra los 3 planes reales de Freddy Obando (Impulso $697, Conversión $1297, Crecimiento $1997).
  - `https://fobandor.com/static/css/output.css` → HTTP/2 200 servido con WhiteNoise (Brotli/Gzip) y HSTS.
  - `https://fobandor.com/es/backoffice/` → HTTP/2 302 redirige a `/accounts/login/` con cookie `csrftoken` segura.
  - Superusuario `fobandorgcp@gmail.com` creado en PostgreSQL de producción.
  - Repositorio sincronizado en GitHub con tag oficial de release `v1.0.0`.

---

### Tarea 4.6: Hotfix de Post-Despliegue — Auto-vinculación de Google OAuth y Blindaje Operativo

- [x] **Diagnóstico y Causa Raíz de Incidentes de Producción:**
  1. *Fallo de Google OAuth ("Account already exists with this email address"):* Al existir previamente `fobandorgcp@gmail.com` en PostgreSQL como superusuario, Allauth rechazaba la autenticación de Google por requerir confirmación explícita de vinculación.
  2. *Pantallas sin estilos:* `/accounts/google/login/` y `/accounts/3rdparty/signup/` carecían de plantillas con diseño corporativo en el proyecto.
  3. *Error 502 Bad Gateway:* EasyPanel inyectaba `PORT=80` por defecto en tiempo de ejecución, causando que Gunicorn escuchara en el puerto 80 mientras Traefik enrutaba al puerto 8000.
  4. *Error de conexión a PostgreSQL:* EasyPanel autogeneró una contraseña para `fobandor_user` distinta a la que se configuró en `DATABASE_URL` (`fobandor_db`).
- [x] **Implementación del Hotfix:**
  - `config/settings/base.py`:
    ```python
    SOCIALACCOUNT_LOGIN_ON_GET = True
    SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
    SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
    ```
  - `templates/socialaccount/login.html`: plantilla con Tailwind CSS para confirmación de conexión de cuenta.
  - `templates/socialaccount/signup.html`: plantilla con Tailwind CSS para registro social completado.
  - `entrypoint.sh`: fijado explícito de `PORT=8000` previo a la llamada de Gunicorn.
  - Base de Datos de Producción: sincronización de credencial mediante `ALTER USER fobandor_user WITH PASSWORD 'fobandor_db';`.
- [x] **Verificación y Criterios de Aceptación:**
  - Suite de pruebas automatizadas: 31/31 tests pasando (`pytest`).
  - Linter: `flake8 config fobandor scripts` sin errores.
  - Login verificado en `/es/admin` para `fobandorgcp@gmail.com` con `Fobandor2026Admin!`.
  - Redirección OAuth directa sin pantallas intermedias.

---

### Tarea 4.7: Transición a Google Workspace Corporativo y Gestión de Administradores Oficiales (`for@fobandor.com` y `jet@fobandor.com`)

> **Estado Actual:** FASE 4: EJECUTADA Y VALIDADA EN PRODUCCIÓN. Superusuarios creados en PostgreSQL y credenciales de Google Workspace activas en VPS.

- [x] **Contexto:**
  - Freddy Obando adquirió el dominio oficial en Google Workspace (`fobandor.com`).
  - Se definen dos cuentas de administración corporativa:
    1. `for@fobandor.com` (Freddy Obando / Propietario).
    2. `jet@fobandor.com` (Desarrollador Fullstack Líder / Arquitecto).
  - Se generaron nuevas credenciales en Google Cloud Console vinculadas al proyecto de Workspace:
    - `GOOGLE_OAUTH_CLIENT_ID`: (valor generado para Workspace en `.env`)
    - `GOOGLE_OAUTH_CLIENT_SECRET`: (valor generado para Workspace en `.env`)
- [x] **Desglose de Acciones Atómicas:**
  1. **Actualización de Entorno en EasyPanel (Hostinger VPS):**
     - Variables de entorno actualizadas en servicio Swarm `fobandor_web` con las nuevas credenciales de Google Workspace.
     - Servicio convergido y contenedor reiniciado exitosamente.
  2. **Creación / Registro de Superusuarios en PostgreSQL de Producción:**
     - Aprovisionamiento ejecutado exitosamente en la base de datos de producción:
       - `for@fobandor.com`: staff=True, superuser=True, verified=True.
       - `jet@fobandor.com`: staff=True, superuser=True, verified=True.
  3. **Verificación de Criterios de Aceptación:**
     - Ambas cuentas creadas con `is_staff=True`, `is_superuser=True`, `is_email_verified=True`.
     - Login exitoso con contraseña de respaldo `Fobandor2026Admin!`.
     - Login exitoso vía Google OAuth con auto-vinculación transparente en 1 clic para ambas cuentas corporativas en `https://www.fobandor.com/accounts/login/`.

---

### Tarea 4.8: Integración de Formspree Real para Diagnóstico Comercial en `/precios/`

> **Estado Actual:** FASE 3: APROBAR. En espera de la aprobación explícita del Desarrollador Líder y de la recepción del Endpoint / Form ID generado por Freddy Obando.

- [ ] **Contexto:**
  - En la vista comercial `/es/precios/` y `/en/pricing/`, además del flujo de compra directa con Stripe Checkout, existe un botón destacado *"Hablemos hoy"* ("Let's Talk Today") que abre un modal de captación de prospectos para diagnósticos a medida.
  - Actualmente dicho formulario apunta a un endpoint de prueba (`https://formspree.io/f/placeholder`).
  - Freddy Obando se encuentra configurando el formulario real en su consola de Formspree vinculado a `for@fobandor.com`.
- [ ] **Desglose de Acciones Atómicas:**
  1. **Parametrización de Entorno (12-Factor):**
     - Configurar `FORMSPREE_ENDPOINT=https://formspree.io/f/<ID_REAL>` en `.env` (desarrollo local).
     - Actualizar variable de entorno `FORMSPREE_ENDPOINT` en el servicio `fobandor_web` de EasyPanel en el VPS (`89.117.32.46`).
     - Mantener `.env.example` actualizado con el placeholder descriptivo.
  2. **Mejora de UX y Blindaje en Plantilla (`templates/billing/pricing.html`):**
     - **Envío Asíncrono con Alpine.js:** Migrar el submit síncrono estándar a un flujo asíncrono vía `fetch()` con encabezado `Accept: application/json`.
       - Evita la redirección externa a la página genérica de Formspree.
       - Deshabilita el botón de envío y muestra spinner / texto *"Enviando diagnóstico..."* durante la petición.
       - Muestra mensaje de éxito reactivo dentro del modal: *"¡Gracias! Hemos recibido tu solicitud. Freddy Obando se contactará contigo en menos de 24 horas."*.
       - Manejo elegante de fallas de red con mensaje de reintento o contacto directo a `for@fobandor.com`.
     - **Metadatos y Protección Anti-Spam Formspree:**
       - Agregar campo oculto `<input type="hidden" name="_subject" value="Nuevo Diagnóstico Comercial - FOBANDOR">` para facilitar la identificación de leads en el inbox de Freddy.
       - Agregar campo honeypot silencioso `<input type="text" name="_gotcha" style="display:none">` para descartar envíos automáticos de bots sin molestar al usuario con captchas.
  3. **Pruebas y Verificación de Aceptación:**
     - Pruebas unitarias en `fobandor/billing/tests/test_views.py` para asegurar que `PricingCatalogView` inyecta correctamente `formspree_endpoint` en el contexto.
     - Ejecución de `pytest` (garantizar 100% passing).
     - Envío de prueba en producción desde `https://www.fobandor.com/es/precios/`.
     - Confirmación de recepción del lead de diagnóstico en la bandeja de entrada de `for@fobandor.com` y en el dashboard de Formspree.

