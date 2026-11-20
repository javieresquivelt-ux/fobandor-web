# TASK.MD: Plan de Ejecución Atómica y Hoja de Ruta — FOBANDOR

> **Gobernanza Multi-Agente:**  
> * **Diseñado y Validado por:** Antigravity-IDE (Arquitecto de Software Senior)  
> * **Agente Ejecutor:** OpenCode (DeepSeek V4 Pro / TDD & Clean Architecture)  
> * **Estado Actual:** FASE 5: REGISTRAR (Etapa 13 — Contraste Inteligente de Logotipo en Modo Claro completada con éxito con 48/48 pruebas pasando).

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

> **Estado Actual:** FASE 4: EJECUTADA. Formspree real (`https://formspree.io/f/mqpqqggk`) integrado con envío asíncrono, honeypot y metadatos. Pendiente verificación de recepción del lead en producción.

- [x] **Contexto:**
  - En la vista comercial `/es/precios/` y `/en/pricing/`, además del flujo de compra directa con Stripe Checkout, existe un botón destacado *"Hablemos hoy"* ("Let's Talk Today") que abre un modal de captación de prospectos para diagnósticos a medida.
  - Actualmente dicho formulario apunta a un endpoint de prueba (`https://formspree.io/f/placeholder`).
  - Freddy Obando se encuentra configurando el formulario real en su consola de Formspree vinculado a `for@fobandor.com`.
- [x] **Desglose de Acciones Atómicas:**
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

---

### Tarea 4.9: Correcciones de Textos del Modal de Diagnóstico e Integración al CMS

> **Estado Actual:** FASE 4: EJECUTADA. Correcciones de texto del modal integradas al CMS (`CompanyProfile`) con fusión A+B (una sola migración).

- [x] **Contexto:**
  - El formulario de diagnóstico comercial en `/es/precios/` fue entregado y verificado en producción (Tarea 4.8).
  - Freddy Obando solicita 2 correcciones de texto inmediatas + la integración de los textos configurables al CMS del Backoffice para que el equipo editorial pueda actualizarlos en el futuro sin intervención técnica.

- [x] **Desglose de Acciones Atómicas:**

  **Sub-tarea A — Correcciones inmediatas de textos (impacto bajo, sin migraciones)**

  1. **Asunto del formulario (`_subject`):**
     - Cambiar en `templates/billing/pricing.html`:
       ```html
       <!-- Antes -->
       <input type="hidden" name="_subject" value="Nuevo Diagnóstico Comercial - FOBANDOR">
       <!-- Después -->
       <input type="hidden" name="_subject" value="Nuevo Formulario Web - FOBANDOR">
       ```
  2. **Título del estado de éxito en el modal:**
     - Cambiar en `templates/billing/pricing.html` línea `{% trans "Solicita tu diagnóstico" %}` → `{% trans "Solicitud enviada" %}` (solo en el bloque `x-show="submitted"`).
     - **Nota:** El título "Solicita tu diagnóstico" del encabezado del formulario activo queda igual; solo cambia el título del estado de confirmación.
  3. **Mensaje de confirmación de éxito:**
     - Cambiar en `templates/billing/pricing.html`:
       ```
       Antes: "¡Gracias! Hemos recibido tu solicitud. Freddy Obando se contactará contigo en menos de 24 horas."
       Después: "¡Gracias! Hemos recibido tu solicitud. Nos contactaremos a la brevedad."
       ```
  4. **Actualización del catálogo de traducción EN:**
     - Actualizar las cadenas correspondientes en `locale/en/LC_MESSAGES/django.po`:
       - `"Thank you! We received your request. Freddy Obando will contact you within 24 hours."` → `"Thank you! We received your request. We will get back to you shortly."`
       - `"Request sent"` → nueva cadena para `"Solicitud enviada"`.
     - Recompilar el catálogo `.mo` con `scripts/build_translations.py`.

  **Sub-tarea B — Integración al CMS (factibilidad: ALTA ✅)**

  > **Análisis de Factibilidad:**
  > El modelo `CompanyProfile` (`fobandor/cms/models.py`) ya es un singleton con patrón `load()`, backoffice dedicado en `/backoffice/empresa/`, formulario bilingüe (Español/Inglés) y es el lugar arquitectónicamente correcto para albergar configuraciones globales del sitio.
  >
  > **Decisión:** Extender `CompanyProfile` con 4 campos nuevos para los textos del modal de diagnóstico. Esto es preferible a crear un nuevo modelo para evitar sobre-modelado y mantener un único punto de configuración para los administradores.

  5. **Migración del modelo `CompanyProfile` (`fobandor/cms/models.py`):**
     - Agregar 4 campos nuevos al modelo `CompanyProfile`:
       ```python
       # Formulario de diagnóstico / modal de precios
       diag_form_subject = models.CharField(
           'Asunto del formulario (Formspree)',
           max_length=200,
           default='Nuevo Formulario Web - FOBANDOR'
       )
       diag_modal_title_es = models.CharField(
           'Título del modal tras envío (ES)',
           max_length=100,
           default='Solicitud enviada'
       )
       diag_modal_title_en = models.CharField(
           'Modal title after submit (EN)',
           max_length=100,
           default='Request sent'
       )
       diag_success_msg_es = models.TextField(
           'Mensaje de éxito (ES)',
           default='¡Gracias! Hemos recibido tu solicitud. Nos contactaremos a la brevedad.'
       )
       diag_success_msg_en = models.TextField(
           'Success message (EN)',
           default='Thank you! We received your request. We will get back to you shortly.'
       )
       ```
     - Generar y aplicar migración: `makemigrations cms` + `migrate`.

  6. **Inyección del perfil en la vista `PricingCatalogView` (`fobandor/billing/views.py`):**
     - Importar `CompanyProfile` y agregar al contexto:
       ```python
       from fobandor.cms.models import CompanyProfile
       ctx['company'] = CompanyProfile.load()
       ```

  7. **Actualización de `templates/billing/pricing.html`:**
     - Reemplazar los textos estáticos del modal por variables de contexto dinámicas:
       ```html
       <!-- Antes -->
       <h4>{% trans "Solicita tu diagnóstico" %}</h4>
       <input type="hidden" name="_subject" value="Nuevo Formulario Web - FOBANDOR">
       <p>{% trans "¡Gracias! Hemos recibido tu solicitud. Nos contactaremos a la brevedad." %}</p>

       <!-- Después -->
       <h4>{% trans "Solicita tu diagnóstico" %}</h4>
       <input type="hidden" name="_subject" value="{{ company.diag_form_subject }}">
       <p>{% if LANGUAGE_CODE == 'es' %}{{ company.diag_success_msg_es }}{% else %}{{ company.diag_success_msg_en }}{% endif %}</p>
       ```
     - El título de éxito en `x-show="submitted"`:
       ```html
       <h4>{% if LANGUAGE_CODE == 'es' %}{{ company.diag_modal_title_es }}{% else %}{{ company.diag_modal_title_en }}{% endif %}</h4>
       ```

  8. **Actualización del formulario del Backoffice (`fobandor/backoffice/views.py` y `templates/backoffice/cms/company_profile_form.html`):**
     - Agregar los 5 nuevos campos al formulario `CompanyProfileUpdateView.fields`.
     - Agregar sección **"Formulario de Diagnóstico"** en el template del Backoffice con pestañas ES/EN para los campos bilingüales.

  9. **Verificación de Aceptación:**
     - `pytest` (target: 33/33 → al menos 33 passing, posibles tests nuevos de contexto).
     - `flake8` sin errores.
     - `python manage.py check` → 0 issues.
     - Verificar en `/es/backoffice/empresa/` que los nuevos campos aparecen y se pueden editar.
     - Cambiar un valor en el Backoffice y verificar que el modal de `/es/precios/` refleja el cambio en tiempo real (sin redeploy).

---

### Tarea 4.10: Activación y Validación de Stripe en Modo Test con Productos y Webhook Criptográfico

> **Estado Actual:** FASE 4: EJECUTADA Y VALIDADA. Credenciales de Stripe Sandbox activas en EasyPanel y VPS Swarm, Webhook configurado en Stripe Workbench, mapeo de Price IDs y tax code SaaS resuelto. Checkout funcional en `https://www.fobandor.com/es/precios/`.

- [x] **Contexto:**
  - Se acordó con el Desarrollador Líder probar primero la pasarela de pagos en Modo Test (Sandbox) de Stripe antes de realizar transacciones comerciales reales.
  - Se configuró el destino de Webhook en Stripe Workbench y se generaron las credenciales de prueba (`pk_test_...`, `sk_test_...` y `whsec_...`).
- [x] **Desglose de Acciones Atómicas Ejecutadas:**
  1. **Configuración de Webhook en Stripe Workbench:**
     - Destino registrado: `https://www.fobandor.com/stripe/webhook/` (formato Snapshot v1).
     - Eventos habilitados: `checkout.session.completed`, `invoice.paid`, `customer.subscription.updated`, `customer.subscription.deleted`.
     - Signing secret obtenido e inyectado en `STRIPE_WEBHOOK_SECRET`.
  2. **Parametrización de Entorno (12-Factor):**
     - `.env` local y variables del servicio Swarm `fobandor_web` en EasyPanel VPS (`89.117.32.46`) actualizadas con `STRIPE_PUBLIC_KEY`, `STRIPE_SECRET_KEY` y `STRIPE_WEBHOOK_SECRET`.
     - Servicio Swarm convergido y verificado.
  3. **Resolución de Price IDs vs Product IDs:**
     - Se identificó que en el Backoffice se habían cargado originalmente Product IDs (`prod_...`).
     - A través de la API de Stripe se extrajeron los Price IDs (`price_...`) exactos asociados a la recurrencia mensual:
       - Impulso ($697/mes): `price_1UczZNDd8zg4z4zarI1nFiTB`
       - Conversión ($1,297/mes): `price_1UczasDd8zg4z4za8jCoZZZa`
       - Crecimiento ($1,997/mes): `price_1UczbgDd8zg4z4zaCxHiSJao`
     - Base de datos local y de producción actualizadas con los Price IDs correspondientes.
  4. **Configuración de Tax Code para Stripe Managed Payments:**
     - Al detectar requerimiento de código fiscal por Managed Payments, se asignó vía API `tax_code="txcd_10000000"` (Software as a Service) a los 3 productos en Stripe.
  5. **Verificación de Aceptación:**
     - Creación de Stripe Checkout Sessions validada con éxito en local y en el contenedor de producción.
     - Suite de pruebas automatizadas: **34/34 tests pasando** (`pytest`).
     - Botón "Comenzar" en `/es/precios/` redirige fluidamente a la pasarela de pago alojada en Stripe (`https://checkout.stripe.com/c/pay/...`).

---

## 8. Etapa 5: Depuración de Hallazgos y Refinamiento Integral (Puntos 1 al 11)

> **Estado Actual:** FASE 4: EJECUTADA. Tareas 5.1 a 5.10 implementadas y verificadas (context processor de `company`, toggle de idioma, formulario de contacto, switches CMS, checkout GET, plan/asignación en SLA).  
> **Objetivo:** Resolver los 11 puntos identificados en la revisión de producción de `www.fobandor.com`, optimizando el frontend, responsive en móviles, flujo de compra Stripe y control operativo en el Backoffice CMS.  
> **Validación Técnica:** Revisado y corregido en conjunto con OpenCode (13 puntos de precisión fáctica y mejoras de robustez arquitectónica incorporados).
>
> **Notas de Ajuste Final (OpenCode):**
> 1. **`company` global vía context processor** (`fobandor.core.context_processors.company`): se inyecta `CompanyProfile.load()` en todas las plantillas (como `social_links`), de modo que el condicional de enlaces en el navbar funcione en cualquier página. `home_view` ya no inyecta `company` (solo `formspree_endpoint`), y `PricingCatalogView` deja de inyectarlo manualmente.
> 2. **`DEFAULT_ASSIGNEE_EMAIL`**: se resuelve con `getattr(settings, 'DEFAULT_ASSIGNEE_EMAIL', 'for@fobandor.com')` (no requiere añadir el setting a `base.py`).

---

### Tarea 5.1: Renderizado Dinámico de Misión, Visión y Valores en la Landing (Punto 1)
- [x] **Contexto:** En `fobandor.com/en/backoffice/empresa/` Freddy cargó los textos de Misión, Visión y Valores, pero la sección `#nosotros` en `templates/pages/home.html` sigue mostrando un texto estático de prueba.
- [x] **Acciones Atómicas:**
  1. En `fobandor/core/views.py` (`home_view`), inyectar en el diccionario de contexto el singleton institucional: `'company': CompanyProfile.load()`.
  2. En `templates/pages/home.html` (sección `#nosotros`), reemplazar el bloque de prueba por una maquetación corporativa que renderice:
     - Título y subtítulo bilingües.
     - Bloque de Misión: `{{ company.mission_es }}` / `{{ company.mission_en }}`.
     - Bloque de Visión: `{{ company.vision_es }}` / `{{ company.vision_en }}`.
     - Bloque de Valores: `{{ company.values_es }}` / `{{ company.values_en }}` renderizado con tarjetas limpias con estilo dark tech y acentos naranja/azul.
  3. Criterio de Aceptación: Al editar Misión, Visión o Valores en `/backoffice/empresa/`, el cambio se refleja inmediatamente en `https://www.fobandor.com/es/#nosotros` y `/en/#nosotros`.

---

### Tarea 5.2: Selector de Idioma con Botón Toggle Directo 1-Clic (Punto 2)
- [x] **Contexto:** El navbar actual usa un menú desplegable `<select>` que requiere dos clics e interrumpe la navegación fluida.
- [x] **Acciones Atómicas:**
  1. En `templates/partials/navbar.html`, sustituir el `<select>` desplegable por un botón interactivo de 1 clic tipo pill/switch.
  2. Implementar formulario con `set_language`:
     - Si el idioma actual es Español (`es`), mostrar botón conmutador hacia **`EN`** (o switch `ES | EN` con indicador activo).
     - Si el idioma actual es Inglés (`en`), mostrar botón conmutador hacia **`ES`**.
  3. Al hacer clic, enviar la petición directa POST a `{% url 'set_language' %}` preservando la URL activa y actualizando la sesión y la cookie `django_language`.
  4. Criterio de Aceptación: Cambio de idioma instantáneo en 1 solo clic tanto en desktop como en móvil.

---

### Tarea 5.3: Estandarización de Enlaces Canónicos en Navbar, Hero y Depuración de Ancla Precios (Puntos 3 y 7)
- [x] **Contexto:** 
  - Estando en `/es/precios/`, los enlaces del navbar son anclas relativas puras (`href="#servicios"`), provocando que fallen al no existir esas secciones dentro de precios.
  - En la landing page, el enlace "Precios" apunta a `#precios` (ancla obsoleta) en vez de redirigir a `/precios/`.
  - Existe un placeholder huérfano `<section id="precios">` en `home.html` (líneas 73-79) que debe ser eliminado.
- [x] **Acciones Atómicas:**
  1. En `templates/partials/navbar.html`, estandarizar los enlaces de navegación para usar la ruta canónica con ancla:
     - Servicios: `href="{% url 'core:home' %}#servicios"`
     - Proyectos: `href="{% url 'core:home' %}#proyectos"`
     - Nosotros: `href="{% url 'core:home' %}#nosotros"`
     - Contacto: `href="{% url 'core:home' %}#contacto"` (condicionado a `{% if not company or company.show_contact_section %}`)
     - Precios: `href="{% url 'billing:pricing' %}"`
  2. En `templates/pages/home.html`:
     - Eliminar el bloque huérfano `<section id="precios">` (líneas 73-79).
     - Revisar y asegurar enlaces del Hero (`#servicios`, `#proyectos`).
  3. Criterio de Aceptación: Navegación consistente y sin enlaces muertos desde cualquier página del sitio.

---

### Tarea 5.4: Integración del Formulario Formspree en Sección Contacto de la Landing (Punto 4)
- [x] **Contexto:** La sección `#contacto` de la home muestra actualmente *"Contact form coming soon"*.
- [x] **Acciones Atómicas:**
  1. En `fobandor/core/views.py` (`home_view`), inyectar en el contexto `formspree_endpoint = getattr(settings, 'FORMSPREE_ENDPOINT', '')`.
  2. En `templates/pages/home.html`, maquetar en la sección `#contacto` un formulario integrado directo:
     - Campos: Nombre (`name`), Email (`email`), Teléfono (`phone`), Mensaje (`message`).
     - Metadatos: Asunto `{{ company.diag_form_subject }}` y honeypot anti-spam `_gotcha`.
     - Envío asíncrono con Alpine.js (`@submit.prevent` + `fetch()` con `Accept: application/json`).
     - Estados reactivos: Botón deshabilitado durante envío ("Enviando mensaje..."), feedback de éxito en verde y mensaje de contingencia en caso de error.
  3. Criterio de Aceptación: Los visitantes pueden enviar consultas directamente desde el pie de la landing page sin necesidad de abrir el modal, llegando directamente a Formspree / `administrator@fobandor.com`.

---

### Tarea 5.5: Switches de Visibilidad de Secciones de la Landing en CMS (Punto 5)
- [x] **Contexto:** Secciones sin contenido o en preparación no deben mostrarse con placeholders vacíos en la landing; Freddy debe poder activarlas o desactivarlas desde el Backoffice.
- [x] **Acciones Atómicas:**
  1. Modificar modelo `CompanyProfile` en `fobandor/cms/models.py` agregando los campos booleanos:
     - `show_services_section = models.BooleanField('Mostrar sección Servicios en Landing', default=True)`
     - `show_projects_section = models.BooleanField('Mostrar sección Proyectos en Landing', default=True)`
     - `show_about_section = models.BooleanField('Mostrar sección Nosotros en Landing', default=True)`
     - `show_contact_section = models.BooleanField('Mostrar sección Contacto en Landing', default=True)`
  2. Generar y aplicar migración de base de datos (`makemigrations cms` + `migrate`).
  3. En `templates/backoffice/cms/company_profile_form.html`, agregar bloque de switches o checkboxes "Visibilidad de Secciones en Landing".
  4. En `templates/pages/home.html`, envolver cada sección con su respectivo `{% if company.show_... %}`.
  5. En `templates/partials/navbar.html`, condicionar el enlace a la sección si está desactivada (evitando anclas muertas).
  6. Criterio de Aceptación: Desactivar una sección en `/backoffice/empresa/` oculta inmediatamente la sección y su ancla en `https://www.fobandor.com/`.

---

### Tarea 5.6: Corrección Responsive y Blindaje Móvil de Navbar en Celulares (Punto 6)
- [x] **Contexto:** En teléfonos Samsung A52, iPhone y pantallas `< 768px`, el navbar genera desbordamiento horizontal (`overflow-x`). El botón hamburguesa queda fuera de la pantalla visible y enlaces como "Mi Cuenta" y "Salir" se solapan en varias líneas.
- [x] **Acciones Atómicas:**
  1. En `templates/partials/navbar.html`:
     - Ocultar los enlaces de usuario ("Mi Cuenta", "Salir", "Iniciar sesión") en la barra superior móvil (`hidden md:flex`).
     - Mover dichos enlaces al interior del drawer desplegable del menú móvil (`x-show="mobileMenuOpen"`), formateados como ítems de lista grandes y cómodos para tocar con el pulgar.
     - La barra superior móvil solo contendrá: Isotipo FOBANDOR (izquierda), botón de cambio de idioma compacto (derecha) y botón de menú hamburguesa (derecha).
  2. En `templates/base.html` y estilos base, aplicar `overflow-x: clip` en lugar de `overflow-x: hidden` en `body` y contenedores para evitar romper el `position: sticky` del navbar.
  3. Criterio de Aceptación: En emulador y dispositivos móviles reales de 360px a 430px de ancho, la barra superior se mantiene 100% contenida sin scroll horizontal y el menú hamburguesa es perfectamente accesible.

---

### Tarea 5.7: Soporte GET en Checkout para Prevenir Error HTTP 405 (Punto 8)
- [x] **Contexto:** Cuando un usuario no autenticado hace clic en "Comenzar" en `/precios/`, el formulario envía un POST. Django redirige al login con `?next=/es/precios/checkout/impulso/`. Tras el login con Google OAuth, el navegador llega a esa URL vía **GET**, y Django retorna un error **HTTP 405 Method Not Allowed** porque la vista solo tiene `def post()`.
- [x] **Acciones Atómicas:**
  1. En `fobandor/billing/views.py` (`CreateCheckoutSessionView`), agregar el método GET:
     ```python
     def get(self, request, slug):
         return self.post(request, slug)
     ```
  2. Si el usuario llega vía GET (por redirección post-login), la vista genera directamente la sesión de Stripe Checkout y lo redirige a Stripe sin interrupción ni error 405.
  3. Escribir test en `fobandor/billing/tests/test_views.py` verificando que una petición GET autenticada a `/precios/checkout/<slug>/` responde con redirección 302 hacia Stripe Checkout, **mockeando `services.create_checkout_session`** para retornar una sesión simulada con `url="https://checkout.stripe.com/pay/test_session"`.
  4. Criterio de Aceptación: Flujo continuo desde "Comenzar" -> Login Google -> Stripe Checkout sin pantallas de error HTTP 405.

---

### Tarea 5.8: Verificación de Retorno y Personalización de Stripe Customer Portal (Punto 9)
- [x] **Contexto:** El retorno desde el portal de facturación de Stripe ya está implementado en `StripeCustomerPortalView.post` (`request.build_absolute_uri(reverse("portal:dashboard"))`). Falta documentar y verificar la personalización gráfica en Stripe Dashboard.
- [x] **Acciones Atómicas:**
  1. Verificar en test unitario existente que `StripeCustomerPortalView.post` construye y pasa el `return_url` canónico con prefijo de idioma del usuario (`/es/mi-cuenta/`).
  2. Documentar en la guía operativa el procedimiento en Stripe Dashboard (`Configuración > Portal de facturación > Personalización de marca`) para asegurar que Freddy suba el isotipo de FOBANDOR y colores de marca.
  3. Criterio de Aceptación: Retorno impecable y consistencia visual entre Stripe y FOBANDOR.

---

### Tarea 5.9: Registro del Nombre del Plan en Órdenes SLA del Backoffice (Punto 10)
- [x] **Contexto:** En `/es/backoffice/entregas/`, la tabla muestra el campo "Servicio" con un valor genérico (*Desarrollo Web con IA*), impidiendo al equipo de operaciones saber si el cliente adquirió el plan Impulso, Conversión o Crecimiento.
- [x] **Acciones Atómicas:**
  1. Modificar modelo `FulfillmentOrder` en `fobandor/fulfillment/models.py`:
     - Añadir campo: `plan = models.ForeignKey('billing.SubscriptionPlan', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Plan de Suscripción')`.
  2. Generar y aplicar migración en `fobandor/fulfillment/migrations/`.
  3. En `fobandor/billing/services.py` (`handle_invoice_paid`), asociar `plan` en el `defaults` del `get_or_create` de `FulfillmentOrder` (aprovechando la variable `plan` ya resuelta).
  4. En `templates/backoffice/fulfillment/order_list.html` y `order_detail.html`, mostrar en la columna Servicio:
     - `{{ order.plan.name_es|default:order.get_order_type_display }}`.
  5. Criterio de Aceptación: El operador del Backoffice visualiza claramente el nombre del plan comercial comprado en cada orden SLA.

---

### Tarea 5.10: Flujo Operativo SLA: Botón de Estado "En Proceso" y Campo "Asignado A" (Punto 11)
- [x] **Contexto:** El estado `"EN_PROCESO"` ya está definido en `FulfillmentOrder.STATUS_CHOICES`, pero no existe el campo de asignación de responsable ni un botón en la interfaz para transicionar la orden a producción activa.
- [x] **Acciones Atómicas:**
  1. Modificar `FulfillmentOrder` en `fobandor/fulfillment/models.py`:
     - Agregar campo: `assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_orders', verbose_name='Asignado a')` (utilizando el `User` ya importado en el modelo).
  2. En `fobandor/billing/services.py` (`handle_invoice_paid`), asignar por defecto a `DEFAULT_ASSIGNEE_EMAIL` (configurado en `settings`, default `'for@fobandor.com'`) si el usuario existe en BD.
  3. En `fobandor/backoffice/views.py` (`FulfillmentOrderDetailView` o formulario de orden):
     - Poblar el selector "Asignado a" filtrando usuarios que pertenezcan a los grupos `Fulfillment_Operators` o `Content_Editors`, o que tengan `is_staff=True`:
       `User.objects.filter(Q(groups__name__in=['Fulfillment_Operators', 'Content_Editors']) | Q(is_staff=True)).distinct()`.
     - Habilitar acción/botón para cambiar el estado a `EN_PROCESO` (*"Iniciar Producción"*).
  4. En `templates/backoffice/fulfillment/order_list.html` y `order_detail.html`:
     - Agregar columna "Asignado a".
     - Permitir filtrado por estado `EN_PROCESO` en las pestañas de listado.
  5. Actualizar y ampliar pruebas unitarias en `fobandor/fulfillment/tests/test_sla.py`.
  6. Criterio de Aceptación: Las órdenes pueden asignarse formalmente y transicionar por el flujo: `Pendiente de Producción` → `En Proceso` → `Entregada`.

---

## 9. Etapa 6: Mejoras de UX/UI — Selector Interactivo de Precios y Contraste de Inputs (Puntos 2 y 3)

> **Estado Actual:** FASE 4: EJECUTADA Y CERTIFICADA EN PRODUCCIÓN. Hover de precios con alto contraste garantizado; embudo de autenticación Allauth 100% maquetado con identidad corporativa de marca.  
> **Objetivo:** Resolver el contraste invisible en hover sobre los botones de precios y maquetar con diseño corporativo completo las pantallas de confirmación de correo (`verification_sent.html`, `email_confirm.html`, `password_reset_done.html`, `logout.html`).

---

### Tarea 6.1: Estandarización de Estilos y Contraste de Inputs en Formularios de Autenticación (Punto 2)
- [x] **Contexto:** En `/accounts/signup/`, `/accounts/login/` y `/accounts/password/reset/`, los campos de formulario se renderizan sin clases CSS Tailwind explícitas. En navegadores Chromium/Edge en modo oscuro, el navegador aplica fondo blanco al input mientras Tailwind hereda `color: inherit` desde el body (`#f3f4f6`, blanco), provocando que el texto tipeado y el placeholder sean blancos sobre fondo blanco (completamente invisibles).
- [x] **Acciones Atómicas:**
  1. En `static/css/input.css` (en `@layer base`), agregar reglas CSS universales para inputs de formulario:
     - Forzar fondo oscuro suave en dark mode: `.dark input[type="text"], .dark input[type="email"], .dark input[type="password"] { background-color: rgba(255, 255, 255, 0.07); color: #f3f4f6; border-color: rgba(255, 255, 255, 0.2); }`.
     - Forzar fondo blanco y texto oscuro en light mode: `input[type="text"], input[type="email"], input[type="password"] { background-color: #ffffff; color: #111827; }`.
  2. En `templates/account/signup.html`, `login.html` y `password_reset.html`:
     - Aplicar clases Tailwind dedicadas a cada input:
       `class="w-full rounded-xl border border-gray-300 dark:border-white/20 px-3.5 py-2.5 bg-white dark:bg-white/5 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:border-fobandor-orange focus:ring-1 focus:ring-fobandor-orange transition-colors"`.
  3. Recompilar `static/css/output.css` localmente.
  4. Criterio de Aceptación: En cualquier navegador (Chrome, Firefox, Safari, Edge) y tanto en modo claro como oscuro, todos los campos de texto tienen fondo, bordes y texto con contraste perfecto y legible.

---

### Tarea 6.2: Selector Interactivo de Planes con Efecto Hover y Selección Dinámica en `/precios/` (Punto 3)
- [x] **Contexto:** Las 3 tarjetas de planes en `/precios/` eran estáticas. Solo la marcada como destacada (`is_highlighted` en BD) tenía estilos fijos. Los otros planes no reaccionaban al mouse over ni permitían ser seleccionados con un clic previo a la compra, y si se desactivaba "Destacado", ninguna tarjeta lucía activa.
- [x] **Acciones Atómicas:**
  1. En `templates/billing/pricing.html`, implementar componente interactivo con **Alpine.js**:
     - Contenedor con estado reactivo:
       `x-data="{ selectedPlan: '{{ highlighted_slug }}' }"`
     - Preseleccionar el plan destacado si existe; si no, preseleccionar por defecto el primer plan (`plans.0.slug`).
  2. Añadir efecto Hover (`on mouse over`) en cada tarjeta:
     - `cursor-pointer transition-all duration-300 ease-out hover:-translate-y-1.5 hover:shadow-2xl hover:shadow-fobandor-orange/15 hover:border-fobandor-orange/70`.
  3. Selección activa al hacer clic:
     - Al hacer clic en cualquier parte de la tarjeta: `@click="selectedPlan = '{{ plan.slug }}'"`.
     - Tarjeta activa seleccionada dinámicamente:
       `:class="selectedPlan === '{{ plan.slug }}' ? 'border-fobandor-orange bg-fobandor-orange/5 ring-1 ring-fobandor-orange shadow-lg shadow-fobandor-orange/10' : 'border-gray-200 dark:border-white/10 bg-white/50 dark:bg-white/5'"`
     - Botón "Comenzar" de la tarjeta seleccionada adquiere el estilo naranja principal:
       `:class="selectedPlan === '{{ plan.slug }}' ? 'bg-fobandor-orange hover:bg-fobandor-orange/90 text-white shadow-lg shadow-fobandor-orange/20' : 'border border-gray-300 dark:border-white/20 hover:border-fobandor-orange text-gray-700 dark:text-gray-200 hover:text-white'"`
  4. Insignia visual:
     - Mantener la insignia `"RECOMENDADO"` en el plan con `plan.is_highlighted=True`.
     - Reflejar visualmente con un borde y foco activo qué tarjeta ha seleccionado el usuario.
  5. Escribir pruebas unitarias que verifiquen que `pricing.html` contiene los atributos Alpine reactivos (42/42 tests pasaron).
  6. Criterio de Aceptación: El usuario puede pasar el mouse sobre cualquiera de los 3 planes (notando elevación y borde iluminado) y seleccionar con un clic cualquiera de ellos, viendo reflejada la selección activa de inmediato.

---

### Tarea 6.3: Suite de Pruebas de Regresión, Compilación y Despliegue en VPS
- [x] **Contexto:** Garantizar cero regresiones y despliegue convergente de las mejoras UX/UI en Hostinger VPS.
- [x] **Acciones Atómicas:**
  1. Ejecutar suite completa `pytest` asegurando que todos los tests pasen (42 tests).
  2. Ejecutar linter `flake8` garantizando 0 errores de estilo.
  3. Compilar estáticos de Tailwind (`output.css`).
  4. Realizar commit semántico y push a `origin/main`.
  5. Desplegar en caliente en Hostinger VPS.
  6. Verificar en caliente en `https://www.fobandor.com/` el contraste de inputs y el selector de planes.
  7. Criterio de Aceptación: Navegación y formularios 100% legibles e interactivos en producción.

---

### Tarea 6.4: Refinamiento de UX/UI — Efecto Hover y Contraste del Botón "Comenzar" en `/precios/` (Punto 3)
- [x] **Contexto:** En [templates/billing/pricing.html](file:///home/jet/proyectos_lnx/proyectos/fobandor/templates/billing/pricing.html#L59), en las tarjetas no seleccionadas, el botón tiene la clase `hover:text-white` pero carece de `hover:bg-fobandor-orange`. En Modo Claro (Light Mode), al pasar el ratón por encima del botón "Comenzar", el texto cambia a color blanco sobre el fondo blanco/transparente de la tarjeta, volviéndose completamente invisible.
- [x] **Acciones Atómicas:**
  1. En `templates/billing/pricing.html`:
     - Reemplazar las clases del botón no seleccionado:
       - **Antes:** `'border border-gray-300 dark:border-white/20 hover:border-fobandor-orange text-gray-700 dark:text-gray-200 hover:text-white'`
       - **Ahora:** `'border-2 border-gray-300 dark:border-white/20 bg-gray-100 dark:bg-white/10 text-gray-900 dark:text-white hover:border-fobandor-orange hover:bg-fobandor-orange hover:text-white hover:shadow-lg hover:shadow-fobandor-orange/25'`
     - Mejorar el efecto hover de la tarjeta completa con elevación `-translate-y-2`, sombra perimetral naranja `hover:shadow-fobandor-orange/20` y fondo con tinte cálido sutil `hover:bg-fobandor-orange/[0.04] dark:hover:bg-white/[0.08]`.
  2. Criterio de Aceptación: En modo claro y oscuro, el botón no seleccionado tiene texto oscuro nítido (`text-gray-900`), y al hacer hover sobre él se rellena inmediatamente de color naranja corporativo con texto blanco en alto contraste. Cero texto blanco sobre fondo blanco.

---

### Tarea 6.5: Maquetación Corporativa del Embudo de Confirmación de Email y Cuenta de Allauth (Nuevo Hallazgo QA)
- [x] **Contexto:** Al completar el registro en `/accounts/signup/`, allauth redirige a `/accounts/confirm-email/` (`EmailVerificationSentView`). Como el archivo `templates/account/verification_sent.html` no existía, el framework cae al template por defecto de allauth en texto plano sin estilos, sin navbar, sin footer y en fuente Serif (Times New Roman), generando una experiencia rota ante el usuario final.
- [x] **Acciones Atómicas:**
  1. Crear `templates/account/verification_sent.html` extendiendo `base.html`:
     - Contenedor centrado y tarjeta corporativa con bordes redondeados y sombra.
     - Ícono gráfico elegante de correo/buzón con acentos en `fobandor-orange`.
     - Título: `Verifica tu dirección de correo electrónico`.
     - Mensaje claro y profesional: explica que se ha despachado un correo de activación, aconseja revisar carpetas de Spam / Correo no deseado y esperar 1-2 minutos.
     - Botones de navegación: volver al inicio (`{% url 'core:home' %}`) o ir a planes (`{% url 'billing:pricing' %}`).
  2. Actualizar `templates/account/email_confirm.html`:
     - Si la clave de confirmación es válida (`{% if confirmation %}`): mostrar mensaje de bienvenida y botón de acción principal "Activar mi cuenta" con estilo `bg-fobandor-orange hover:bg-fobandor-orange/90 text-white`.
     - Si la clave expiró o no es válida: advertencia visual y botón para solicitar reenvío o ir al login.
  3. Crear `templates/account/password_reset_done.html` y `templates/account/logout.html` asegurando que ninguna pantalla secundaria de autenticación quede sin estilos.
  4. Criterio de Aceptación: Todas las pantallas del embudo de registro, confirmación de correo y restablecimiento de credenciales heredan `base.html` con la identidad visual completa de FOBANDOR en dark y light mode.

---

### Tarea 6.6: Suite de Pruebas de Regresión, Compilación y Despliegue en VPS
- [x] **Contexto:** Validar ausencia de regresiones, compilar CSS y desplegar en Hostinger VPS.
- [x] **Acciones Atómicas:**
  1. Ejecutar suite completa `pytest` asegurando que todos los tests pasen (43 tests).
  2. Ejecutar linter `flake8` garantizando 0 errores.
  3. Recompilar `static/css/output.css`.
  4. Realizar commit semántico y push a `origin/main`.
  5. Desplegar imagen actualizada en Docker Swarm (`fobandor_web`).
  6. Verificar en vivo en `https://www.fobandor.com/` el hover de precios y la pantalla de verificación de correo.
  7. Criterio de Aceptación: Despliegue convergente y verificado en producción sin fallos.

---

## 10. Etapa 7: Implementación del Servicio de Correo Transaccional (SMTP) y Registro Blindado (Punto 1)

> **Estado Actual:** FASE 4: EJECUTADA Y CERTIFICADA EN PRODUCCIÓN. Correo SMTP de Google Workspace (`smtp.gmail.com`) activo y verificado en vivo con envío de correo exitoso. Registro blindado contra caídas con `CustomAccountAdapter.send_mail`.  
> **Objetivo:** Resolver definitivamente el Error 500 al registrar usuarios manuales en `/accounts/signup/` implementando el servicio formal de envío de correos transaccionales (SMTP) y blindando la resiliencia del sistema ante eventuales caídas del servidor de correo.

---

### Tarea 7.1: Aprovisionamiento y Configuración de Credenciales SMTP de Google (Workspace / Gmail)
- [x] **Contexto:** Para el envío de correos transaccionales de confirmación de cuenta y notificaciones, se configuró el servidor SMTP de Google (`smtp.gmail.com`). Autenticación mediante Contraseña de Aplicación de 16 dígitos (*App Password*) sobre la cuenta `administrator@fobandor.com`.
- [x] **Acciones Atómicas:**
  1. Definir los parámetros de conexión SMTP oficiales de Google:
     - `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`
     - `EMAIL_HOST=smtp.gmail.com`
     - `EMAIL_PORT=587`
     - `EMAIL_USE_TLS=True`
     - `EMAIL_HOST_USER=administrator@fobandor.com`
     - `EMAIL_HOST_PASSWORD=shsfmvaajpgxgfjk`
     - `DEFAULT_FROM_EMAIL=FOBANDOR <administrator@fobandor.com>`
  2. Inyectar estas variables en el servicio Swarm `fobandor_web` dentro de EasyPanel en el VPS (`89.117.32.46`).
  3. Probar conectividad y autenticación SMTP desde el contenedor ejecutando `python manage.py shell` y enviando un correo de prueba vía `django.core.mail.send_mail`.
  4. Criterio de Aceptación: Conexión SMTP autenticada contra `smtp.gmail.com` y entrega exitosa de correo de prueba al buzón del administrador (`EMAIL_SENT_COUNT: 1` verificado en vivo).

---

### Tarea 7.2: Configuración de Django allauth y Flujo de Verificación por Email
- [x] **Contexto:** Con el servicio SMTP activo, el registro de usuarios puede enviar formalmente el correo de confirmación de cuenta con enlace criptográfico para activar su cuenta.
- [x] **Acciones Atómicas:**
  1. En `config/settings/production.py`:
     - Activar `ACCOUNT_EMAIL_VERIFICATION = env("ACCOUNT_EMAIL_VERIFICATION", default="mandatory")`.
     - Configurar `ACCOUNT_EMAIL_REQUIRED = True` y `ACCOUNT_AUTHENTICATION_METHOD = "email"`.
  2. Personalizar las plantillas de correo de allauth (`templates/account/email/email_confirmation_subject.txt` y `email_confirmation_message.html` / `.txt`):
     - Asunto corporativo: `Confirma tu cuenta en FOBANDOR / Confirm your FOBANDOR account`.
     - Diseño bilingüe con estilo de marca (logo, colores de marca y enlace seguro de activación).
  3. Criterio de Aceptación: El usuario que se registra recibe de inmediato un correo formateado profesionalmente con el botón de activación de cuenta.

---

### Tarea 7.3: Blindaje Resiliente contra Fallos de Conexión SMTP en `CustomAccountAdapter`
- [x] **Contexto:** Para garantizar que una caída temporal de red o del proveedor de correo nunca genere una pantalla de `Server Error (500)` en blanco ante el usuario final, la aplicación debe capturar fallos a nivel de adaptador.
- [x] **Acciones Atómicas:**
  1. En `fobandor/users/adapters.py` (`CustomAccountAdapter`):
     - Sobreescribir `send_mail(self, template_prefix, email, context)`.
     - Envolver la llamada en `try...except Exception as exc:` con registro en el logger de advertencia.
     - Si el envío de correo falla, el usuario no recibe un error 500; se le informa de manera elegante que revise su correo o solicite reenvío.
  2. Escribir prueba unitaria en `fobandor/users/tests/test_gate.py`:
     - Simular fallo de socket SMTP y verificar que la vista responde con redirección HTTP 302 y mensaje de advertencia controlado sin 500.
  3. Criterio de Aceptación: Cero excepciones no capturadas ante fallos de servidor SMTP (Tests pasan 40/40).

---

### Tarea 7.4: Validación End-to-End en Producción
- [x] **Contexto:** Comprobar el ciclo completo en `https://www.fobandor.com/`.
- [x] **Acciones Atómicas:**
  1. Desplegar imagen `easypanel/fobandor/web:latest` compilada con commit `0645c5b`.
  2. Actualizar variables de entorno en el servicio Swarm `fobandor_web`.
  3. Verificar convergencia del servicio y estabilidad de tareas (`docker service ps fobandor_web`).
  4. Enviar email de prueba real vía shell dentro del contenedor hacia `administrator@fobandor.com` (`EMAIL_SENT_COUNT: 1`).
  5. Criterio de Aceptación: Flujo completo de registro, activación y servicio SMTP 100% verificado en vivo.




---

## 11. Etapa 8: Mapeo Resiliente de Plan y Servicio en Órdenes de Fulfillment (Punto Backoffice SLA)

> **Estado Actual:** FASE 4: EJECUTADA. Corrección de carrera de webhooks implementada (resolución multi-fuente vía `invoice.lines`/subscription por API, metadata en checkout, i18n, comando de reconciliación y test de regresión). Pendiente despliegue en VPS y reconciliación de las 2 órdenes huérfanas.
> **Nota de corrección (OpenCode):** `invoice.lines` NO viene en el payload del webhook por defecto; la resolución obtiene las líneas vía `stripe.Invoice.retrieve(expand=["lines.data.price"])` (fallback `stripe.Subscription.retrieve(expand=["items.data.price"])`).  
> **Objetivo:** Resolver la condición de carrera entre webhooks de Stripe (`invoice.paid` vs `checkout.session.completed`) para que las órdenes de entrega (`FulfillmentOrder`) registren siempre de forma certera el Plan contratado y el Servicio correspondiente, tanto en órdenes futuras como en las ya creadas en producción.

---

### Tarea 8.1: Detección y Resolución Multi-Fuente de Plan en `handle_invoice_paid`
- [x] **Contexto:** Actualmente, `handle_invoice_paid` asume que `CustomerSubscription` ya existe en base de datos. Como Stripe despacha `invoice.paid` antes o en paralelo a `checkout.session.completed`, la consulta a `CustomerSubscription` devuelve `None`, provocando que la orden se cree con `plan = None` y `order_type = "WEB_DEV"` por defecto.
- [x] **Acciones Atómicas:**
  1. En `fobandor/billing/services.py` (`handle_invoice_paid`):
     - Inspeccionar los ítems de la factura (`invoice.lines.data`).
     - Extraer el ID de precio (`line.price.id` o `line.plan.id`) y resolver el plan directamente mediante `SubscriptionPlan.objects.filter(stripe_price_id=price_id).first()`.
     - Si `subscription_id` está presente pero la suscripción aún no existía en BD, crearla o vincularla inmediatamente con `plan` y `status="active"`.
     - Asignar `order_type = plan.order_type` (ej. `"MARKETING"`).
     - Si la orden ya existía pero tenía `plan = None`, actualizarla retroactivamente en caso de reintentos del webhook.

---

### Tarea 8.2: Sincronización Bidireccional en `handle_checkout_completed` y Metadata en Checkout
- [x] **Contexto:** Reforzar la integridad referencial desde el evento `checkout.session.completed` y la creación de la sesión de pago.
- [x] **Acciones Atómicas:**
  1. En `create_checkout_session`:
     - Agregar `subscription_data={"metadata": {"user_id": str(user.pk), "plan_id": str(plan.pk)}}` para que el objeto suscripción de Stripe herede la metadata del plan.
  2. En `handle_checkout_completed`:
     - Al guardar `CustomerSubscription`, buscar órdenes de fulfillment huérfanas del usuario (`FulfillmentOrder.objects.filter(user=user, plan__isnull=True)`) y vincularles el `plan`, `subscription` y `order_type`.

---

### Tarea 8.3: I18n de Planes y Servicios en Vistas del Backoffice
- [x] **Contexto:** En `/en/backoffice/entregas/`, los títulos y selecciones deben responder al idioma activo del operador.
- [x] **Acciones Atómicas:**
  1. En `templates/backoffice/fulfillment/order_list.html`:
     - Desplegar el nombre del plan según el idioma: `{% if LANGUAGE_CODE == 'en' %}{{ order.plan.name_en|default:order.plan.name_es|default:"—" }}{% else %}{{ order.plan.name_es|default:order.plan.name_en|default:"—" }}{% endif %}`.
  2. En `fobandor/fulfillment/models.py`:
     - Aplicar `gettext_lazy` a `ORDER_TYPES` para que `get_order_type_display` sea traducido adecuadamente al inglés (ej: "Marketing Coaching" / "Acompañamiento de Marketing").

---

### Tarea 8.4: Script de Reconciliación de Órdenes Existentes en Producción
- [x] **Contexto:** Las órdenes existentes en producción (Order 1 para `jet@fobandor.com` y Order 2 para `fabiola.obando@cystec.global`) quedaron con `plan=None`.
- [x] **Acciones Atómicas:**
  1. Ejecutar comando de reconciliación en la BD de producción:
     - Relacionar Order 1 con Subscription 1 (*Plan 2 • Conversión*, `order_type="MARKETING"`).
     - Relacionar Order 2 con Subscription 2 (*Plan 1 • Impulso*, `order_type="MARKETING"`).
  2. Comprobar que en `/backoffice/entregas/` ambas filas muestren sus respectivos planes y servicios de forma inmediata.

---

### Tarea 8.5: Suite de Pruebas de Regresión y Despliegue en VPS
- [x] **Contexto:** Garantizar que los tests unitarios cubran la llegada desordenada de webhooks.
- [x] **Acciones Atómicas:**
  1. En `fobandor/billing/tests/test_webhooks.py`:
     - Escribir test donde `invoice.paid` se procesa **sin** que exista previamente la `CustomerSubscription` en base de datos, verificando que la `FulfillmentOrder` resultante tiene asignado el `plan` correcto extraído de `invoice.lines`.
  2. Ejecutar `pytest` (>=44 tests) y `flake8`.
  3. Commit, push y redespliegue en caliente en VPS.
  4. Criterio de Aceptación: El backoffice muestra siempre el plan y servicio contratado sin guiones `—` huérfanos.

---

## 12. Etapa 9: Notificaciones Transaccionales por Correo Electrónico tras Compra (Cliente y Equipo Interno)

> **Estado Actual:** FASE 4: EJECUTADA Y CERTIFICADA EN PRODUCCIÓN. Envío automatizado de correos transaccionales 100% dinámicos: (1) Correo al cliente con resumen de compra y enlace oficial directo al PDF de Stripe, y (2) Alerta interna a administradores y grupo `Content_Editors` con el asunto estandarizado en zona horaria `America/New_York` (Florida) y enlace directo a `/backoffice/entregas/`.  
> **Objetivo:** Implementar el envío automatizado de correos transaccionales 100% dinámicos (Cero Hardcoding) ante el evento de compra exitosa (`invoice.paid` en Stripe): (1) Correo al cliente con resumen de compra y enlace oficial directo al PDF de la factura generado por Stripe (`invoice_pdf`), y (2) Alerta interna a administradores y grupo `Content_Editors` con el asunto estandarizado en zona horaria `America/New_York` (Florida) y enlace directo a `/backoffice/entregas/`.

---

### Tarea 9.1: Servicio de Despacho de Correo al Cliente con Enlace Oficial al PDF de Stripe
- [x] **Contexto:** Al confirmarse el cobro en Stripe, el cliente debe recibir un correo transaccional branded con los datos dinámicos de su compra y el botón de acceso directo a la factura oficial en PDF emitida por Stripe (`invoice_pdf`), garantizando máxima deliverabilidad sin adjuntos pesados.
- [x] **Acciones Atómicas:**
  1. En `fobandor/billing/services.py`:
     - Crear función `send_customer_purchase_email(user, invoice_data, plan, order)`.
     - Variables 100% dinámicas inyectadas al contexto:
       * `client_name`: `user.get_full_name() or user.email`.
       * `plan_name`: `plan.name_es` (o `plan.name_en` según idioma preferido del usuario).
       * `service_name`: `order.get_order_type_display()`.
       * `amount_paid`: `(invoice_data.get("amount_paid", 0) / 100)` formateado en USD.
       * `currency`: `invoice_data.get("currency", "usd").upper()`.
       * `invoice_pdf_url`: Enlace directo oficial al PDF de Stripe (`invoice_data.get("invoice_pdf")`).
       * `hosted_invoice_url`: Enlace directo a la factura web de Stripe (`invoice_data.get("hosted_invoice_url")`).
       * `portal_url`: URL al portal del cliente (`/es/portal/dashboard/`).
       * `support_email`: Correo oficial de soporte y contacto `admin@fobandor.com`.
     - Manejo de excepciones defensivo (`try...except` con logger warning) para evitar que fallos temporales de red SMTP bloqueen el retorno 200 a Stripe.
  2. Crear plantillas corporativas bilingües:
     - `templates/billing/email/customer_purchase_invoice.html` y `.txt`.
     - Diseño responsive con la identidad FOBANDOR (Build · Ads · Studio), desglose de la compra, botón destacado "Descargar Factura Oficial en PDF", botón secundario "Ir a mi Portal de Cliente" y pie de contacto y soporte: `admin@fobandor.com`.
  3. Criterio de Aceptación: El cliente recibe un correo corporativo con todas las variables dinámicas de su compra, botón directo a su factura oficial emitida por Stripe y datos de contacto de soporte apuntando a `admin@fobandor.com`. Cero datos hardcodeados.

---

### Tarea 9.2: Servicio de Alerta Interna Dinámica para Administradores y Grupo `Content_Editors`
- [x] **Contexto:** El equipo operativo debe recibir una alerta inmediata ante cada nueva orden generada para gestionar el SLA. Los destinatarios y datos deben ser consultados dinámicamente de la base de datos y la fecha/hora debe expresarse en la zona horaria oficial de la empresa (`America/New_York` / Florida).
- [x] **Acciones Atómicas:**
  1. En `fobandor/billing/services.py`:
     - Crear función `send_internal_purchase_alert(user, invoice_data, plan, order)`.
     - Formateo de fecha y hora dinámicos en zona horaria `America/New_York`:
       * Usar `zoneinfo.ZoneInfo("America/New_York")`.
       * Convertir el timestamp del pago (`invoice_data.get("created")` o `order.paid_at`) a fecha/hora local de Florida (ej: `2026-11-18 19:05 EST`).
     - Asunto exacto requerido (100% dinámico):
       `Nueva compra de servicios - {fecha_hora_ny} - {cliente_email} - {servicio_y_plan}`
       *Ejemplo real evaluado en runtime:* `Nueva compra de servicios - 2026-11-18 19:05 EST - cliente@correo.com - Acompañamiento de Marketing (Plan 1 • Impulso)`
     - Destinatarios consultados dinámicamente de la base de datos (cero correos fijos en código):
       * `staff_emails = User.objects.filter(is_staff=True).values_list('email', flat=True)`
       * `editors_emails = User.objects.filter(groups__name="Content_Editors").values_list('email', flat=True)`
       * Destinatarios consolidados: `list(set(filter(None, list(staff_emails) + list(editors_emails))))`
     - Contexto dinámico para el cuerpo del mensaje:
       * Fecha/Hora en Florida, Cliente (email y nombre), Plan, Monto y moneda, Estado de orden inicial (Pendiente de Producción), Fecha límite SLA (calculada a 7 días), Operador asignado, Enlace directo: `https://fobandor.com/en/backoffice/entregas/`.
  2. Crear plantillas internas:
     - `templates/billing/email/internal_purchase_alert.html` y `.txt`.
     - Diseño limpio de panel operativo con tabla de variables y botón de acción directa al backoffice de entregas.
  3. Criterio de Aceptación: Todos los administradores y miembros de `Content_Editors` registrados en la base de datos reciben la notificación con el asunto dinámico en hora de Florida y enlace a la orden.

---

### Tarea 9.3: Integración en el Pipeline del Webhook `handle_invoice_paid`
- [x] **Contexto:** Disparar ambos correos transaccionales exactamente cuando la orden de entrega y el registro de facturación han sido consolidados con su plan y suscripción.
- [x] **Acciones Atómicas:**
  1. En `fobandor/billing/services.py` (`handle_invoice_paid`):
     - Disparar `send_customer_purchase_email` y `send_internal_purchase_alert` una vez creada/actualizada la `FulfillmentOrder` y `BillingInvoice`.
     - Persistir `invoice_pdf_url` y `hosted_invoice_url` en el modelo `BillingInvoice`.
  2. Criterio de Aceptación: Disparo automático y desacoplado de ambos correos tras cada cobro exitoso procesado por el webhook.

---

### Tarea 9.4: Pruebas Automatizadas (TDD) y Validación de Regresión
- [x] **Contexto:** Garantizar que los correos se generen con las variables dinámicas esperadas, en la zona horaria correcta y sin dependencias hardcodeadas.
- [x] **Acciones Atómicas:**
  1. En `fobandor/billing/tests/test_webhooks.py`:
     - Test unitario mockeando `django.core.mail.send_mail` / `EmailMultiAlternatives.send`.
     - Verificar que el correo al cliente se envía a su dirección real con el enlace al PDF de Stripe.
     - Verificar que el correo interno se despacha a la lista combinada (Staff + Content_Editors) con el asunto formateado en hora de `America/New_York`.
  2. Ejecutar suite `pytest` y `flake8`.
  3. Criterio de Aceptación: 100% de tests pasando (45/45 tests) y 0 errores de estilo.

---

### Tarea 9.5: Despliegue en VPS y Prueba en Vivo
- [x] **Contexto:** Despliegue en producción y verificación E2E.
- [x] **Acciones Atómicas:**
  1. Commit semántico y push a `origin/main`.
  2. Compilar imagen en el VPS y actualizar servicio `fobandor_web`.
  3. Ejecutar simulación de evento de prueba para certificar la llegada de ambos correos en las casillas reales.
  4. Criterio de Aceptación: Correos entregados con éxito en bandejas de entrada reales con datos 100% dinámicos.

---

## 18. Etapa 10: Resiliencia de Webhook Stripe (API Moderna StripeObject), Inyección SMTP Google en Docker Swarm y Reconciliación E2E

### Tarea 10.1: Compatibilidad de Stripe Line Items y Conversión Segura de StripeObject
- [x] **Contexto:** En la API moderna de Stripe, las líneas de factura almacenan el precio en `pricing.price_details.price` y los objetos retornados por el SDK son instancias de `StripeObject`, las cuales lanzan `AttributeError` al llamar a métodos de diccionario como `.get()`.
- [x] **Acciones Atómicas:**
  1. En `fobandor/billing/services.py`:
     - Refactorizar `_price_id_from_lines()` para soportar:
       * `item.get("pricing", {}).get("price_details", {}).get("price")` (Stripe moderno).
       * `item.get("price")` (como string ID o como dict con clave `"id"`).
       * Conversión previa con `getattr(obj, "to_dict", lambda: obj)()` si el elemento es un `StripeObject`.
     - En `_extract_price_id_from_invoice()` y `_extract_price_id_from_subscription()`:
       * Asegurar que cualquier retorno del SDK (`stripe.Invoice.retrieve` / `stripe.Subscription.retrieve`) sea convertido de inmediato a `dict` vía `.to_dict()`.
       * Envolver la invocación completa en bloques `try...except Exception` defensivos.
     - En `handle_invoice_paid()`:
       * Si `plan` no se pudo resolver desde las líneas pero el usuario ya cuenta con una `CustomerSubscription` activa vinculada a `subscription_id`, reutilizar el plan de dicha suscripción como fallback inmediato.
       * Agregar logging detallado con `logger.exception()` ante cualquier eventualidad no prevista para garantizar trazabilidad sin fallos silenciosos.
  2. Criterio de Aceptación: Extracción exitosa de `price_id` tanto para payloads antiguos de Stripe como para los emitidos por la API moderna.

---

### Tarea 10.2: Pruebas Unitarias Automatizadas (TDD)
- [x] **Contexto:** Certificar que la suite de tests cubra la estructura moderna de `pricing` y la compatibilidad con `StripeObject`.
- [x] **Acciones Atómicas:**
  1. En `fobandor/billing/tests/test_webhooks.py`:
     - Agregar test unitario con payload real de Stripe moderno (`{"pricing": {"price_details": {"price": "..."}}}`).
     - Validar que `handle_invoice_paid` extrae el plan, crea la `FulfillmentOrder`, la `BillingInvoice` y despacha ambos correos.
  2. Ejecutar `pytest` y `flake8` garantizando 0 errores.
  3. Criterio de Aceptación: Tests automatizados pasando con 100% de cobertura sobre el flujo de cobro.

---

### Tarea 10.3: Inyección de Variables SMTP de Google Workspace en Docker Swarm (VPS)
- [x] **Contexto:** El contenedor en producción carece de las variables `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD`, lo cual impide la conexión con el servidor SMTP de Google Workspace.
- [x] **Acciones Atómicas:**
  1. Actualizar la definición del servicio Swarm `fobandor_web` en el host:
     - `EMAIL_HOST=smtp.gmail.com`
     - `EMAIL_PORT=587`
     - `EMAIL_USE_TLS=true`
     - `EMAIL_HOST_USER=administrator@fobandor.com`
     - `EMAIL_HOST_PASSWORD=shsfmvaajpgxgfjk`
     - `DEFAULT_FROM_EMAIL=FOBANDOR <admin@fobandor.com>`
  2. Verificar con `docker service inspect fobandor_web` que las variables están activas en el contenedor.
  3. Probar la conectividad y despacho SMTP real desde la terminal Django hacia un destinatario de prueba.
  4. Criterio de Aceptación: Conexión SMTP autenticada con Google Workspace y confirmación de envío exitoso.

---

### Tarea 10.4: Despliegue en Producción y Reconciliación de la Orden Pendiente
- [x] **Contexto:** Desplegar el código corregido en el VPS, sanar la orden de compra de `servicioydemo@gmail.com` y emitir los correos pendientes.
- [x] **Acciones Atómicas:**
  1. Compilar y actualizar el contenedor `fobandor_web`.
  2. Reprocesar el webhook pendiente (`evt_1UdJu5Dd8zg4z4zajMVyhFbm`) o ejecutar comando de reconciliación para `servicioydemo@gmail.com`:
     - Creación de `BillingInvoice`.
     - Creación de `FulfillmentOrder` vinculada al *Plan 1 • Impulso*.
     - Disparo del correo con PDF Stripe a `servicioydemo@gmail.com`.
     - Disparo de la alerta al equipo interno (`admin@fobandor.com`, `Content_Editors`, etc.).
  3. Verificar en vivo en `https://fobandor.com/en/backoffice/entregas/`.
  4. Criterio de Aceptación: Orden visible en el Backoffice con su plan correspondiente y correos recibidos por cliente y equipo.

---

## 19. Etapa 11: Optimización UX de Notificaciones por Correo (Legibilidad Inline, Enlace Canónico al Portal y Simplificación Sobria)

### Tarea 11.1: Rediseño Minimalista de Alta Legibilidad de la Alerta Interna
- [x] **Contexto:** Gmail y clientes web descartan pseudo-clases CSS (`:first-child`, `:last-child`), provocando que el texto de la tabla apareciera en negro sobre fondo azul marino. Bajo el principio "menos es más", se requiere un diseño operativo limpio, con fondo claro y estilos 100% inline en cada celda.
- [x] **Acciones Atómicas:**
  1. En `templates/billing/email/internal_purchase_alert.html`:
     - Sustituir el fondo oscuro por un contenedor blanco nítido (`#ffffff`) sobre marco gris suave (`#f1f5f9`).
     - Aplicar estilos inline universales en cada elemento `<td>` (`style="color: #0f172a; padding: 10px 8px; font-weight: 600;"`) y etiquetas (`style="color: #64748b;"`).
     - Mantener el botón de acción principal en color naranja institucional (`#f97316`) con tipografía blanca nítida, dirigiendo a `https://fobandor.com/en/backoffice/entregas/`.
  2. Criterio de Aceptación: Legibilidad y contraste óptimos certificados en Gmail, Outlook y dispositivos móviles en modo claro y oscuro.

---

### Tarea 11.2: Corrección Canónica del Enlace al Portal de Cliente
- [x] **Contexto:** El botón "Acceder a mi Portal de Cliente" dirigía a `/es/portal/dashboard/`, respondiendo con HTTP 404 debido a que la ruta canónica en el proyecto es `/es/mi-cuenta/`.
- [x] **Acciones Atómicas:**
  1. En `fobandor/billing/services.py`:
     - Importar `reverse` desde `django.urls`.
     - Construir `portal_url` dinámicamente con `site_domain + reverse("portal:dashboard")`, resolviendo a `https://fobandor.com/es/mi-cuenta/`.
  2. Criterio de Aceptación: El botón del correo redirige sin errores al portal donde el cliente visualiza su suscripción y orden activa.

---

### Tarea 11.3: Simplificación Sobria del Correo del Cliente
- [x] **Contexto:** Eliminar textos redundantes en el pie de página de `customer_purchase_invoice.html` y `.txt`, adoptando una sola línea minimalista de contacto y soporte.
- [x] **Acciones Atómicas:**
  1. En `templates/billing/email/customer_purchase_invoice.html` y `.txt`:
     - Simplificar el footer a: `FOBANDOR — Build. Ads. Studio. · Soporte: admin@fobandor.com · www.fobandor.com`.
  2. Criterio de Aceptación: Correo ligero, limpio y libre de duplicaciones.

---

### Tarea 11.4: Batería de Pruebas Automatizadas y Despliegue
- [x] **Contexto:** Validación con `pytest` y despliegue al servidor de producción.
- [x] **Acciones Atómicas:**
  1. En `fobandor/billing/tests/test_webhooks.py`:
     - Agregar aserciones para certificar que el cuerpo del correo incluye `/mi-cuenta/` y excluye `/portal/dashboard/`.
  2. Ejecutar `pytest` (46/46 pasando) y `flake8` (0 errores).
  3. Desplegar a producción mediante commit semántico, push y actualización de `fobandor_web` en el host KVM VPS.
  4. Criterio de Aceptación: Servicio convergido en producción y verificación E2E.

---

## 20. Etapa 12: Modernización del Branding e Identidad Visual (Logotipo Oficial Dinámico en CMS y Navbar/Footer)

### Tarea 12.1: Extracción y Generación de Activo Estático Oficial
- [x] **Contexto:** El isotipo preliminar en el navbar era un badge CSS cuadrado simple con la letra "F". Se suministró la imagen oficial con alas estilizadas en degradé naranja (`#E8560F`) y azul (`#0E67C2`) más el wordmark tipográfico "FOBANDOR".
- [x] **Acciones Atómicas:**
  1. Extracción y procesamiento del activo con fondo transparente a `static/images/logo-fobandor.png`.
  2. Generación vectorial de referencia en `instructions/logo.svg`.
  3. Criterio de Aceptación: Activo de alta resolución con transparencia alfa y proporciones nativas preservadas.

---

### Tarea 12.2: Extensión de CompanyProfile (Singleton CMS) con Campo de Logotipo
- [x] **Contexto:** Habilitar al equipo administrativo la capacidad de cambiar o actualizar el logotipo de la empresa en cualquier momento desde el Backoffice sin requerir despliegues de código.
- [x] **Acciones Atómicas:**
  1. En `fobandor/cms/models.py`:
     - Añadir campo `logo = models.ImageField('Logotipo principal', upload_to='branding/', blank=True, null=True, help_text=...)` en `CompanyProfile`.
  2. Generar y aplicar migración `0004_companyprofile_logo`.
  3. En `fobandor/backoffice/views.py`:
     - Añadir `'logo'` a los campos editables de `CompanyProfileUpdateView`.
  4. En `templates/backoffice/cms/company_profile_form.html`:
     - Habilitar `enctype="multipart/form-data"` en el formulario.
     - Integrar previsualización en miniatura del logotipo actual sobre fondo oscuro y selector de archivo.
  5. Criterio de Aceptación: Logotipo editable en `/es/backoffice/empresa/` con persistencia en el volumen persistente de medios (`fobandor_media`).

---

### Tarea 12.3: Integración Frontend en Navbar, Footer y Backoffice con Fallback Robusto
- [x] **Contexto:** Desplegar el logotipo corporativo oficial tanto en la landing pública como en el portal administrativo, asegurando un fallback elegante al asset estático si no se ha subido uno personalizado en el CMS.
- [x] **Acciones Atómicas:**
  1. En `templates/partials/navbar.html`: Cargar `{% load static %}` y renderizar `company.logo.url` si existe, o `static 'images/logo-fobandor.png'`.
  2. En `templates/partials/footer.html`: Cargar `{% load static %}` y reemplazar el badge CSS por la imagen oficial del logotipo.
  3. En `templates/backoffice/base_backoffice.html`: Reemplazar el badge del sidebar por el logotipo institucional unificado.
  4. Criterio de Aceptación: Branding cohesivo y nítido en todas las vistas desktop y móviles.

---

### Tarea 12.4: Pruebas Automatizadas y Verificación de Regresiones
- [x] **Contexto:** Garantizar cobertura de pruebas y estabilidad del sistema.
- [x] **Acciones Atómicas:**
  1. En `fobandor/cms/tests/test_models.py`: Añadir test unitario para la presencia y persistencia del campo `logo`.
  2. Ejecutar suite de pruebas con `pytest` (47/47 pasando) y linter con `flake8` (0 infracciones).
  3. Criterio de Aceptación: Suite limpia sin regresiones.

---

## 21. Etapa 13: Contraste Inteligente de Logotipo en Modo Claro mediante Filtro Perimetral CSS (Alternativa 3)

### Tarea 13.1: Definición de la Regla CSS `.brand-logo-adaptive` y Recompilación de Tailwind
- [x] **Contexto:** El logotipo corporativo cuenta con isotipo en degradé naranja/azul y la palabra "FOBANDOR" en blanco puro (`#FFFFFF`). En Modo Claro (`html:not(.dark)`), el fondo blanco provoca la pérdida total de contraste del texto. Se requiere una solución que no obligue al usuario a mantener ni subir versiones duales (clara/oscura) en el CMS.
- [x] **Acciones Atómicas:**
  1. En `static/css/input.css`:
     - Incorporar en `@layer components` la clase semántica `.brand-logo-adaptive`:
       ```css
       @layer components {
         .brand-logo-adaptive {
           filter: drop-shadow(0 0 1.5px rgba(15, 23, 42, 0.95))
                   drop-shadow(0 1px 3px rgba(15, 23, 42, 0.4));
           transition: filter 0.2s ease-in-out;
         }
         .dark .brand-logo-adaptive {
           filter: none;
         }
       }
       ```
  2. Compilar Tailwind CSS: `npm run build:css` para actualizar `static/css/output.css`.
  3. Criterio de Aceptación: La regla procesa el canal alfa tanto en SVG como en PNG transparente, delineando con precisión milimétrica cada glifo de "FOBANDOR" en modo claro y apagándose en modo oscuro.

---

### Tarea 13.2: Aplicación de la Clase Adaptativa en Plantillas de Navbar y Footer
- [x] **Contexto:** Las áreas expuestas a fondos claros son el Navbar público (`bg-white/70`) y el Footer (`bg-gray-50`). La barra lateral del Backoffice es permanentemente oscura (`bg-fobandor-dark`), por lo que no requiere alteración.
- [x] **Acciones Atómicas:**
  1. En `templates/partials/navbar.html`:
     - Añadir `brand-logo-adaptive` a las etiquetas `<img>` del logo (tanto dinámica `company.logo.url` como fallback estático).
  2. En `templates/partials/footer.html`:
     - Añadir `brand-logo-adaptive` a las etiquetas `<img>` del logo en el bloque de marca.
  3. Criterio de Aceptación: El logotipo mantiene legibilidad absoluta sobre fondo claro sin alterar la apariencia limpia original en modo oscuro.

---

### Tarea 13.3: Batería de Pruebas Automatizadas y Calidad
- [x] **Contexto:** Asegurar estabilidad y ausencia de regresiones en la suite de pruebas.
- [x] **Acciones Atómicas:**
  1. Ejecutar suite de pruebas: `source .venv/bin/activate && pytest`.
  2. Ejecutar análisis estático: `flake8 config fobandor scripts`.
  3. Criterio de Aceptación: 48/48 pruebas pasando y 0 infracciones de estilo.

---

### Tarea 13.4: Despliegue en Producción y Verificación Visual con Alternador de Temas
- [x] **Contexto:** Desplegar en el cluster Hostinger VPS (`fobandor_web`) y verificar el comportamiento reactivo en vivo.
- [x] **Acciones Atómicas:**
  1. Generar commit semántico y push a `main`.
  2. Sincronizar en el VPS, reconstruir la imagen Docker multi-etapa y actualizar el servicio Swarm `fobandor_web`.
  3. Verificar en vivo en `https://fobandor.com/es/` alternando el switch de sol/luna (Modo Claro vs Modo Oscuro).
  4. Criterio de Aceptación: Transición suave, texto 100% legible en fondo claro y logo original nítido en fondo oscuro.
