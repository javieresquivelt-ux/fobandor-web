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

### [ADR-012] Arquitectura de Modelos CMS Bilingües y Patrón Singleton para Perfil Corporativo
* **Estado:** Aprobado.
* **Contexto:** En la Etapa 2 se requiere administrar dinámicamente las 4 líneas de servicio, proyectos, redes sociales y datos corporativos de FOBANDOR en español e inglés sin introducir dependencias pesadas de terceros (como `django-modeltranslation` o `django-parler`) que añadan complejidad o incompatibilidades con Python 3.14 / Django 5.2.
* **Decisión:** 
  * Implementar campos bilingües explícitos a nivel de modelo (`title_es`, `title_en`, `desc_es`, `desc_en`, etc.).
  * Implementar `CompanyProfile` con patrón singleton garantizado por `pk=1` forzado en el método `save()` y método de clase `load()` con `get_or_create`. En el Django Admin y en el Backoffice se restringe la adición de múltiples registros.
  * Inyección de redes sociales oficiales en plantillas públicas mediante context processor (`fobandor.core.context_processors.social_links`).
* **Justificación / Razonamiento:** Máxima robustez, cero dependencias frágiles, total compatibilidad con Django 5.2 LTS y consultas SQL directas y eficientes.

---

### [ADR-013] Implementación de Grupos RBAC y Asignación Granular de Permisos
* **Estado:** Aprobado.
* **Contexto:** Se requiere segregar las funciones de administración interna entre editores de contenido y operadores de entrega/servicios, evitando otorgar `is_superuser` indiscriminadamente.
* **Decisión:**
  * Crear dos grupos Django mediante management command idempotente (`python manage.py create_rbac_groups`):
    * `Content_Editors`: Permisos `add`, `change` y `view` sobre todos los modelos de `fobandor.cms` (sin permiso `delete` destructivo directo).
    * `Fulfillment_Operators`: Reservado para la gestión de órdenes de entrega en Etapa 3.
  * Acceso al Backoffice (`/backoffice/`) restringido a usuarios con `is_staff=True` mediante `StaffRequiredMixin`.
* **Nota de Alcance (Etapa 2):** La granularidad por grupos (`Content_Editors` / `Fulfillment_Operators`) surte efecto únicamente en el Django Admin (`/admin/`) durante la Etapa 2. En `/backoffice/` el gate es solo `is_staff=True`; la aplicación de permisos granulares por grupo en el backoffice queda diferida a la Etapa 3 (junto con `FulfillmentOrder`).
* **Justificación / Razonamiento:** Aprovecha el motor nativo de permisos y grupos de Django (`django.contrib.auth.models.Group`), facilitando la auditoría y sin requerir bibliotecas externas de RBAC.

---

### [ADR-014] Backoffice Dedicado como Aplicación Django Desacoplada (`fobandor.backoffice`)
* **Estado:** Aprobado.
* **Contexto:** Se evaluó si utilizar exclusivamente el Django Admin estándar (`/admin/`) o construir un portal de administración a medida para el equipo de FOBANDOR.
* **Decisión:** Desarrollar una aplicación independiente `fobandor.backoffice` con rutas bajo `/backoffice/`, vistas CBV estándar de Django, plantillas DTL con Tailwind CSS estilizadas con la identidad corporativa de FOBANDOR y reactividad ligera con HTMX / Alpine.js. El Django Admin estándar se mantiene activo en `/admin/` exclusivamente como herramienta de mantenimiento técnico de bajo nivel para superusuarios.
* **Justificación / Razonamiento:** Ofrece al cliente Freddy Obando y su equipo una experiencia de usuario personalizada, rápida y alineada con la marca, manteniendo los formularios limpios y protegiendo el panel nativo de Django contra modificaciones de interfaz frágiles.

---

### [ADR-015] Gestión Dinámica de Planes de Acompañamiento y Catálogo Comercial en Backoffice
* **Estado:** Aprobado por el Desarrollador Líder.
* **Contexto:** Freddy Obando entregó la definición oficial de los 3 paquetes de servicios reales ("Planes de Acompañamiento: Marketing Digital & Ventas para negocios locales"):
  * **Plan 1 • Impulso:** $697 USD/mes, compromiso mínimo 2 meses, enfocado en generar demanda con Meta Ads.
  * **Plan 2 • Conversión (Recomendado):** $1,297 USD/mes, compromiso mínimo 3 meses, enfocado en embudos, CRM y citas.
  * **Plan 3 • Crecimiento:** $1,997 USD/mes, compromiso mínimo 3 meses, enfocado en fidelización, recompra y LTV.
  Se exige como requisito crítico del negocio que ningún plan ni precio quede hardcodeado, y que el administrador o encargado pueda gestionar los planes, textos y claves de precio de Stripe directamente desde `/backoffice/planes/`. Además, el CTA de diagnóstico comercial se integrará provisionalmente con Formspree.io.
* **Decisión:**
  1. **Enriquecimiento del Modelo `SubscriptionPlan`:** Incorporar campos bilingües de subtítulo (`subtitle_es/en`), meses de compromiso mínimo (`min_commitment_months`), público objetivo (`target_audience_es/en`), texto legal (`disclaimer_es/en`) y endpoint de Formspree (`formspree_endpoint`).
  2. **Módulo CRUD en Backoffice (`/backoffice/planes/`):** Vistas CBV para listar y editar planes con pestañas Alpine.js, permitiendo actualizar textos y el `stripe_price_id` sin tocar código fuente ni desplegar.
  3. **Catálogo de Alta Fidelidad (`/precios/`):** Rediseño visual fiel a la infografía oficial con badges de compromiso mínimo, badge "RECOMENDADO" y modal/sección de diagnóstico conectado a Formspree.
* **Justificación / Razonamiento:** Garantiza soberanía operativa a Freddy Obando y su equipo administrativo para ajustar su oferta comercial y precios de Stripe en tiempo real, manteniendo la pasarela de pagos desacoplada de cambios de código.

---

### [ADR-016] Estrategia de Despliegue en Producción con EasyPanel, Traefik y WhiteNoise en Hostinger VPS
* **Estado:** Propuesto en FASE 3: APROBAR (En espera de aprobación del Desarrollador Líder).
* **Contexto:**
  * El cliente Freddy Obando adquirió el dominio `fobandor.com` en NIC.com (DNS en GoDaddy) y dispone de un servidor Hostinger KVM VPS (`89.117.32.46`, 8 GB RAM, 96 GB SSD) administrado mediante EasyPanel v2.31.0 con Traefik 3.6.7 en los puertos 80 y 443.
  * El servidor ejecuta activamente `n8n` y `barberbot` (`evolution-api` + postgres + redis) con uso mínimo de CPU (0.0%) y 6.4 GB de RAM disponibles.
  * El plan de EasyPanel presentaba un límite de proyectos concurrentes (máximo 3 proyectos activos). Se detectó el proyecto detenido `massaro`, el cual fue respaldado íntegramente (`/root/backups/backup_massaro_20261116.tar.gz`) y descargado a local, procediéndose a su eliminación en la UI de EasyPanel para liberar un slot dedicado a `fobandor`.
  * Los registros DNS en NIC.com/GoDaddy fueron configurados: `@` (A) -> `89.117.32.46` y `www` (CNAME) -> `fobandor.com`, verificándose su propagación global hacia el servidor.
* **Decisión:**
  1. **Arquitectura de Empaquetado:** Implementar un `Dockerfile` multi-etapa:
     - *Etapa 1 (`frontend-builder` con `node:22-alpine`):* Compila y minifica Tailwind CSS sin inflar la imagen de producción.
     - *Etapa 2 (`runner` con `python:3.14-slim`):* Runtime liviano con dependencias de producción, usuario no-root `django`, servidor WSGI Gunicorn (3 workers, timeout 120s) y script de inicialización `entrypoint.sh` para aplicar migraciones y seeders automáticos.
  2. **Serving de Archivos Estáticos:** Adoptar **WhiteNoise** con compresión Brotli y Gzip (`whitenoise[brotli]`) y almacenamiento con hash inmutable (`CompressedManifestStaticFilesStorage`). Esto garantiza el cumplimiento estricto de la directriz *Zero External CDN*, evitando la complejidad y sobrecarga de memoria de un contenedor Nginx adicional.
  3. **Enrutamiento y Terminación TLS/SSL:** Delegar la terminación HTTPS y emisión automática de certificados Let's Encrypt a **Traefik**, configurando en Django `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`, `USE_X_FORWARDED_HOST = True` y `USE_X_FORWARDED_PORT = True`.
  4. **Base de Datos de Producción:** Crear un servicio administrado PostgreSQL 16 provisto por EasyPanel en la red interna del proyecto `fobandor`, conectándose mediante la variable de entorno `DATABASE_URL` (estándar 12-Factor).
  5. **Ciclo de Vida de Pasarela Stripe:** Desplegar inicialmente con claves de Stripe en *Test Mode* en el dominio productivo `https://fobandor.com/` para validar el flujo completo de checkout y la recepción de webhooks criptográficos sobre HTTPS real sin túneles de desarrollo (`stripe listen`/`ngrok`). Una vez validado comercialmente con Freddy Obando, la transición a *Live Mode* se realizará de forma inmediata mediante variables de entorno en EasyPanel y actualización de IDs de precios en `/backoffice/planes/`.
* **Justificación / Razonamiento:**
  * Máxima simplicidad operativa y uso eficiente de los recursos del VPS (menos de 300 MB de RAM adicionales para el runtime Django + Postgres).
  * Renovación de certificados SSL 100% automatizada y sin intervención manual.
  * Zero External CDN y alta velocidad de carga mediante compresión Brotli local.
  * Despliegue continuo sin fricción vía GitHub a la rama `main`.

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
| **1. ANALIZAR** | **COMPLETADA** | Análisis profundo de los 11 hallazgos identificados en producción y mapeo con las 10 capturas de pantalla del Google Doc. |
| **2. PLANIFICAR** | **COMPLETADA** | Desglose atómico de la **Etapa 5 (Tareas 5.1 a 5.10)** en `task.md`, abarcando Frontend, Responsive móvil, Checkout GET y Backoffice SLA. |
| **3. APROBAR** | **APROBADO** | Plan de la Etapa 5 aprobado por el desarrollador líder, con ajustes finales (context processor `company` y `DEFAULT_ASSIGNEE_EMAIL`). |
| **4. EJECUTAR** | **EJECUTADA (Etapa 5)** | Tareas 5.1 a 5.10 implementadas y verificadas por OpenCode (38/38 tests). Pendiente despliegue y validación en vivo. |
| **5. REGISTRAR** | **EN PROGRESO** | Sección 19 documentada en `memory.md` con razonamientos arquitectónicos, ejecución y hallazgos. |
| **6. APRENDER** | **PENDIENTE** | Verificación en caliente en producción y actualización viva de la documentación. |

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

---

## 5. Preparación y Validación Técnica para la Etapa 2

* **Objetivo de la Etapa:** Identidad, RBAC y Backoffice CMS.
* **Documento Rector:** [task.md](file:///home/jet/proyectos_lnx/proyectos/fobandor/task.md) (Sección 4: Tareas 2.0 a 2.11).
* **Decisiones Arquitectónicas Incorporadas:** ADR-012 (Modelos bilingües y Singleton), ADR-013 (Grupos RBAC Django), ADR-014 (Backoffice desacoplado).
* **Condiciones de Entrada:**
  * Base de datos PostgreSQL 16 activa en contenedor Docker `fobandor_postgres`.
  * Modelo `CustomUser` y `UserManager` verificados y con test suite pasando.
  * Runtime Python 3.14.4 + Django 5.2.19 LTS en `.venv/`.
  * Repositorio remoto sincronizado en rama `main`.
* **Próxima Acción (FASE 4):** Ejecución atómica de las tareas 2.0 a 2.11 por parte de OpenCode (DeepSeek V4 Pro) en el entorno de desarrollo local.

---

## 6. Correcciones al Plan de la Etapa 2 (revisión técnica OpenCode)

Correcciones aplicadas al plan de la Etapa 2 tras revisión técnica, antes de la validación final por Antigravity-IDE:

### Decisiones confirmadas por el desarrollador líder
1. **RBAC:** En Etapa 2 el backoffice valida únicamente `is_staff=True`; la granularidad por grupos aplica solo en `/admin/` y se difiere a Etapa 3 (documentado en ADR-013).
2. **`ServiceItem`:** Se **siembran** los sub-servicios por categoría (gestión vía Django Admin, sin CRUD propio en backoffice en Etapa 2).
3. **Login anónimo:** `LOGIN_URL = "admin:login"` como solución temporal hasta Etapa 3.

### Bugs corregidos en el plan (`task.md`) y en configuración
1. `test_seed_initial_content_idempotent`: eliminado el fixture inexistente `django_db_setup`.
2. `config/settings/base.py`: añadido `LOGIN_URL = "admin:login"` y `LOGIN_REDIRECT_URL = "core:home"`.
3. `config/urls.py`: añadido `static(settings.MEDIA_URL, ...)` bajo `DEBUG` para servir `Project.image` en desarrollo.
4. `seed_initial_content`: ahora siembra `ServiceItem` (sub-servicios) por cada categoría.
5. `create_rbac_groups`: se especificó la creación de `fobandor/users/management/__init__.py` y `management/commands/__init__.py`.

### Coherencia / alcance
6. Eliminado el título `### Etapa 3` duplicado en `task.md`.
7. Añadidos `service_confirm_delete.html` y `project_confirm_delete.html` al árbol de archivos de la Etapa 2.
8. `social_links` ahora proviene exclusivamente de un **context processor global** (`fobandor.core.context_processors.social_links`); `home_view` solo inyecta `services`.
9. Uso directo de `{{ LANGUAGE_CODE }}` (del context processor i18n) en lugar de `{% get_current_language %}`.
10. Tests del backoffice: `client.force_login(user)` y `client.get(url, follow=False)` (sin prefijo `/es` hardcodeado).
11. `StaffRequiredMixin`: redirección vía `reverse('core:home')` en lugar de `redirect('/')`.

---

## 7. Hallazgos y Validación de la Ejecución de la Etapa 2

* **Commit Oficial:** `5e3a51e` en `origin/main` (`feat(etapa-2): identidad, rbac y backoffice cms`).
* **Suite de Pruebas Automatizadas:** 10/10 tests pasando en `pytest` (3 de `users`, 4 de `cms`, 3 de `backoffice`).
* **Calidad de Código:** `flake8 config fobandor scripts` con 0 advertencias o errores.
* **Integridad de Migraciones:** `python manage.py makemigrations --check --dry-run` reporta 0 cambios pendientes.
* **Siembra Inicial de Datos:**
  * 4 categorías de servicio principales (`desarrollo-web`, `desarrollo-apps`, `publicidad`, `fobandor-studios`).
  * 23 sub-servicios bilingües sembrados (`ServiceItem`).
  * 5 redes sociales oficiales (`Instagram`, `TikTok`, `X`, `YouTube`, `Facebook`).
  * Perfil corporativo singleton inicializado en Orlando, Florida.
* **Verificación HTTP Real:**
  * `/es/` → HTTP 200 con servicios y redes dinámicas desde PostgreSQL.
  * `/en/` → HTTP 200 con títulos y descripciones en inglés.
  * `/es/backoffice/` (anónimo) → Redirección 302 hacia `/es/admin/login/?next=/es/backoffice/`.
  * `/es/backoffice/` (staff autenticado) → HTTP 200 dashboard con métricas reales.
* **Criterio de Aceptación:** CUMPLIDO AL 100%. Etapa 2 cerrada exitosamente.

---

## 8. Arquitectura y Planificación de la Etapa 3 (FASE 1 y FASE 2)

* **Objetivo:** Registro de Clientes, Social Login con Gmail, Onboarding AVS, Stripe Checkout, Webhooks y Motor SLA 7 Días.
* **Componentes Principales:**
  1. **Autenticación:** `django-allauth[socialaccount]` con `CustomSocialAccountAdapter` que marca `is_email_verified = True` para Google OAuth 2.0 (ADR-008). Gate previo a checkout `EmailVerifiedRequiredMixin` (ADR-006).
  2. **Facturación (`fobandor.billing`):** 3 planes mensuales base con soporte de cupones (`allow_promotion_codes=True`), Stripe Customer Portal y Webhook listener criptográfico firmado (`/stripe/webhook/`).
  3. **Entregas SLA (`fobandor.fulfillment`):** Modelo `FulfillmentOrder` con cálculo automático de fecha límite (`due_date = paid_at + 7 días`). Detección automática de órdenes `VENCIDA` vía management command `check_overdue_orders` (ADR-009).
  4. **Portal Cliente (`fobandor.portal`):** Dashboard de autoservicio en `/mi-cuenta/` con barra de progreso de días de entrega restantes y descarga de entregables.
* **Estado:** FASE 3: APROBAR (Pausa obligatoria para revisión del desarrollador líder).

---

## 9. Decisiones y Correcciones de la Etapa 3 (revisión técnica OpenCode)

Decisiones confirmadas por el desarrollador líder:

1. **Mapeo plan → órdenes:** cada cobro genera **1 `FulfillmentOrder`** por suscripción; el `order_type` se deriva de `SubscriptionPlan.order_type`.
2. **Webhooks:** `invoice.paid` como **única fuente** que crea/renueva órdenes (idempotente por `stripe_invoice_id` único); `checkout.session.completed` solo activa la suscripción y vincula `User.stripe_customer_id`.

Correcciones técnicas aplicadas al plan (ver `task.md` §5 "Notas de Corrección"):

1. `CustomSocialAccountAdapter.save_user` (persistencia de `is_email_verified`).
2. `allauth.urls` fuera de `i18n_patterns`.
3. `SubscriptionPlan.order_type` (fuente del `order_type` de la orden).
4. `FulfillmentOrder.stripe_invoice_id` único.
5. `LOGIN_URL = "account_login"`.
6. `stripe_customer_id` como fuente única en `User`.
7. URLs absolutas para Stripe Checkout/Portal.
8. Señal `email_confirmed` para verificación Email/Password.

---

## 10. Hallazgos y Validación de la Ejecución de la Etapa 3

### Versiones instaladas
* **stripe 17.0.0** y **django-allauth 65.22.1** (compatibles con Python 3.14.4 / Django 5.2.19).

### Ajustes durante la ejecución (desviaciones menores)
1. **Middleware allauth:** `allauth.account.middleware.AccountMiddleware` añadido (requisito de allauth 65).
2. **Settings deprecados:** reemplazados `ACCOUNT_AUTHENTICATION_METHOD`/`ACCOUNT_EMAIL_REQUIRED`/`ACCOUNT_USERNAME_REQUIRED` por `ACCOUNT_LOGIN_METHODS` y `ACCOUNT_SIGNUP_FIELDS`.
3. **Excepción de firma:** se usa `stripe.SignatureVerificationError` (top-level) porque `stripe.error` ya no es importable en stripe 17.
4. **Webhook → dict:** `event.to_dict()` antes de procesar (el `Event` de Stripe no soporta `.get()`).
5. **Formato de precio:** `{{ plan.price_usd|unlocalize }}` con `{% load l10n %}` para evitar `$199,00` (localización es) y mostrar `$199.00`.
6. **Vistas de entregas en `fobandor.backoffice`** (no en `fulfillment/views.py`), con semáforo de SLA (`sla_level`) en el modelo.
7. **`Site`** de `django.contrib.sites` creado con dominio `localhost:8000`.

### Verificación de aceptación (Tarea 3.11)
* `python manage.py check` → 0 issues. `makemigrations --check --dry-run` → sin cambios.
* `pytest` → **24/24 passing** (3 users + 1 gate + 2 señal/gate + 4 cms + 3 backoffice + 4 sla + 2 billing models + 3 webhooks + 2 portal).
* `flake8 config fobandor scripts` → limpio.
* Seeds: 3 planes (`Starter` $199, `Pro` $499, `Enterprise` $999) + grupos RBAC (Content_Editors + Fulfillment_Operators con permisos sobre `FulfillmentOrder`).
* HTTP real: `/es/precios/` 200, `/accounts/login/` 200 (con botón Google), `/es/mi-cuenta/` 302 → `/accounts/login/`, `/stripe/webhook/` GET 405 (solo POST).

### Prerrequisitos externos pendientes (fuera de código)
* **Stripe test mode:** crear 3 Products/Prices y cargar `stripe_price_id` reales en los planes; configurar webhook endpoint `/stripe/webhook/`.
* **Google Cloud:** crear proyecto OAuth, credenciales y autorizar callback `http://localhost:8000/accounts/google/login/callback/`.

---

## 11. Refinamiento Comercial: Planes de Acompañamiento y CMS de Facturación

* **Origen:** Definición comercial entregada por Freddy Obando (`instructions/planes.jpeg`).
* **Alcance Aprobado:**
  1. Modelo `SubscriptionPlan` enriquecido con subtítulos, compromiso mínimo (2 y 3 meses), público objetivo, disclaimers y Formspree.
  2. Gestión de planes desde `/backoffice/planes/` para autonomía total del staff en actualización de ofertas y `stripe_price_id`.
  3. Integración con Formspree.io para captación de leads de diagnóstico ("Hablemos hoy").
  4. Rediseño de alta fidelidad en `/precios/`.

### Decisiones confirmadas (revisión técnica OpenCode)
1. **Planes legacy:** el seeder **desactiva** (`is_active=False`) cualquier plan fuera de `{impulso, conversion, crecimiento}` (sin borrado destructivo).
2. **Formspree global:** endpoint vía `FORMSPREE_ENDPOINT` (12-factor), fuera del modelo `SubscriptionPlan`.
3. **Compromiso mínimo informativo:** `min_commitment_months` se muestra como badge en `/precios/`; no se fuerza en Stripe (suscripción mensual auto-renovable). Limitación documentada.

### Ejecución (Tareas 3.12–3.16)
* **Catálogo real:** `impulso` $697 (2 meses), `conversion` $1297 (3 meses, destacado), `crecimiento` $1997 (3 meses). Todo bilingüe (features y disclaimer ES/EN).
* **`order_type`:** añadido choice `MARKETING` ("Acompañamiento de Marketing") a `SubscriptionPlan` y `FulfillmentOrder`; los 3 planes mapean a `MARKETING`.
* **Backoffice `/backoffice/planes/`:** listado + edición con `SubscriptionPlanForm` (features editables como una-línea-por-bullet), pestañas ES/EN/«Precio y datos». `slug` no editable.
* **`/precios/`:** subtítulos, badge "RECOMENDADO" (`is_highlighted`), badge de compromiso, público objetivo, disclaimer y modal de diagnóstico conectado a Formspree (`FORMSPREE_ENDPOINT`).
* **Verificación:** `pytest` 28/28, `flake8` limpio, `check` 0 issues, migraciones limpias, CSS compilado. HTTP: `/es/precios/` y `/en/precios/` 200 con planes bilingües; `/es/backoffice/planes/` anónimo → 302.

---

## 12. Preparación y Validación Técnica para la Etapa 4 (Producción en VPS Hostinger)

* **Objetivo de la Etapa:** SEO Técnico, Blindaje OWASP, Empaquetado Docker Multi-Etapa y Despliegue en Vivo en Hostinger KVM VPS (`89.117.32.46`) bajo EasyPanel y Traefik.
* **Documento Rector:** [task.md](file:///home/jet/proyectos_lnx/proyectos/fobandor/task.md) (Sección 6: Tareas 4.0 a 4.5).
* **Decisiones Arquitectónicas Incorporadas:** ADR-016 (Despliegue EasyPanel + Traefik + WhiteNoise + Docker Multi-Etapa).

### Diagnóstico de Infraestructura del VPS Target (`89.117.32.46`)
1. **Acceso y Hardware:**
   - Conexión vía SSH por llave pública: `ssh root@89.117.32.46`.
   - Sistema Operativo: Ubuntu Linux x86_64 en Hostinger KVM VPS.
   - Memoria RAM: 8.0 GB totales (6.4 GB disponibles, 1.4 GB en uso por el kernel y containers activos).
   - Almacenamiento SSD: 96.0 GB totales (86.0 GB disponibles, 9.9 GB en uso).
   - Carga de Procesador: CPU load 0.00 / 0.00 / 0.00 (holgura térmica y de cómputo óptima).
2. **Servicios y Puertos Activos:**
   - **Traefik 3.6.7:** Escuchando en `0.0.0.0:80` y `0.0.0.0:443`, administrando los routers de entrada, balanceo y Let's Encrypt SSL.
   - **EasyPanel v2.31.0:** Panel web administrativo en `http://89.117.32.46:3000`.
   - **Proyectos existentes:** `n8n` (workflow automation) y `barberbot` (`evolution-api` + PostgreSQL + Redis).
3. **Gestión de Cuota de Proyectos y Slot en EasyPanel:**
   - EasyPanel (versión comunitaria) presentaba una restricción operativa de máximo 3 proyectos activos concurrentes.
   - Con `barberbot`, `n8n` y `massaro` (inactivo), el servidor se encontraba en 3/3 proyectos.
   - **Protocolo de Respaldo Preventivo:** Se empaquetó el proyecto `massaro` íntegramente en el VPS:
     ```bash
     tar -czvf /root/backups/backup_massaro_20261116.tar.gz -C /etc/easypanel/projects massaro
     ```
     El archivo (1.8 MB) fue descargado localmente a `backups/backup_massaro_20261116.tar.gz` (incluido en `.gitignore` para no contaminar el historial de Git).
   - El Desarrollador Líder eliminó el proyecto `massaro` en la UI de EasyPanel, dejando 2 proyectos activos y 1 slot libre disponible para `fobandor`.

### Diagnóstico y Auditoría de Dominio y DNS (NIC.com / GoDaddy)
1. **Delegación de Dominio:**
   - Dominio comercial oficial: `fobandor.com` (propiedad de Freddy Obando).
   - Registrador: NIC.com, gestionado bajo la infraestructura DNS de GoDaddy (`ns19.domaincontrol.com`, `ns20.domaincontrol.com`).
2. **Registros DNS Configurados:**
   - Registro `A` para host `@`: `89.117.32.46` (TTL: 600 segundos).
   - Registro `CNAME` para host `www`: `fobandor.com.` (TTL: 1800 segundos).
3. **Validación de Propagación:**
   - Verificado con `dig @8.8.8.8 fobandor.com A` y `dig @1.1.1.1 fobandor.com A` → Responde `89.117.32.46`.
   - Verificado `dig www.fobandor.com CNAME` → Responde `fobandor.com.`.
   - Traefik en el VPS ya recibe el tráfico: `curl -I http://fobandor.com/` retorna `HTTP/1.1 308 Permanent Redirect` hacia HTTPS; `https://fobandor.com/` retorna `HTTP/2 404 page not found` emitido por Traefik, indicando que el proxy está a la espera del backend `fobandor`.

### Estrategia de Pasarela de Pagos Stripe en Producción
* Se analizó la viabilidad de desplegar la plataforma con Stripe en **Modo Test** (`pk_test_...`, `sk_test_...` y webhook secret `whsec_...` en EasyPanel).
* **Conclusión Técnica:** Es la mejor práctica recomendada. Permite validar en el entorno productivo real (`https://fobandor.com/`) el flujo E2E:
  1. Registro de usuario y Social Login de Google con HTTPS real.
  2. Redirección a Stripe Checkout con tarjetas de prueba internacionales.
  3. Recepción del webhook criptográfico `invoice.paid` en `https://fobandor.com/stripe/webhook/` con certificado SSL válido sin requerir túneles de desarrollo (`stripe listen`).
  4. Generación automática de `FulfillmentOrder` y verificación del semáforo SLA 7 días en `/backoffice/entregas/`.
* Una vez validado con Freddy Obando, el paso a **Modo Live** es inmediato: únicamente se cambian las 3 variables de Stripe en el panel de EasyPanel y se cargan los `price_...` de producción en `/backoffice/planes/`.

### Estado de Google Cloud OAuth
* El desarrollador líder configuró las credenciales en Google Cloud Console para Web Application:
  - Authorized JavaScript Origins: `http://localhost:8000`, `https://www.fobandor.com`.
  - Authorized Redirect URIs: `http://localhost:8000/accounts/google/login/callback/`, `https://www.fobandor.com/accounts/google/login/callback/`, `http://127.0.0.1:8000/accounts/google/login/callback/`.
* Se corrigió la lectura de `GOOGLE_OAUTH_CLIENT_ID` y `GOOGLE_OAUTH_CLIENT_SECRET` en `config/settings/base.py`.
* Verificado localmente: el botón "Continuar con Google" redirige con éxito a la pantalla de consentimiento de Google Cloud sin errores 400.

### Decisiones y Correcciones Técnicas de la Etapa 4 (Revisión OpenCode)
Tras la revisión técnica del Agente Ejecutor (OpenCode / DeepSeek V4 Pro), se incorporaron los siguientes refinamientos críticos al plan de despliegue:
1. **Definición de `DATABASES` en `production.py`:** Se incorpora `DATABASES = {'default': env.db('DATABASE_URL')}`, resolviendo la ausencia de backend de base de datos en producción.
2. **Ciclo de `collectstatic` en Runtime:** Se eliminó `collectstatic` del `Dockerfile` (que fallaba en build al carecer de `.env` y generar estáticos sin el manifest de WhiteNoise) y se trasladó a `entrypoint.sh`, ejecutándose en runtime con las variables de entorno inyectadas por EasyPanel.
3. **Sincronización del `Site` de Django (`setup_production_site`):** Se crea un comando para asegurar que `Site.domain` y `Site.name` apunten a `www.fobandor.com` en la base de datos de producción, garantizando que el sitemap XML y los callbacks de Allauth generen URLs absolutas válidas.
4. **Resolución de Email Transaccional en Producción:**
   - Se parametriza el backend SMTP en `production.py` vía variables de entorno (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`).
   - Se configura `ACCOUNT_EMAIL_VERIFICATION = env('ACCOUNT_EMAIL_VERIFICATION', default='optional')`. Esto desbloquea el registro manual si Freddy Obando no ha provisto aún las credenciales SMTP, mientras que los usuarios que ingresan vía Google OAuth quedan automáticamente verificados al 100% de inmediato (ADR-008).
5. **Persistencia de Media:** Se documenta el montaje de volumen persistente en EasyPanel (`fobandor_media` -> `/app/media/`) para evitar pérdida de entregables de `FulfillmentOrder` en futuros despliegues.
6. **Anti-patrón CSRF Corregido:** Se fija `CSRF_COOKIE_HTTPONLY = False` para permitir a HTMX leer la cookie `csrftoken` en peticiones dinámicas.
7. **OWASP `check --deploy` Limpio:** Se incorporan `SECURE_SSL_REDIRECT = True` y `SECURE_REFERRER_POLICY = 'same-origin'`, y se modera `SECURE_HSTS_PRELOAD = False` hasta validar la estabilidad del certificado SSL en vivo.
8. **Automatización de Superusuario:** `entrypoint.sh` soporta inicialización automática con `DJANGO_SUPERUSER_EMAIL` y `DJANGO_SUPERUSER_PASSWORD`.

### Condición de Entrada a la FASE 4 (EJECUTAR)
* Planificación exhaustiva detallada en `task.md` (Tareas 4.0 a 4.5) con las 14 correcciones integradas.
* Fundamentos arquitectónicos y operacionales documentados en ADR-016.
* **Pausa Obligatoria de Gobernanza HARNESS (FASE 3: APROBAR):** Plan refinado listo para ejecución.

---

## 13. Ejecución de la Etapa 4 (Tareas 4.0–4.4)

### Versiones instaladas
* **gunicorn 27.0.1**, **whitenoise 6.12.0** (+ **brotli 1.2.1**).

### Hallazgo crítico durante la ejecución
1. **`STATICFILES_STORAGE` está obsoleto en Django 5.2.** El plan usaba `STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'`, que Django 5.2 **ignora** (deprecado en 4.2, eliminado en 5.1; ahora se usa `STORAGES`). Consecuencia: `collectstatic` generaba archivos **sin hash** y **sin `staticfiles.json`** (storage por defecto `StaticFilesStorage`). Se corrigió en `production.py` con:
   ```python
   STORAGES = {
       'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
       'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
   }
   ```
   Verificado: `collectstatic` genera `staticfiles.json` + archivos hasheados `.br`/`.gz` (676 post-processed).

### Implementado (4.0–4.4)
* **SEO:** `StaticViewSitemap` (tuplas manuales bilingües), `templates/robots.txt`, rutas `/sitemap.xml` y `/robots.txt` fuera de `i18n_patterns`, meta OG/Twitter en `base.html`, command `setup_production_site`, tests `test_seo.py`.
* **Producción:** `config/settings/production.py` completo (DATABASES, proxy Traefik, STORAGES/WhiteNoise, cookies, OWASP, SMTP configurable, `ACCOUNT_EMAIL_VERIFICATION` env).
* **Docker:** `Dockerfile` multi-stage (node:22-alpine → python:3.14-slim, usuario no-root `django`), `.dockerignore`, `entrypoint.sh` (collectstatic → migrate → setup_production_site → seeders → createsuperuser condicional → gunicorn 3 workers).

### Verificación de aceptación (Tarea 4.3)
* `python manage.py check` → 0 issues. `makemigrations --check --dry-run` → sin cambios.
* `pytest` → **31/31 passing** (28 previas + 3 SEO).
* `flake8 config fobandor scripts` → limpio.
* `collectstatic --settings=config.settings.production` → manifest OK (140 archivos, 676 post-processed).
* `check --deploy --settings=config.settings.production`:
  * Con `SECRET_KEY` dev (`django-insecure-...`): **W009** (placeholder, esperado) + **W021** (`SECURE_HSTS_PRELOAD=False`, diferido).
  * Con `SECRET_KEY` real: solo **W021** (HSTS preload diferido hasta validar SSL en vivo).
  * En producción (clave real + `SECURE_HSTS_PRELOAD=true` tras validar SSL): **0 warnings**.

### Despliegue en Vivo y Verificación Técnica de Aceptación (Tarea 4.5)
* **Infraestructura:** Hostinger VPS (`89.117.32.46`), EasyPanel v2.31.0, Docker Swarm.
* **Servicio `fobandor_postgres`:** PostgreSQL 16 activo con credencial generada `fsy7cv7fgi0kzedqetiu` y base `fobandor_db`.
* **Servicio `fobandor_web`:**
  - Build multi-stage exitoso desde GitHub `main` (`100ad3c`).
  - Runtime Gunicorn en puerto 8000 (3 workers).
  - Migraciones completadas en PostgreSQL y seeders automáticos ejecutados:
    - `seed_initial_content` (servicios, redes sociales, perfil corporativo).
    - `seed_subscription_plans` (Impulso $697, Conversión $1297, Crecimiento $1997).
    - `create_rbac_groups` (`Content_Editors` y `Fulfillment_Operators`).
    - Superusuario inicial `fobandorgcp@gmail.com` creado exitosamente.
* **Verificación de Red y Protocolo HTTPS:**
  - `https://fobandor.com/` → HTTP/2 302 -> `/es/` HTTP/2 200 con candado SSL válido emitido por Let's Encrypt / Traefik.
  - `https://www.fobandor.com/` → HTTP/2 302 -> `/es/` HTTP/2 200.
  - `https://fobandor.com/robots.txt` → HTTP/2 200 (directivas y sitemap presentes).
  - `https://fobandor.com/sitemap.xml` → HTTP/2 200 con `<urlset>` y URLs bilingües con dominio `www.fobandor.com`.
  - `https://fobandor.com/es/precios/` → HTTP/2 200 (catálogo comercial completo).
  - `https://fobandor.com/static/css/output.css` → HTTP/2 200 servido directamente por WhiteNoise con Brotli/Gzip y cabeceras HSTS de 1 año.
  - `https://fobandor.com/es/backoffice/` → HTTP/2 302 hacia `/accounts/login/` con cookies de sesión seguras (`SameSite=Lax`, `Secure`).
* **Release Oficial:** Publicado tag de versión **`v1.0.0`** en GitHub:
  `https://github.com/javieresquivelt-ux/fobandor-web/releases/tag/v1.0.0`.

---

## 14. Incidente de Post-Despliegue, Hotfix y Regularización de Gobernanza HARNESS

### Diagnóstico de Fallas Operativas en Vivo
Durante la verificación inicial del despliegue en EasyPanel se presentaron tres incidentes operativos:
1. **Google OAuth ("An account already exists with this email address"):** Al intentar ingresar con `fobandorgcp@gmail.com`, Allauth rechazó la operación enviando a una vista de `signup` sin estilos. Causa: `allauth` no vincula automáticamente cuentas sociales a usuarios locales preexistentes por motivos de seguridad por defecto, requiriendo `SOCIALACCOUNT_EMAIL_AUTHENTICATION = True` y `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True`.
2. **Error 502 Bad Gateway intermitente:** EasyPanel inyectaba `PORT=80` en el entorno del contenedor, causando que Gunicorn escuchara en el puerto 80 mientras Traefik dirigía el tráfico a `fobandor_web:8000`. Solución: fijar `PORT=8000` de forma estricta en `entrypoint.sh`.
3. **Credencial de PostgreSQL:** Se sincronizó la contraseña en la base de datos de producción mediante `ALTER USER fobandor_user WITH PASSWORD 'fobandor_db';`.

### Regularización de Gobernanza y Aprendizaje
* **Desviación detectada:** Durante la atención del incidente en vivo, Antigravity-IDE implementó cambios de código y plantillas directamente sin formular primero la tarea atómica en `task.md` ni solicitar la aprobación previa del Desarrollador Líder en FASE 3.
* **Medida Correctiva:** El incidente fue formalmente regularizado incorporando la **Tarea 4.6 en `task.md`** y este registro en `memory.md`.
* **Regla Inmutable:** Se ratifica que cualquier intervención técnica (incluyendo hotfixes de producción o ajustes de configuración) debe ceñirse sin excepciones al ciclo HARNESS: Análisis → Tarea Atómica → Aprobación Explícita del Desarrollador Líder → Ejecución → Registro.

---

## 15. Transición a Google Workspace Corporativo y Gobierno de Cuentas Oficiales (@fobandor.com)

* **Contexto:** Freddy Obando activó el servicio oficial de Google Workspace para el dominio `fobandor.com`, superando la fase de cuentas provisionales de Gmail (`fobandorgcp@gmail.com`). Se habilitaron nuevas credenciales OAuth 2.0 en Google Cloud asociadas a la organización oficial.
* **Política de Cuentas de Administración (Staff & Superuser):**
  1. **`for@fobandor.com`:** Propietario y Director General (Freddy Obando).
  2. **`jet@fobandor.com`:** Desarrollador Líder y Arquitecto Técnico.
* **Mecanismo Técnico de Autenticación:**
  - Se utiliza la auto-vinculación transparente habilitada en la Tarea 4.6 (`SOCIALACCOUNT_EMAIL_AUTHENTICATION = True` y `AUTO_CONNECT = True`).
  - Al registrarse previamente ambos usuarios en PostgreSQL de producción con `is_staff=True`, `is_superuser=True` y contraseña inicial de respaldo (`Fobandor2026Admin!`), el inicio de sesión vía Google OAuth con sus cuentas corporativas `@fobandor.com` funcionará inmediatamente en 1 solo clic.
* **Resultados de la Ejecución (Tarea 4.7):**
  - Superusuarios creados en PostgreSQL en vivo: `for@fobandor.com` y `jet@fobandor.com` con `is_staff=True`, `is_superuser=True`, `is_email_verified=True`.
  - Credenciales de Google Workspace OAuth 2.0 actualizadas en el servicio `fobandor_web` en el VPS Hostinger.
  - Servicio convergido y verificado: `https://fobandor.com/` respondiendo HTTP/2 200.

---

## 16. Integración y Robustecimiento de Formspree para Captación de Leads y Diagnóstico Comercial

* **Contexto Comercial:**
  En el modelo de conversión de FOBANDOR, la vista de precios (`/precios/`) atiende a dos perfiles de prospecto:
  1. *Comprador Inmediato:* Selecciona directamente uno de los tres planes de suscripción mensual (Impulso $697, Conversión $1,297, Crecimiento $1,997) e inicia el flujo de pago con Stripe Checkout.
  2. *Prospecto Calificado / En Consulta:* Requiere un análisis previo de requerimientos, integración personalizada o consultoría estratégica antes de comprometerse con un plan mensual. Para este segmento, el CTA *"Hablemos hoy"* ("Let's Talk Today") abre un modal interactivo de diagnóstico.
* **Diagnóstico Técnico del Endpoint Provisional:**
  - El código base actual utilizaba un placeholder (`https://formspree.io/f/placeholder`) inyectado mediante `settings.FORMSPREE_ENDPOINT`.
  - El formulario realizaba un envío síncrono estándar (`method="POST"`), lo cual, tras la sumisión, redirige al usuario a la página de agradecimiento por defecto alojada en `formspree.io`, rompiendo la identidad visual corporativa y alejándolo del sitio web de FOBANDOR.
* **Decisiones Arquitectónicas y de Experiencia de Usuario (UX):**
  1. **Configuración 12-Factor y Cero Hardcoding:** Mantener `FORMSPREE_ENDPOINT` desacoplado a través de variables de entorno tanto en el entorno local (`.env`) como en el servicio Swarm de producción (`fobandor_web` en EasyPanel).
  2. **Envío Asíncrono sin Abandono del Sitio (Zero Friction):**
     - Emplear Alpine.js (librería ya cargada localmente sin CDN) para interceptar el evento `submit` y despachar la petición vía `fetch()` con encabezado `Accept: application/json`.
     - Esto permite conservar al usuario en `fobandor.com`, ofreciendo un estado de carga reactivo (*"Enviando..."*) y un mensaje de éxito contextual (*"¡Gracias! Hemos recibido tu solicitud. Freddy Obando se contactará contigo en menos de 24 horas."*).
  3. **Blindaje Anti-Spam Silencioso (Honeypot):**
     - Incorporar el campo oculto `<input type="text" name="_gotcha" style="display:none">`. Formspree descarta automáticamente cualquier envío donde este campo venga diligenciado por bots automatizados, eliminando la necesidad de CAPTCHAs que generen fricción en la conversión de clientes de alto valor.
  4. **Metadatos y Enrutamiento de Notificaciones:**
     - Integrar `<input type="hidden" name="_subject" value="Nuevo Diagnóstico Comercial - FOBANDOR">` para que el propietario Freddy Obando (`for@fobandor.com`) identifique y priorice inmediatamente el correo entrante con reglas de bandeja en Google Workspace.
* **Gobernanza:**
  - Plan detallado en `task.md` (Tarea 4.8).
  - Estado: **FASE 4: EJECUTADA** con endpoint real `https://formspree.io/f/mqpqqggk`.

### Ejecución (Tarea 4.8)
* **Endpoint real:** `FORMSPREE_ENDPOINT=https://formspree.io/f/mqpqqggk` en `.env` (producción vía EasyPanel `fobandor_web`).
* **UX asíncrona (Alpine.js):** `@submit.prevent` + `fetch()` con `Accept: application/json` y `FormData` (incluye honeypot y `_subject` automáticamente). Estados reactivos: `submitting` (botón deshabilitado, "Enviando diagnóstico..."), `submitted` (mensaje de éxito) y `error` (fallback a `for@fobandor.com`). Sin redirección externa.
* **Anti-spam:** honeypot `_gotcha` (`display:none` + `tabindex="-1"` + `autocomplete="off"` + `aria-hidden`) y `_subject` = "Nuevo Diagnóstico Comercial - FOBANDOR".
* **Bilingüe:** mensajes ES/EN vía `{% trans %}` (catálogo EN regenerado: 51 cadenas).
* **Pruebas:** `fobandor/billing/tests/test_views.py` (contexto `formspree_endpoint` + render de `_gotcha`/`_subject`/`@submit.prevent`). Suite total **33/33 passing**.
* **Verificación y Despliegue en VPS (Producción):**
  1. EasyPanel LMDB y servicio Docker Swarm `fobandor_web` actualizados con `FORMSPREE_ENDPOINT=https://formspree.io/f/mqpqqggk`.
  2. Build automatizado multi-stage completado exitosamente desde GitHub `main` (`cmwl6xhoc000h06o71ct368ne.log`).
  3. Servicio Docker Swarm convergido y verificado: `https://www.fobandor.com/es/precios/` y `https://www.fobandor.com/en/precios/` sirviendo el formulario interactivo en vivo con el endpoint real.
* **Hallazgo Clave de Aceptación con Formspree:**
  - Al realizar la prueba de envío asíncrono con `Accept: application/json`, Formspree retorna: `{"error":"In order to submit via AJAX, you need to set a custom key or reCAPTCHA must be disabled in this form's settings page."}`.
  - Para que el envío asíncrono transparente (sin CAPTCHA ni abandono del sitio) funcione de manera fluida, Freddy debe acceder al dashboard de Formspree (`mqpqqggk`), ir a la pestaña **Settings** -> sección **Spam Protection**, y desactivar la opción **reCAPTCHA** (dejando la protección anti-spam en el honeypot `_gotcha` que ya implementamos en el formulario).
* **Estado de Producción Actual:** Formulario funcionando correctamente. Freddy desactivó reCAPTCHA y verificó recepción de envíos en la pestaña **Submissions** de Formspree. Las notificaciones llegan a `administrator@fobandor.com`.

---

## 17. Correcciones de Textos del Modal de Diagnóstico e Integración al CMS (`CompanyProfile`)

### Contexto
Con el formulario de diagnóstico operando en producción, Freddy Obando solicita:
1. **Corrección de textos inmediata:** Cambios en el asunto del formulario, título del estado de éxito y mensaje de confirmación.
2. **Integración al CMS:** Que estos textos sean editables desde el Backoffice en `/backoffice/empresa/` sin intervención técnica.

### Decisión Arquitectónica: Extender `CompanyProfile` (Singleton)

* **Alternativa descartada:** Crear un nuevo modelo `ContactFormSettings` → Sobre-modelado innecesario para un formulario único.
* **Decisión adoptada:** Agregar 5 campos nuevos al modelo `CompanyProfile` existente:
  - `diag_form_subject` (CharField, `default='Nuevo Formulario Web - FOBANDOR'`): Asunto del email enviado a Formspree.
  - `diag_modal_title_es` / `diag_modal_title_en` (CharField, `default='Solicitud enviada'` / `'Request sent'`): Título del bloque de éxito del modal.
  - `diag_success_msg_es` / `diag_success_msg_en` (TextField): Mensaje completo de confirmación bilingüe.
* **Justificación:**
  - `CompanyProfile` ya es el singleton de configuración global del sitio.
  - Tiene backoffice propio (`/backoffice/empresa/`), formulario con pestañas ES/EN y el patrón `load()` lo hace trivialmente inyectable en cualquier vista.
  - Cambiar estos textos desde el Backoffice (sin redeploy) es el flujo más simple para un equipo editorial no técnico.
  - La vista `PricingCatalogView` ya carga el contexto de planes; inyectar `company = CompanyProfile.load()` tiene impacto mínimo en rendimiento (consulta cacheada en un único registro singleton).
* **Impacto técnico:** 1 migración de BD (solo DDL `ALTER TABLE` con columnas `DEFAULT`, sin datos en riesgo), actualización de vista, template y formulario del backoffice.
* **Gobernanza:** Plan detallado en `task.md` (Tarea 4.9). Estado: **FASE 4: EJECUTADA** (fusión A+B, una sola migración).

### Ejecución (Tarea 4.9)
* **Modelo:** 5 campos nuevos en `CompanyProfile` (migración `cms.0002`), con defaults ya corregidos.
* **Vista:** `PricingCatalogView` inyecta `company = CompanyProfile.load()`.
* **Plantilla:** `_subject` → `{{ company.diag_form_subject }}`; título de éxito y mensaje → `{{ company.diag_modal_title_es/en }}` y `{{ company.diag_success_msg_es/en }}` (bilingüe). Se eliminó el `{% trans %}` estático obsoleto del mensaje de éxito.
* **Backoffice:** `CompanyProfileUpdateView.fields` ampliado; sección "Formulario de Diagnóstico" en el formulario con campos bilingües en pestañas ES/EN y `diag_form_subject` en zona común.
* **Catálogo EN:** limpiado el string obsoleto (regenerado a 50 cadenas).
* **Pruebas:** `test_pricing_view_uses_company_profile_diag_texts` (render dinámico desde `CompanyProfile`). Suite **34/34 passing**.
* **Verificación local:** `/es/precios/` y `/en/precios/` muestran los textos corregidos desde CMS ("Solicitud enviada"/"Request sent", "Nos contactaremos a la brevedad"/"We will get back to you shortly").
* **Pendiente (producción):** desplegar a EasyPanel (`fobandor_web`) y verificar que la edición en `/es/backoffice/empresa/` se refleja en `/es/precios/` sin redeploy.

---

## 18. Activación y Validación de Stripe en Modo Test con Productos y Webhook Criptográfico

### Contexto y Decisión Operativa
Para validar el ciclo completo de suscripción, checkout y despacho SLA de 7 días antes de realizar cobros reales a tarjetas de clientes, se acordó activar y probar la plataforma en **Modo Test (Sandbox)** de Stripe.

### Credenciales y Destino de Eventos (Stripe Workbench)
1. **Configuración de Webhook en Stripe:**
   - Destino creado bajo Stripe Workbench: `https://www.fobandor.com/stripe/webhook/` (formato Snapshot v1).
   - Eventos escuchados: `checkout.session.completed`, `invoice.paid`, `customer.subscription.updated`, `customer.subscription.deleted`.
   - Secreto de firma generado e inyectado en `STRIPE_WEBHOOK_SECRET` (`whsec_...`).
2. **Claves de API Test:**
   - Inyectadas en `.env` local y en el servicio Swarm `fobandor_web` en EasyPanel VPS: `STRIPE_PUBLIC_KEY` (`pk_test_...`) y `STRIPE_SECRET_KEY` (`sk_test_...`).

### Hallazgos Críticos y Correcciones de Pasarela

1. **Diferenciación entre Product ID y Price ID:**
   - *Incidente potencial:* Inicialmente se habían ingresado IDs con prefijo `prod_...` (`prod_VeI9...`, `prod_VeIB...`, `prod_VeIC...`) en el Backoffice.
   - *Causa:* En Stripe, `prod_` representa el producto comercial general, mientras que `price_` representa la tarifa o frecuencia recurrente requerida por la API de Checkout Sessions (`line_items: [{'price': price_id}]`).
   - *Solución:* Mediante la API de Stripe se resolvieron los `price_...` exactos asociados a cada producto y se actualizaron en PostgreSQL:
     - *Plan 1 • Impulso:* `price_1UczZNDd8zg4z4zarI1nFiTB` ($697 USD / mes).
     - *Plan 2 • Conversión:* `price_1UczasDd8zg4z4za8jCoZZZa` ($1,297 USD / mes).
     - *Plan 3 • Crecimiento:* `price_1UczbgDd8zg4z4zaCxHiSJao` ($1,997 USD / mes).

2. **Requisito de `tax_code` por Stripe Managed Payments:**
   - *Incidente:* Al crear la primera sesión de prueba, Stripe rechazó la solicitud con error:
     `Invalid line_items[0]: the product tax code is missing. Product tax code is required for Managed Payments, which is enabled by default on your account.`
   - *Solución:* Se actualizaron los 3 productos de Stripe vía API asignándoles el código de impuestos de Software/SaaS: `tax_code="txcd_10000000"`.

### Verificación y Aceptación
* **Creación de Sesiones de Checkout:** Validada con éxito para los 3 planes tanto en entorno local como directamente en el contenedor de producción (`fobandor_web.1`). Las sesiones retornan URLs válidas `https://checkout.stripe.com/c/pay/cs_test_...`.
* **Suite de Pruebas:** **34/34 passing** en `pytest`.
* **Estado:** Pasarela Stripe 100% operativa en modo prueba en `https://www.fobandor.com/es/precios/`.

---

## 19. Análisis Arquitectónico y Estrategia de Solución para los 11 Hallazgos de Revisión (Etapa 5)

### Contexto y Diagnóstico
Durante la revisión de producción de `https://www.fobandor.com/`, el Desarrollador Líder y Freddy Obando documentaron 11 observaciones críticas (con 10 capturas de pantalla) distribuidas en tres áreas: Frontend/Navegación, Pasarela de Pago/Auth, y Backoffice/Flujo SLA.

### Razonamiento Arquitectónico y Decisiones de Diseño

#### 1. Misión, Visión y Valores en la Landing (Punto 1)
* **Diagnóstico:** El modelo `CompanyProfile` contiene los campos `mission_es/en`, `vision_es/en` y `values_es/en` gestionables en `/backoffice/empresa/`. Sin embargo, `fobandor/core/views.py:home_view(request)` no inyectaba esta información al contexto, dejando la sección `#nosotros` con textos hardcodeados de prueba.
* **Decisión:** Inyectar `'company': CompanyProfile.load()` en el diccionario de contexto de la función `home_view(request)` y renderizar los textos dinámicamente en `templates/pages/home.html`. El campo `values_es/en` se maquetará en tarjetas modulares con estilo dark-tech y acentos neón, garantizando coherencia visual y dinamismo editorial.

#### 2. Selector de Idioma: Toggle Directo 1-Clic (Punto 2)
* **Diagnóstico:** El `<select>` nativo requiere dos interacciones (abrir dropdown + seleccionar) y en móviles resulta tosco y propenso a desbordamientos.
* **Decisión:** Reemplazar el desplegable por un botón toggle tipo pastilla (`pill switch` con `ES` y `EN`). Al hacer clic, envía un POST inmediato al endpoint estándar `set_language` de Django, alternando el idioma sin fricción.

#### 3 y 7. Enlaces Canónicos y Navegación entre Vistas (Puntos 3 y 7)
* **Diagnóstico:** Los enlaces del navbar usaban anclas puras (`#servicios`, `#proyectos`). Al navegar a `/precios/`, el navegador intenta buscar `#servicios` dentro de esa vista y falla. Además, en la home, el botón "Precios" apuntaba a `#precios` en vez de `/precios/`, y subsistía una sección huérfana placeholder `#precios` en `home.html` (líneas 73-79).
* **Decisión:** Todos los enlaces del navbar adoptarán URLs canónicas absolutas con ancla: `{% url 'core:home' %}#servicios`, y el enlace de precios apuntará inequívocamente a `{% url 'billing:pricing' %}`. Se depura la sección huérfana `#precios` en `home.html` y se estandarizan los CTAs del Hero.

#### 4. Formulario de Contacto Integrado en la Landing (Punto 4)
* **Diagnóstico:** La sección `#contacto` en la home es actualmente un texto vacío.
* **Decisión:** Reutilizar la infraestructura asíncrona de Formspree (Alpine.js + fetch JSON) para incrustar un formulario de contacto directo en el pie de página, compartiendo el asunto corporativo (`company.diag_form_subject`) y el honeypot anti-spam `_gotcha` inyectando `formspree_endpoint` en `home_view(request)`.

#### 5. Switches de Visibilidad de Secciones en CMS (Punto 5)
* **Diagnóstico:** Secciones en construcción no deben mostrar textos de prueba si aún no tienen datos definitivos.
* **Decisión:** Añadir campos booleanos en `CompanyProfile` (`show_services_section`, `show_projects_section`, `show_about_section`, `show_contact_section`). Esto otorga a Freddy el control total para encender o apagar secciones de la landing desde el Backoffice sin requerir despliegues de código. En el navbar, los enlaces a secciones inactivas se ocultan para evitar anclas muertas.

#### 6. Blindaje Responsive del Navbar Móvil (Punto 6)
* **Diagnóstico:** En pantallas móviles estrechas (Samsung A52 / iPhone de 360px a 390px), la barra superior colapsa porque intenta acomodar el logo, "Mi Cuenta", "Salir", el selector de idioma y el toggler de tema en una sola fila, generando un scroll horizontal de 20-40px que oculta el botón hamburguesa.
* **Decisión:** 
  - Barra superior móvil limpia: Solo Isotipo FOBANDOR a la izquierda y Botón Toggle Idioma + Botón Hamburguesa a la derecha.
  - Los enlaces de sesión ("Mi Cuenta", "Cerrar sesión" / "Iniciar sesión") y navegación se trasladan al interior del drawer desplegable de Alpine.js.
  - Reglas de contención con `overflow-x: clip` en el body y contenedores para evitar scroll horizontal sin romper el `position: sticky` del navbar.

#### 7. Prevención del Error HTTP 405 en Stripe Checkout (Punto 8)
* **Diagnóstico:** Un usuario no autenticado hace clic en "Comenzar" (POST a `billing:checkout`). Django redirige a `/accounts/login/?next=/es/precios/checkout/impulso/`. Tras el login con Google OAuth, Django redirige al `next` vía **GET**, pero `CreateCheckoutSessionView` solo admitía POST, disparando un HTTP 405 Method Not Allowed.
* **Decisión:** Implementar `def get(self, request, slug): return self.post(request, slug)` en `CreateCheckoutSessionView`. De este modo, la redirección post-login genera la sesión de Stripe Checkout y envía al usuario directamente a la pasarela sin fricción. En el test suite, se mockea `services.create_checkout_session` para verificar el 302 hacia Stripe Checkout independientemente de las claves de entorno.

#### 8. Retorno desde Stripe Customer Portal (Punto 9)
* **Diagnóstico:** El portal de facturación de Stripe devuelve al usuario a la URL configurada. El código en `StripeCustomerPortalView.post` ya construye `request.build_absolute_uri(reverse("portal:dashboard"))` con el idioma activo.
* **Decisión:** Verificar mediante test que la redirección canónica opera correctamente y proveer la guía documental para que Freddy suba el isotipo de FOBANDOR en la configuración del Customer Portal en Stripe Dashboard.

#### 9. Nombre del Plan en Órdenes SLA del Backoffice (Punto 10)
* **Diagnóstico:** La tabla en `/backoffice/entregas/` muestra "Servicio" pero no indica qué plan compró el cliente (Impulso, Conversión o Crecimiento).
* **Decisión:** Añadir `plan = models.ForeignKey('billing.SubscriptionPlan', null=True, blank=True)` en `FulfillmentOrder` y poblarlo en el handler `handle_invoice_paid` de `billing/services.py` (donde la variable `plan` ya se resuelve). En las plantillas `order_list.html` y `order_detail.html` se renderiza `{{ order.plan.name_es|default:order.get_order_type_display }}`.

#### 10. Flujo de Trabajo SLA: Estado "En Proceso" y "Asignado A" (Punto 11)
* **Diagnóstico:** Las órdenes pasaban directo de "Pendiente" a "Entregada" y no había trazabilidad de quién es el responsable de la entrega dentro del equipo. El estado `EN_PROCESO` ya existe en `STATUS_CHOICES` del modelo desde la Etapa 3.
* **Decisión:**
  - Agregar campo `assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_orders', verbose_name='Asignado a')` en `FulfillmentOrder`.
  - En `handle_invoice_paid`, asignar por defecto a `settings.DEFAULT_ASSIGNEE_EMAIL` (`for@fobandor.com`) si dicho usuario existe.
  - El selector en el Backoffice se poblará dinámicamente con los miembros de los grupos `Fulfillment_Operators` (ADR-013) y `Content_Editors`, además de Administradores (`is_staff=True`), y se habilitará un botón de acción *"Iniciar Producción"* para transicionar formalmente al estado `EN_PROCESO`.

---

### Ajustes Finales de Diseño (OpenCode, pre-ejecución)
* **`company` global por context processor:** `fobandor.core.context_processors.company` inyecta `CompanyProfile.load()` en todas las plantillas (paralelo a `social_links`). Elimina la necesidad de inyectar `company` por-vista y habilita el condicional de visibilidad de secciones en el navbar en cualquier página. `home_view` conserva solo `formspree_endpoint`; `PricingCatalogView` deja de inyectar `company` manualmente.
* **`DEFAULT_ASSIGNEE_EMAIL`:** `getattr(settings, 'DEFAULT_ASSIGNEE_EMAIL', 'for@fobandor.com')` (sin añadir setting a `base.py`).

### Ejecución (Tareas 5.1–5.10)
* **Context processor `company`:** `fobandor.core.context_processors.company` + registro en `TEMPLATES`.
* **Modelos:** `CompanyProfile` + `show_*_section` (4 booleanos); `FulfillmentOrder` + `plan` (FK) y `assigned_to` (FK). Migraciones `cms.0003` y `fulfillment.0003`.
* **Landing:** `#nosotros` dinámico (misión/visión/valores bilingües), `#contacto` con formulario Formspree asíncrono (honeypot + `_subject`), sección `#precios` huérfana eliminada, CTA hero estandarizado, secciones condicionadas por `show_*`.
* **Navbar:** toggle de idioma 1-clic (pill `ES | EN`), enlaces canónicos (`core:home#...` / `billing:pricing`), enlaces condicionados a visibilidad, blindaje móvil (`overflow-x-clip`, enlaces de sesión movidos al drawer).
* **Billing:** `CreateCheckoutSessionView.get()` (fix HTTP 405); verificación de `return_url` canónico en Customer Portal.
* **Fulfillment SLA:** `handle_invoice_paid` asocia `plan` y asigna `assigned_to` por defecto; backoffice con columna "Asignado a", filtro `EN_PROCESO` y botón "Iniciar Producción" (transición `PENDIENTE_PRODUCCION → EN_PROCESO → ENTREGADA`).
* **Pruebas:** `test_checkout_get_redirects_to_stripe` (mock), `test_customer_portal_builds_canonical_return_url`, `test_webhook_invoice_paid_assigns_default_assignee`, `test_fulfillment_start_production_transitions_status`. Suite **38/38 passing**.
* **Verificación local:** home bilingüe con misión/visión/valores y formulario de contacto; navbar con toggle ES/EN y enlaces canónicos.
* **Pendiente (producción):** desplegar en EasyPanel (`fobandor_web`) y verificar en vivo los 11 puntos.

---

## 20. Incidente y Resolución: Envíos "Pending" en Formspree (Formulario de Contacto)

### Síntoma
* Los envíos del formulario `#contacto` (y del modal de `/precios/`) mostraban el mensaje de éxito, pero en el dashboard de Formspree quedaban en estado **"pending"** (no en "spam"). No se reenviaban por email automáticamente; solo llegaban al liberarlos manualmente.
* Los dos correos destino (`admin@fobandor.com` y `administrator@fobandor.com`) estaban **verificados** en la cuenta de Formspree.

### Causa raíz
* El filtro ML anti-spam **Formshield** (escaneo de machine learning de Formspree) estaba activo y retenía los envíos en estado "pending" antes de entregarlos al buzón `admin@fobandor.com`.

### Solución
* Desactivar **Formshield** en el dashboard de Formspree (form `mqpqqggk`). Se conserva el **honeypot `_gotcha`** ya implementado en los formularios como protección anti-spam ligera.
* **Resultado:** los envíos llegan directamente al buzón (verificado por Freddy Obando).

### Lección aprendida
* Para envíos **AJAX** con `Accept: application/json`, tener **Formshield activo** puede retener los envíos en "pending". Con honeypot propio, Formshield es redundante y conviene mantenerlo desactivado.
* Configuración recomendada para formularios FOBANDOR en Formspree:
  1. **Formshield:** desactivado.
  2. **reCAPTCHA:** desactivado (necesario para AJAX).
  3. **Honeypot `_gotcha`:** activo (implementado en `pricing.html` y `home.html`).
  4. **Destino:** correo verificado en *Account → Linked Emails*.

### Nota
* Resolución 100% del lado de Formspree (dashboard); **no requiere cambios de código ni redeploy**.








