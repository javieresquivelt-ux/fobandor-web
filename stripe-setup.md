# Guía Paso a Paso: Configuración de Stripe (Test Mode y Producción)

> **Proyecto:** FOBANDOR (`www.fobandor.com`)  
> **Cliente / Emprendedor:** Freddy Obando (Orlando, Florida, EE.UU.)  
> **Propósito:** Configurar los 3 productos de suscripción mensual en Stripe, obtener las claves API y configurar el Webhook para el motor de entregas con SLA de 7 días.

---

## 1. Resumen de la Arquitectura de Pagos de FOBANDOR

FOBANDOR utiliza una integración nativa de **Stripe Checkout en modo suscripción recurrente** y **Webhooks firmados criptográficamente**:

1. **Catálogo de 3 Planes Mensuales:**
   * **Starter:** $199.00 USD / mes (Desarrollo Web & Contenido base).
   * **Pro:** $499.00 USD / mes (Web + Apps + Publicidad IA mensual).
   * **Enterprise:** $999.00 USD / mes (Solución integral + Fobandor Studios).
2. **Ciclo de Entrega (SLA 7 Días):**  
   Cada vez que Stripe procesa exitosamente un cobro mensual (`invoice.paid`), el sistema crea o renueva automáticamente una orden de entrega (`FulfillmentOrder`) en la base de datos con una fecha límite de `paid_at + 7 días`.
3. **Seguridad y Privacidad (PCI-DSS):**  
   FOBANDOR nunca almacena datos de tarjetas ni CVVs en sus servidores. Toda la información financiera vive exclusivamente en la infraestructura de Stripe.

---

## 2. Instrucciones para Freddy Obando (Dashboard de Stripe)

Puedes compartir estas instrucciones directamente con Freddy Obando para que configure su cuenta de Stripe:

### Paso 1: Iniciar Sesión y Activar "Test Mode"
1. Ingresa a tu panel de administración en:  
   👉 **[https://dashboard.stripe.com/](https://dashboard.stripe.com/)**
2. En la parte superior derecha de la pantalla, activa el interruptor que dice **"Test mode"** (Modo de prueba).
   * Verás que la barra de navegación muestra un banner naranja o la leyenda *"Viewing test data"*. Todo lo que hagas aquí es simulado y no genera cobros reales.

---

### Paso 2: Crear los 3 Planes de Suscripción en el Catálogo

En el menú lateral izquierdo, haz clic en **Catálogo de productos** (Product catalog) o ve a:  
👉 **[https://dashboard.stripe.com/test/products](https://dashboard.stripe.com/test/products)**

Crea los siguientes 3 productos:

#### Producto 1: Plan Starter
* Haz clic en **"+ Agregar producto"** (+ Add product).
* **Nombre:** `Plan Starter`
* **Descripción:** `Desarrollo Web y Publicidad Base con Inteligencia Artificial.`
* En la sección **Información de precios**:
  * **Modelo de precios:** *Estándar* (Standard pricing).
  * **Precio:** `199.00`
  * **Moneda:** `USD - Dólar estadounidense`.
  * **Facturación:** Selecciona **Recurrente** (Recurring).
  * **Período de facturación:** **Mensual** (Monthly).
* Haz clic en **"Guardar producto"**.
* En la pantalla del producto guardado, busca la sección **Precios**. Verás un identificador que comienza con `price_` (ejemplo: `price_1QxyzStarter123456789`).  
  👉 **Copia y guarda ese ID de precio.**

#### Producto 2: Plan Pro
* Haz clic en **"+ Agregar producto"**.
* **Nombre:** `Plan Pro`
* **Descripción:** `Solución completa de Web, Apps y Campañas Publicitarias con IA.`
* En **Información de precios**:
  * **Precio:** `499.00` `USD`.
  * **Facturación:** **Recurrente** / **Mensual**.
* Haz clic en **"Guardar producto"**.
* 👉 **Copia y guarda el ID de precio (`price_...`).**

#### Producto 3: Plan Enterprise
* Haz clic en **"+ Agregar producto"**.
* **Nombre:** `Plan Enterprise`
* **Descripción:** `Solución integral Full Stack con Producción Audiovisual Fobandor Studios.`
* En **Información de precios**:
  * **Precio:** `999.00` `USD`.
  * **Facturación:** **Recurrente** / **Mensual**.
* Haz clic en **"Guardar producto"**.
* 👉 **Copia y guarda el ID de precio (`price_...`).**

---

### Paso 3: Obtener las Claves de la API (API Keys)

1. En el menú lateral izquierdo, ve a **Desarrolladores** (Developers) > **Claves de API** (API keys) o visita:  
   👉 **[https://dashboard.stripe.com/test/apikeys](https://dashboard.stripe.com/test/apikeys)**
2. Asegúrate de seguir en **Test Mode**.
3. Localiza y copia:
   * **Clave publicable (Publishable key):** Comienza por `pk_test_...`
   * **Clave secreta (Secret key):** Haz clic en *"Revelar clave de prueba"* y copia la cadena que comienza por `sk_test_...`.

---

### Paso 4: Configurar el Webhook (Notificaciones de Pago)

1. En el menú lateral izquierdo, ve a **Desarrolladores** (Developers) > **Webhooks** o visita:  
   👉 **[https://dashboard.stripe.com/test/webhooks](https://dashboard.stripe.com/test/webhooks)**
2. Haz clic en el botón **"+ Agregar extremo"** (+ Add endpoint).
3. Completa los campos:
   * **URL del extremo:**  
     `https://www.fobandor.com/stripe/webhook/`  
     *(Para pruebas locales en desarrollo con Stripe CLI o ngrok, se utiliza la URL local o el comando `stripe listen`).*
   * **Versión:** Déjala en la versión recomendada por defecto de Stripe.
   * **Eventos para escuchar:** Haz clic en **"+ Seleccionar eventos"** y marca exactamente estos 4 eventos:
     * `checkout.session.completed` (Cuando el cliente completa la pantalla de pago).
     * `invoice.paid` (Cuando el pago mensual se aprueba; crea/renueva la orden de 7 días).
     * `customer.subscription.deleted` (Cuando el cliente cancela su suscripción).
     * `customer.subscription.updated` (Cuando se renueva o actualiza el estado).
4. Haz clic en **"Agregar extremo"**.
5. En la página de detalles del webhook recién creado, busca la sección **Secreto de firma** (Signing secret).
6. Haz clic en **"Revelar"** y copia el valor (comienza por `whsec_...`).

---

## 3. Resumen de los 6 Datos que Freddy debe entregarte

Para dejar FOBANDOR 100% conectado, Freddy debe entregarte esta lista:

| Variable | Formato / Prefijo | Ejemplo |
| :--- | :--- | :--- |
| **Clave Publicable** | `pk_test_...` | `pk_test_51Pxyz...` |
| **Clave Secreta** | `sk_test_...` | `sk_test_51Pxyz...` |
| **Secreto Webhook** | `whsec_...` | `whsec_abc123...` |
| **ID Precio Starter ($199)** | `price_...` | `price_1QxyzStarter...` |
| **ID Precio Pro ($499)** | `price_...` | `price_1QxyzPro...` |
| **ID Precio Enterprise ($999)** | `price_...` | `price_1QxyzEnterprise...` |

---

## 4. Dónde pegar estos datos en el Proyecto FOBANDOR

### A. Las 3 Claves API en el archivo `.env`
Abre el archivo [`.env`](file:///home/jet/proyectos_lnx/proyectos/fobandor/.env) en la raíz del proyecto. En las **líneas 8 a 11**, reemplaza los valores de prueba:

```env
# Stripe API Keys (Modo Test en desarrollo)
STRIPE_PUBLIC_KEY=pk_test_TU_CLAVE_PUBLICABLE_REAL
STRIPE_SECRET_KEY=sk_test_TU_CLAVE_SECRETA_REAL
STRIPE_WEBHOOK_SECRET=whsec_TU_SECRETO_DE_WEBHOOK_REAL
```

> **Reglas:** Sin comillas, sin espacios antes o después del `=`, todo en una sola línea.

---

### B. Los 3 IDs de Precio en el archivo de seed de Django
Abre el archivo:  
[`fobandor/billing/management/commands/seed_subscription_plans.py`](file:///home/jet/proyectos_lnx/proyectos/fobandor/fobandor/billing/management/commands/seed_subscription_plans.py)

En la lista `PLANS`, reemplaza los valores de `stripe_price_id`:

```python
PLANS = [
    {
        'slug': 'starter',
        'name_es': 'Starter',
        'name_en': 'Starter',
        'price_usd': Decimal('199.00'),
        'stripe_price_id': 'price_TU_ID_REAL_STARTER',  # <--- Reemplazar aquí
        'order_type': 'WEB_DEV',
        'order': 1,
        'is_active': True,
        'is_highlighted': False,
        ...
    },
    {
        'slug': 'pro',
        'name_es': 'Pro',
        'name_en': 'Pro',
        'price_usd': Decimal('499.00'),
        'stripe_price_id': 'price_TU_ID_REAL_PRO',      # <--- Reemplazar aquí
        'order_type': 'APP_DEV',
        'order': 2,
        'is_active': True,
        'is_highlighted': True,
        ...
    },
    {
        'slug': 'enterprise',
        'name_es': 'Enterprise',
        'name_en': 'Enterprise',
        'price_usd': Decimal('999.00'),
        'stripe_price_id': 'price_TU_ID_REAL_ENTERPRISE', # <--- Reemplazar aquí
        'order_type': 'STUDIOS',
        'order': 3,
        'is_active': True,
        'is_highlighted': False,
        ...
    },
]
```

---

### C. Aplicar la actualización en la Base de Datos
Una vez guardados los cambios en `seed_subscription_plans.py`, ejecuta este comando en tu terminal para actualizar la base de datos PostgreSQL:

```bash
source .venv/bin/activate
python manage.py seed_subscription_plans
```

Verás el mensaje de confirmación actualizando los planes con sus IDs oficiales de Stripe.

---

## 5. Cómo probar Webhooks de Stripe en Localhost (Desarrollo)

Para recibir y probar los webhooks de Stripe directamente en tu máquina local (`localhost:8000`), puedes usar la herramienta oficial **Stripe CLI**:

1. **Instalar Stripe CLI en Ubuntu:**
   ```bash
   curl -s https://packages.stripe.dev/api/security/keypair/stripe-cli-gpg/public | gpg --dearmor | sudo tee /usr/share/keyrings/stripe.gpg
   echo "deb [signed-by=/usr/share/keyrings/stripe.gpg] https://packages.stripe.dev/stripe-cli-debian-local stable main" | sudo tee /etc/apt/sources.list.d/stripe.list
   sudo apt update
   sudo apt install stripe
   ```
2. **Iniciar sesión con tu cuenta de Stripe:**
   ```bash
   stripe login
   ```
3. **Escuchar y reenviar eventos hacia tu servidor local:**
   ```bash
   stripe listen --forward-to localhost:8000/stripe/webhook/
   ```
   * Stripe CLI te imprimirá un secreto local: `Your webhook signing secret is whsec_12345...`
   * Si estás probando con el CLI, coloca temporalmente ese `whsec_...` en tu `.env` como `STRIPE_WEBHOOK_SECRET`.
4. **Disparar un cobro de prueba automático:**
   ```bash
   stripe trigger invoice.paid
   ```
   * Verás en la consola de Django la creación automática de una nueva `FulfillmentOrder` con fecha límite de 7 días.

---

## 6. Paso a Producción (Live Mode)

Cuando el sitio esté en el VPS en `https://www.fobandor.com/` y listo para recibir pagos reales:

1. Entra a Stripe y desactiva el switch **"Test mode"** (pasando a Live Mode).
2. Repite los mismos pasos:
   * Crea los 3 productos en el catálogo de producción (obtendrás nuevos `price_live_...`).
   * Copia las claves de producción (`pk_live_...` y `sk_live_...`).
   * Configura el webhook de producción con la URL `https://www.fobandor.com/stripe/webhook/` y obtén su `whsec_live_...`.
3. Actualiza el `.env` del servidor VPS con esas claves de producción.
4. ¡El sistema estará cobrando en dólares reales con SLA automático de 7 días!

---

© 2026 FOBANDOR. Guía técnica de integración de pagos Stripe.
