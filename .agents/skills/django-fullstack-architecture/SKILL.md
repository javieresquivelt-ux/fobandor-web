---
name: django-fullstack-architecture
description: >-
  Guía de arquitectura para proyectos fullstack con Django 5.2 LTS, PostgreSQL,
  HTMX, Alpine.js y Tailwind CSS bajo el patrón Server-Driven y Clean Architecture.
  Usar cuando se inicializa un nuevo módulo, se diseña un modelo de datos, se
  implementa RBAC, se construye un backoffice, o se necesita aplicar los patrones
  arquitectónicos validados en el proyecto FOBANDOR.
---

# Django Fullstack Architecture — Lecciones Aprendidas FOBANDOR

## Stack Tecnológico Validado

| Capa | Tecnología | Versión Validada |
|:---|:---|:---|
| Framework | Django | 5.2 LTS |
| Runtime | Python | 3.14+ |
| Base de Datos | PostgreSQL | 16+ |
| Interactividad | HTMX | 2.0.4 |
| Micro-UI | Alpine.js | 3.14.9 |
| Estilos | Tailwind CSS | 3.4+ |
| Servidor WSGI | Gunicorn | 3 workers, timeout 120s |

---

## Principios Fundamentales (ADRs Validados)

### 1. Server-Driven sobre SPAs (ADR-001)

**Por qué:** DTL + HTMX + Alpine.js elimina la sobrecarga de React/Vue, mantiene SEO nativo, centraliza lógica en Python y simplifica la deuda técnica.

**Regla:**
- **DTL**: Todo el renderizado de páginas y datos.
- **HTMX**: Interactividad reactiva por fragmentos HTTP (filtros, búsqueda, actualizaciones parciales).
- **Alpine.js**: Exclusivamente micro-estado efímero en el cliente (dark mode, modales, menú móvil, selección de tarjetas, envío de formularios AJAX).

### 2. CustomUser desde la Migración 0001 (ADR-004 / ADR-011)

> [!CAUTION]
> **Nunca** ejecutar `migrate` antes de definir el CustomUser. Cambiar el modelo de usuario tras la primera migración es extremadamente destructivo.

```python
# fobandor/users/models.py
class User(AbstractUser):
    username = None  # Eliminamos username nativo
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()  # UserManager PERSONALIZADO es obligatorio
```

**Por qué ADR-011:** Definir `username = None` sobre `AbstractUser` sin un `UserManager` propio provoca `TypeError` en `createsuperuser` porque el manager base intenta `self.model(username=..., ...)`.

```python
class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email, password, **extra_fields)
```

### 3. Zero External CDN (ADR-003)

**Regla:** Prohibir CDNs externos para activos críticos.

```
static/
├── fonts/montserrat/     ← WOFF2 locales (@font-face)
├── js/vendor/
│   ├── htmx.min.js       ← HTMX local
│   └── alpine.min.js     ← Alpine.js local
└── css/
    ├── input.css         ← Directivas Tailwind
    └── output.css        ← CSS compilado y minificado
```

**Beneficios validados:** Inmunidad a firewalls corporativos, cumplimiento GDPR, multiplexado HTTP/2.

### 4. Patrón Singleton para Configuración Global (ADR-012)

```python
class CompanyProfile(models.Model):
    """Singleton: solo existe 1 registro. Usar CompanyProfile.load() en vistas."""

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    class Meta:
        verbose_name = 'Perfil de la Empresa'
```

**Context Processor Global:** Para inyectar `company` en TODAS las plantillas sin repetición por-vista:

```python
# fobandor/core/context_processors.py
def company(request):
    from fobandor.cms.models import CompanyProfile
    return {'company': CompanyProfile.load()}
```

Registrar en `settings/base.py`:
```python
TEMPLATES = [{'OPTIONS': {'context_processors': [
    # ...
    'fobandor.core.context_processors.company',
]}}]
```

---

## Arquitectura de Módulos (Clean Architecture)

```
fobandor/
├── core/        ← Home, contexto global, URLs estáticas
├── users/       ← CustomUser, RBAC, mixins de autenticación
├── cms/         ← CMS bilingüe (CompanyProfile singleton, ServiceCategory, Project)
├── billing/     ← Stripe Checkout, Webhooks, Planes, Facturas
├── fulfillment/ ← Motor SLA 7 días (FulfillmentOrder)
├── backoffice/  ← Panel staff desacoplado (es_staff guard)
└── portal/      ← Dashboard cliente (/mi-cuenta/)
```

**Patrón Services / Selectors:**
- `services.py`: Mutaciones de BD, llamadas a APIs externas (Stripe, envío de email).
- `selectors.py`: Consultas de lectura optimizadas con ORM.
- Las **vistas** son thin (sin lógica de negocio).

---

## RBAC con Grupos Django (ADR-013)

```python
# Tres roles funcionales validados:
GRUPOS_RBAC = {
    'Content_Editors': [...permisos_cms],      # CMS sin acceso financiero
    'Fulfillment_Operators': [...permisos_sla], # Gestión de entregas SLA
}
# Superadmin: is_superuser=True → acceso total
# Cliente: is_staff=False → solo /mi-cuenta/
```

**Guard Mixins:**
```python
class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

class EmailVerifiedRequiredMixin(UserPassesTestMixin):
    """Bloquea el checkout hasta que el email esté verificado."""
    def test_func(self):
        return getattr(self.request.user, 'is_email_verified', False)
```

---

## Autenticación Híbrida (Email + Google OAuth)

```python
# settings/base.py — para auto-vincular cuentas sociales a cuentas locales existentes
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True  # ← CRÍTICO para no duplicar usuarios
```

> [!WARNING]
> Sin `AUTO_CONNECT = True`, allauth rechaza el login OAuth de un usuario ya registrado
> con email/contraseña, enviándolo a una vista de signup sin estilos.

---

## Backoffice Desacoplado (ADR-014)

- Aplicación Django independiente (`fobandor.backoffice`).
- Guard único en `BackofficeMixin`: `is_staff=True`.
- Patrón CBV completo: `ListView`, `DetailView`, `UpdateView` con templates en `templates/backoffice/`.
- **Sin** dependencia de `django.contrib.admin` para las vistas operativas.

---

## Modelos Bilingües (ADR-012)

```python
class ServiceItem(models.Model):
    title_es = models.CharField(max_length=200)
    title_en = models.CharField(max_length=200)
    desc_es = models.TextField()
    desc_en = models.TextField()

    # En template:
    # {{ item.title_es }} / {{ item.title_en }}
    # o con i18n: usar context processor con LANGUAGE_CODE
```

---

## Checklist de Inicio de Proyecto

- [ ] Crear `fobandor/users/` con `CustomUser` y `UserManager` antes de cualquier `migrate`.
- [ ] Configurar `AUTH_USER_MODEL = 'users.User'` en `base.py`.
- [ ] Definir `USERNAME_FIELD = 'email'` y `REQUIRED_FIELDS = []`.
- [ ] Agregar `django-environ` y crear `.env.example` documentado.
- [ ] Iniciar PostgreSQL 16 en Docker Compose para paridad dev/prod.
- [ ] Crear grupos RBAC con management command (`create_rbac_groups`).
- [ ] Configurar `LANGUAGE_CODE`, `LANGUAGES` y `LocaleMiddleware` para i18n ES/EN.
- [ ] Generar favicons con Pillow desde el logo oficial.
- [ ] Correr `pytest` antes de cada commit.

## Referencias

- [ADRs completos del proyecto](../../memory.md)
- [spec.md — Especificación técnica](../../spec.md)
