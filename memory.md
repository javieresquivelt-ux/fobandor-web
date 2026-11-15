# MEMORY.MD: Memoria del Sistema, Decisiones Arquitectónicas y Registro Técnico

> **Proyecto:** FOBANDOR (`www.fobandor.com`)  
> **Cliente / Emprendedor:** Freddy Obando (Orlando, Florida, EE.UU.)  
> **Desarrollador Fullstack Líder:** Desarrollador en Chile (Ubuntu OS)  
> **Rol del Sistema:** Arquitecto de Software Senior y Experto en Ingeniería de Datos (Antigravity AI)  
> **Fecha de Inicio:** 14 de Noviembre de 2026  
> **Metodología:** HARNESS Framework (Iterativo e incremental por etapas)

---

## 1. Bitácora de Decisiones Arquitectónicas (ADRs)

### [ADR-001] Adopción de Enfoque Server-Driven y Rechazo Expreso de SPAs (React / Vue)
* **Estado:** Aprobado.
* **Contexto:** Se requiere un sitio comercial de alta velocidad, SEO optimizado y bajo costo de mantenimiento para servicios de IA, con mantenedores de CMS, usuarios y clientes. Se evaluó el uso de SPAs tradicionales (React/Vue) frente a un stack Server-Driven.
* **Decisión:** Desarrollar el 100% del frontend con **Django Template Language (DTL)** modularizado en `partials/`, **HTMX** para interactividad reactiva por fragmentos HTTP y **Alpine.js** exclusivamente para micro-interacciones de interfaz (estado efímero: Dark/Light mode, modales, menú móvil).
* **Justificación / Razonamiento:**
  * Elimina la sobrecarga de empaquetados JS masivos, problemas de hidratación y desincronización de estado cliente/servidor.
  * Reduce la deuda técnica y permite unificar todo el modelo de datos y validaciones en Python/Django.
  * SEO nativo superior sin necesidad de frameworks SSR complejos como Next.js o Nuxt.

---

### [ADR-002] Base de Datos Local y Paridad Dev / Prod mediante Docker
* **Estado:** Aprobado por el Desarrollador Líder.
* **Contexto:** El cliente Freddy Obando está cotizando proveedores de VPS (Hostinger u otro) para el despliegue final. Para ganar tiempo, el desarrollo arranca en la máquina local del desarrollador (Ubuntu). Se evaluó instalar PostgreSQL nativo vs. contenedor Docker.
* **Decisión:** Implementar la base de datos de desarrollo mediante un contenedor Docker con la imagen oficial `postgres:16-alpine`, volumen persistente `postgres_data` y orquestación con `docker-compose.yml`.
* **Justificación / Razonamiento:**
  * **Paridad Dev/Prod (12-Factor X):** Asegura que el motor de base de datos, extensiones y comportamiento sean idénticos en desarrollo y en el VPS final en Hostinger.
  * **Aislamiento del Host:** No contamina el sistema operativo Ubuntu del desarrollador con demonios o servicios PostgreSQL en segundo plano.
  * **Configuración Agnóstica:** Django se conecta mediante la variable `DATABASE_URL` gestionada por `django-environ`. Si el entorno cambia, basta con actualizar `.env`.

---

### [ADR-003] Estrategia "Zero External CDN" para Recursos Estáticos (Fuentes y Scripts)
* **Estado:** Aprobado por el Desarrollador Líder.
* **Contexto:** En ocasiones, clientes o usuarios navegan desde redes con bloqueos estrictos (firewalls corporativos, proxys institucionales, extensiones de privacidad) que impiden la carga de recursos alojados en CDNs públicos (Google Fonts, cdnjs, unpkg), provocando fallas visuales graves o interfaces rotas.
* **Decisión:** Prohibir CDNs externos para activos críticos. Toda la tipografía (**Montserrat** en formato WOFF2) y las librerías frontend (**HTMX 2.x** y **Alpine.js 3.x**) se descargarán, almacenarán y servirán localmente desde el directorio `static/` del proyecto.
* **Justificación / Razonamiento:**
  * **Inmunidad de Red:** El sitio web carga de forma consistente incluso en redes corporativas con bloqueo de CDNs o sin salida abierta a servicios de terceros.
  * **Cumplimiento de Privacidad (GDPR / AVS):** Elimina el rastreo involuntario o la transmisión de IPs de usuarios hacia Google Fonts.
  * **Rendimiento:** Servir fuentes y scripts desde el mismo origen aprovecha el multiplexado HTTP/2 y reduce las negociaciones TLS externas.

---

### [ADR-004] Definición Temprana de CustomUser desde la Migración Inicial
* **Estado:** Aprobado.
* **Contexto:** En Django, cambiar el modelo de usuario después de haber generado la primera migración de base de datos es extremadamente complejo y propenso a errores en producción.
* **Decisión:** Implementar la aplicación `fobandor.users` con el modelo `User(AbstractUser)` antes de ejecutar cualquier comando `migrate`:
  * `USERNAME_FIELD = 'email'` (el correo es el identificador principal de login).
  * Soporte nativo para RBAC de staff (Superadmin, Editor de Contenido, Operador de Entregas).
  * Campos para clientes: verificación previa obligatoria (`is_email_verified`), campos de facturación AVS (País, Estado, Ciudad, ZIP, Línea 1 y 2), teléfono E.164, y vinculación con `stripe_customer_id`.
* **Justificación / Razonamiento:** Garantiza un esquema de datos limpio y escalable para autenticación B2B y B2C sin deuda técnica futura.

---

### [ADR-005] Modelo de Negocio Core: Prepago + SLA 7 Días + Renovación Automática
* **Estado:** Aprobado.
* **Contexto:** El cliente Freddy Obando ofrece paquetes mensuales de contenido/publicidad para redes sociales y servicios digitales con compromiso de entrega.
* **Decisión:** Implementar el flujo mediante Stripe Checkout (3 planes mensuales con cupones de descuento `allow_promotion_codes=True`), Stripe Customer Portal y Webhooks firmados:
  1. El cliente paga por anticipado.
  2. Los webhooks `checkout.session.completed` e `invoice.paid` generan automáticamente una `FulfillmentOrder` en PostgreSQL con estado `PENDIENTE_PRODUCCION` y fecha límite `due_date = paid_at + 7 días`.
  3. El equipo de FOBANDOR gestiona la cola en el Backoffice, sube el entregable digital dentro del plazo de 7 días y marca la orden como `ENTREGADA`.
  4. Cada cobro mensual exitoso en Stripe renueva automáticamente el ciclo de entrega de 7 días.

---

### [ADR-006] Seguridad PCI-DSS y Gate de Verificación Previa por Correo
* **Estado:** Aprobado.
* **Contexto:** Cumplimiento legal y mitigación de fraude en transacciones de clientes estadounidenses y latinoamericanos.
* **Decisión:**
  * Queda terminantemente prohibido almacenar números de tarjeta, CVVs o fechas de expiración en la base de datos local. Todas las transacciones son delegadas a Stripe Checkout y Stripe Customer Portal.
  * Se implementa un **Gate de Seguridad**: ningún cliente puede acceder a una sesión de Stripe Checkout si su correo no ha sido verificado activamente (`is_email_verified = True`).
  * Se registra la aceptación de Términos de Servicio y Políticas de Privacidad con marca de tiempo inmutable (`terms_accepted_at`).

---

### [ADR-007] Arquitectura de Autenticación Unificada por Sesiones y Matriz RBAC
* **Estado:** Aprobado.
* **Contexto:** Se requiere autenticar y gobernar el acceso a tres áreas diferenciadas: Portal de Cliente (`/mi-cuenta/`), Backoffice (`/backoffice/`) y soporte técnico. Se analizó el uso de tokens JWT frente a sesiones de Django.
* **Decisión:** Utilizar el sistema de **Session-Based Authentication nativo de Django** con cookies criptográficas `HttpOnly` y `SameSite=Lax`, identificando al usuario por su `email`:
  * Portal de Cliente (`/mi-cuenta/`): Protegido con `LoginRequiredMixin` para usuarios no-staff (`is_staff = False`).
  * Backoffice (`/backoffice/`): Protegido con `StaffRequiredMixin` y permisos granulares por grupos Django:
    * *Superadmin:* Acceso global irrestricto.
    * *Editor de Contenido:* Acceso exclusivo al CMS (4 líneas de servicio, proyectos, nosotros, RRSS).
    * *Operador Studio:* Acceso exclusivo a la cola de `FulfillmentOrder` (SLA 7 días) y subida de entregables.
* **Justificación / Razonamiento:** En una arquitectura Server-Driven con DTL + HTMX, las sesiones HttpOnly eliminan el riesgo de robo de tokens por XSS en `localStorage`, soportan revocación inmediata desde el servidor y cuentan con protección CSRF nativa en cada petición HTMX.

---

### [ADR-008] Autenticación Social con Cuentas Gmail (Google OAuth 2.0) y Reserva de Google Workspace
* **Estado:** Aprobado por el Desarrollador Líder.
* **Contexto:** Se evaluó la conveniencia de integrar autenticación mediante Google para agilizar el registro de clientes y mejorar la seguridad del staff.
* **Decisión:**
  1. **Aprobado para Ejecución (Etapa 3): Social Login con Cuentas Gmail (Google OAuth 2.0 / `django-allauth`):**
     * Permite a los clientes registrarse o autenticarse en 1 clic.
     * **Verificación Instantánea:** Los usuarios que ingresan con Gmail quedan automáticamente marcados con `is_email_verified = True`, eliminando la fricción y espera del correo de activación antes de Stripe Checkout.
     * **Onboarding AVS:** Se requerirá un paso breve posterior para capturar la dirección de facturación completa y teléfono E.164 exigidos por Stripe para procesar cobros en EE.UU.
  2. **Documentado pero Fuera del Plan de Ejecución: Google Workspace SSO:**
     * Se deja diseñada la capacidad de restringir el acceso del staff en `/backoffice/` a cuentas corporativas con dominio `@fobandor.com` para una fase futura de expansión, sin incluirla en el cronograma actual.
* **Justificación / Razonamiento:** Maximiza la tasa de conversión y registro de clientes, reduce los tickets de soporte por emails de activación perdidos en spam, y mantiene el alcance del proyecto enfocado y sin desviaciones.

---

### [ADR-009] Mecanismo de Detección de Órdenes `VENCIDA` (SLA 7 Días)
* **Estado:** Propuesto para Etapa 3.
* **Contexto:** El estado `VENCIDA` de `FulfillmentOrder` requiere una evaluación periódica de `due_date` frente a la fecha actual. No puede depender solo de una acción del usuario.
* **Decisión (recomendada):** Implementar un `management command` (ej. `python manage.py mark_overdue_orders`) que marque `VENCIDA` las órdenes con `due_date < now()` y `status = PENDIENTE_PRODUCCION`, y programarlo vía **cron** en el VPS.
* **Justificación / Razonamiento:** Mantiene coherencia 12-Factor sin introducir Celery/Redis en la infraestructura; el cron del VPS es suficiente para una evaluación diaria de bajo costo.

---

### [ADR-010] Versionado de Runtime y Framework (Corrección v2)
* **Estado:** Aprobado.
* **Contexto:** El host de desarrollo dispone únicamente de **Python 3.14.4**, mientras el plan original fijaba Django `>=5.1,<5.2`, que no soporta Python 3.14.
* **Decisión:** Adoptar **Django 5.2 LTS** (`Django>=5.2,<5.3`), con soporte oficial de Python 3.14. Instalar **Docker Engine + Compose** en el host para mantener PostgreSQL 16 activo desde la Etapa 1 (paridad dev/prod intacta, ADR-002).
* **Justificación / Razonamiento:** Evita instalar un runtime Python 3.12 adicional (sin pyenv/deadsnakes en el host) y aprovecha la rama LTS con mayor soporte de seguridad y estabilidad.

---

### [ADR-011] Corrección del Modelo `CustomUser` con `UserManager` Personalizado
* **Estado:** Aprobado.
* **Contexto:** Definir `username = None` sobre `AbstractUser` deja activo el `UserManager` por defecto, cuyo `_create_user` exige el argumento `username` y construye `self.model(username=..., ...)`, provocando `TypeError` en `createsuperuser` y `create_user`.
* **Decisión:** Proveer un `UserManager` personalizado (`use_in_migrations = True`) con `_create_user`, `create_user` y `create_superuser` basados exclusivamente en `email`, y asignarlo como `objects = UserManager()` en el modelo.
* **Justificación / Razonamiento:** Es requisito técnico obligatorio para un `USERNAME_FIELD = 'email'` sin campo `username`; sin él, la gestión de usuarios falla en tiempo de ejecución.

---

## 2. Diagnóstico del Entorno de Ejecución (Ubuntu Local)

* **Sistema Operativo:** Linux Ubuntu 26.04.1 LTS "Resolute" (x86_64).
* **Python Runtime:** Python 3.14.4 disponible (`python3`).
* **Node.js y npm:** Node v22.22.1 y npm 9.2.0 disponibles (se utilizarán para compilar Tailwind CSS localmente).
* **Docker:** Instalado en Tarea 1.0 — Docker Engine 29.9.3 y Docker Compose plugin v5.7.1 (repo oficial `download.docker.com` con `resolute`). Servicio `docker` activo y habilitado; contenedor `fobandor_postgres` (`postgres:16-alpine`) operativo y saludable.
* **Control de Versiones:** Git 2.53.0 disponible.

---

## 3. Estado de la Gobernanza HARNESS

| Fase HARNESS | Estado | Acciones Realizadas / Próximas |
| :--- | :---: | :--- |
| **1. ANALIZAR** | **COMPLETADA** | Análisis del prompt oficial, imágenes de marca, catálogo de 4 líneas y redacción de `agent.md`, `spec.md` e `informe_entendimiento.md`. |
| **2. PLANIFICAR** | **COMPLETADA** | Desglose atómico de tareas para la Etapa 1 en `task.md` con arquitectura limpia (*Thin Models/Views*, `services.py`, `selectors.py`), enriquecido con especificaciones exactas de modelos, dependencias y comandos para DeepSeek V4 Pro en OpenCode. |
| **3. APROBAR** | **APROBADO** | Dictamen APROBADO emitido por Antigravity-IDE tras revisar los 6 puntos de corrección (ADRs 009-011, Django 5.2 LTS, `UserManager`, Docker, i18n, fallback BD). |
| **4. EJECUTAR** | **COMPLETADA Y VALIDADA** | Etapa 1 ejecutada por OpenCode y validada técnicamente por Antigravity-IDE. Criterios de aceptación 100% cumplidos (Postgres 16 en Docker, CustomUser con test suite pytest pasando al 100%, Zero-CDN, DTL/Tailwind/Alpine/i18n). |
| **5. REGISTRAR** | **COMPLETADA (Etapa 1)** | Bitácora `memory.md` y `task.md` sincronizadas con los hallazgos y validación de la Etapa 1. |
| **6. APRENDER** | **COMPLETADA (Etapa 1)** | Consolidación del `README.md` exhaustivo y sincronización exitosa del repositorio remoto en GitHub (`javieresquivelt-ux/fobandor-web`). |

---

## 4. Hallazgos y Decisiones de la Ejecución de la Etapa 1

### Versiones instaladas (verificadas en tiempo de ejecución)
* **Django 5.2.19** — confirma el ADR-010 (compatible con Python 3.14.4; Django 5.1 habría fallado).
* **psycopg 3.3.9**, **Pillow 13.0.0**, **pytest 9.2.0**, **pytest-django 4.14.0**, **flake8 7.5.0**, **polib 1.2.0**.
* **Docker Engine 29.9.3**, **Docker Compose v5.7.1**, contenedor `postgres:16-alpine` saludable.
* **HTMX 2.0.4** y **Alpine.js 3.14.9** servidos localmente desde `static/js/vendor/`.
* **Montserrat** en formato variable WOFF2 (subconjuntos `latin` y `latin-ext`), con `@font-face` declarando `font-weight: 400 700`.

### Decisiones y desviaciones respecto al plan original
1. **Fonts como fuente variable:** En lugar de 4 archivos estáticos (400/500/600/700), Montserrat v31 se sirve como fuente variable (un único archivo por subconjunto) con rango `font-weight: 400 700`. Mantiene la estrategia Zero External CDN y reduce el peso total.
2. **Scripts auxiliares añadidos (no previstos en el árbol objetivo):** `scripts/generate_favicons.py` (favicons desde `logo-fobandor.jpg`) y `scripts/build_translations.py` (catálogo EN → `.po`/`.mo` vía `polib`).
3. **Traducción EN funcional:** Se compiló un catálogo EN (31 cadenas) con `polib`, ya que el host no dispone de `msgfmt` (solo GNU gettext-runtime). `LOCALE_PATHS = [BASE_DIR / 'locale']` añadido a `config/settings/base.py`.
4. **`docker` en la sesión de OpenCode:** Tras `usermod -aG docker`, la sesión persistente no adquiere el grupo hasta re-login. Se usó `sg docker -c "..."` para los comandos de Docker. No afecta al runtime de producción.
5. **`.flake8` añadido:** excluye `migrations/` y `scripts/build_translations.py` (E501) para mantener `flake8` limpio sobre código propio.
6. **Anclas de navegación:** Se añadieron secciones placeholder (`#proyectos`, `#precios`, `#nosotros`, `#contacto`) para evitar enlaces rotos del navbar, aunque la Etapa 1 solo exige Hero + 4 líneas.

### Credenciales y datos de entorno generados (LOCAL / desarrollo)
* **Superusuario:** `admin@fobandor.com` / `ChangeMe123!` (creado para validar `UserManager`; **cambiar en producción**).
* **BD local:** `fobandor_user` / `fobandor_secret` / `fobandor_db` (solo desarrollo, definidos en `docker-compose.yml` y `.env`).
* **SECRET_KEY:** valor inseguro de desarrollo en `.env` (`django-insecure-...`), documentado con aviso de cambio en producción.

### Verificación de aceptación (Tarea 1.9)
* `python manage.py check` → 0 issues. `makemigrations --check --dry-run` → sin cambios.
* `createsuperuser --noinput` → exitoso (valida el `UserManager` de ADR-011).
* `/` → 302 → `/es/` (por `i18n_patterns`); `/es/` y `/en/` → HTTP 200.
* Traducción ES/EN verificada en hero, nav y CTA ("Ideas, código..." ↔ "Ideas, code...").
* Zero External CDN confirmado: todos los assets servidos desde `/static/`; únicamente existen enlaces salientes a RRSS oficiales y `xmlns` SVG.
* `flake8` (config, fobandor, scripts) → limpio.

### Auditoría y Enriquecimiento Técnico de Antigravity-IDE (FASE 4 → 5)
1. **Configuración de Pytest (`pytest.ini`):** Se creó `pytest.ini` apuntando a `DJANGO_SETTINGS_MODULE = config.settings.local` y `--reuse-db`.
2. **Suite de Pruebas Automatizadas (`fobandor/users/tests/test_models.py`):** Se crearon 3 pruebas unitarias de regresión para validar la creación de usuario estándar por email, creación de superusuario sin username y el lanzamiento de `ValueError` ante email vacío. Resultado: 3/3 tests pasando.
3. **Soporte de Testing en Entorno Local:** Se incluyó `"testserver"` en `ALLOWED_HOSTS` dentro de `config/settings/local.py` para compatibilidad transparente con `django.test.Client` y `pytest-django`.
4. **Sincronización de Checkboxes en `task.md`:** Se actualizaron a `[x]` todas las casillas de las tareas 1.0 a 1.9, certificando el pase formal a la Etapa 2.

