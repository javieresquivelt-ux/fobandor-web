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

## 5. Planificación de Próximas Etapas (Roadmap Anticipado)

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
