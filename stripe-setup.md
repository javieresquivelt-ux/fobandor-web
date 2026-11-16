# Guía Paso a Paso: Configuración de Stripe (Test Mode y Producción)

> **Proyecto:** FOBANDOR (`www.fobandor.com`)  
> **Cliente / Emprendedor:** Freddy Obando (Orlando, Florida, EE.UU.)  
> **Propósito:** Configurar los 3 Planes de Acompañamiento en Stripe, obtener las claves API y configurar el Webhook para el motor de entregas con SLA de 7 días.

---

## 1. Resumen de la Arquitectura de Pagos de FOBANDOR

FOBANDOR utiliza una integración nativa de **Stripe Checkout en modo suscripción recurrente mensual** y **Webhooks firmados criptográficamente**:

1. **Catálogo Oficial de 3 Planes de Acompañamiento (Marketing Digital & Ventas):**
   * **Plan 1 • Impulso:** **$697.00 USD / mes** (Acompañamiento mínimo: 2 meses. Genera demanda con Meta Ads).
   * **Plan 2 • Conversión (Recomendado):** **$1,297.00 USD / mes** (Acompañamiento mínimo: 3 meses. Embudos, CRM, automatizaciones y citas).
   * **Plan 3 • Crecimiento:** **$1,997.00 USD / mes** (Acompañamiento mínimo: 3 meses. Recompra, fidelización, referidos y LTV).
2. **Ciclo de Entrega (SLA 7 Días):**  
   Cada vez que Stripe procesa exitosamente un cobro mensual (`invoice.paid`), el sistema crea o renueva automáticamente una orden de entrega (`FulfillmentOrder`) en la base de datos con una fecha límite de `paid_at + 7 días`.
3. **Gestión Dinámica en Backoffice CMS:**  
   Los precios, textos y códigos de Stripe **no están hardcodeados**. El administrador de FOBANDOR puede actualizar el `Stripe Price ID` o el precio en cualquier momento desde **`/backoffice/planes/`** sin necesidad de programadores ni despliegues.
4. **Seguridad y Privacidad (PCI-DSS):**  
   FOBANDOR nunca almacena números de tarjeta ni códigos CVV en sus servidores. Toda la pasarela opera delegada en Stripe.

---

## 2. Instrucciones para Freddy Obando (Dashboard de Stripe)

Freddy ya tiene creada su cuenta en Stripe y los 3 productos en el catálogo. Aquí están los pasos exactos para completar la vinculación:

### Paso 1: Activar "Test mode" (Modo de prueba)
1. Ingresa a tu panel de administración en:  
   👉 **[https://dashboard.stripe.com/](https://dashboard.stripe.com/)**
2. En la parte superior derecha, asegúrate de activar el interruptor que dice **"Test mode"** (Modo de prueba).
   * Verás que la barra de navegación muestra un banner naranja o la leyenda *"Viewing test data"*.

---

### Paso 2: Obtener el ID de Precio (`price_...`) de cada uno de los 3 Planes

En el menú lateral izquierdo, ve a **Product catalog** (Catálogo de productos) o visita:  
👉 **[https://dashboard.stripe.com/test/products](https://dashboard.stripe.com/test/products)**

Verás los 3 productos que ya creaste. Haz clic en cada uno de ellos para copiar su **Price ID**:

#### 1. Plan impulso ($697.00 USD/mes)
* Haz clic sobre el producto **Plan impulso**.
* En la sección **Pricing** (Precios), verás un código que empieza por `price_` (ejemplo: `price_1QxyzImpulso...`).
* 👉 **Copia y guarda ese ID de precio.**

#### 2. Plan Conversión ($1,297.00 USD/mes)
* Haz clic sobre el producto **Plan Conversión**.
* En la sección **Pricing**, copia el identificador que empieza por `price_` (ejemplo: `price_1QxyzConversion...`).
* 👉 **Copia y guarda ese ID de precio.**

#### 3. Plan Crecimiento ($1,997.00 USD/mes)
* Haz clic sobre el producto **Plan Crecimiento** *(si dice "Plan Crecimirnto", puedes corregir el nombre editando el producto)*.
* En la sección **Pricing**, copia el identificador que empieza por `price_` (ejemplo: `price_1QxyzCrecimiento...`).
* 👉 **Copia y guarda ese ID de precio.**

> ⚠️ **Nota Importante sobre Enlaces de Pago (`buy.stripe.com`):**  
> No es necesario crear Payment Links colectivos que sumen los 3 planes en una sola canasta ($3,993 USD). FOBANDOR genera automáticamente la sesión de pago individual para cada cliente según el plan que seleccione en la web. Solo necesitamos el código **`price_...`** de cada uno.

---

### Paso 3: Obtener las Claves de la API (API Keys en Modo Test)

1. En el menú lateral izquierdo, ve a **Developers** (Desarrolladores) > **API keys** (Claves de API) o visita:  
   👉 **[https://dashboard.stripe.com/test/apikeys](https://dashboard.stripe.com/test/apikeys)**
2. Asegúrate de seguir en **Test Mode**.
3. Copia:
   * **Publishable key (Clave publicable):** Comienza por `pk_test_...`
   * **Secret key (Clave secreta):** Haz clic en *"Reveal test key"* y copia la cadena que comienza por `sk_test_...`.

---

### Paso 4: Configurar el Webhook (Notificaciones de Cobro y Entrega)

1. En el menú lateral izquierdo, ve a **Developers** (Desarrolladores) > **Webhooks** o visita:  
   👉 **[https://dashboard.stripe.com/test/webhooks](https://dashboard.stripe.com/test/webhooks)**
2. Haz clic en el botón **"+ Add endpoint"** (+ Agregar extremo).
3. Completa los campos:
   * **Endpoint URL (URL del extremo):**  
     `https://www.fobandor.com/stripe/webhook/`  
     *(Para pruebas locales en desarrollo con Stripe CLI, se utiliza el comando `stripe listen` como se detalla en la sección 5).*
   * **Select events to listen to (Eventos para escuchar):** Haz clic en **"+ Select events"** y marca exactamente estos 4 eventos:
     * `checkout.session.completed` (Cuando el cliente completa el pago inicial).
     * `invoice.paid` (Cuando el pago mensual se aprueba; crea/renueva la orden de 7 días).
     * `customer.subscription.deleted` (Cuando el cliente cancela su suscripción).
     * `customer.subscription.updated` (Cuando se renueva o actualiza el estado).
4. Haz clic en **"Add endpoint"** (Agregar extremo).
5. En la página de detalles del webhook recién creado, busca la sección **Signing secret** (Secreto de firma).
6. Haz clic en **"Reveal"** (Revelar) y copia el valor (comienza por `whsec_...`).

---

## 3. Resumen de los 6 Datos que Freddy debe entregarte

| Dato Solicitado | Prefijo / Formato | Ejemplo |
| :--- | :--- | :--- |
| **Clave Publicable** | `pk_test_...` | `pk_test_51Pxyz...` |
| **Clave Secreta** | `sk_test_...` | `sk_test_51Pxyz...` |
| **Secreto de Webhook** | `whsec_...` | `whsec_abc123...` |
| **ID Precio Plan Impulso ($697)** | `price_...` | `price_1QxyzImpulso...` |
| **ID Precio Plan Conversión ($1,297)** | `price_...` | `price_1QxyzConversion...` |
| **ID Precio Plan Crecimiento ($1,997)** | `price_...` | `price_1QxyzCrecimiento...` |

---

## 4. Dónde cargar estos datos en la Plataforma FOBANDOR

### Opción A: A través del Backoffice Web (La forma más fácil y recomendada)
1. Inicia sesión en el Backoffice con tu cuenta staff:  
   👉 **`http://localhost:8000/es/backoffice/planes/`**
2. Verás la lista con los 3 Planes de Acompañamiento (**Plan 1 • Impulso**, **Plan 2 • Conversión**, **Plan 3 • Crecimiento**).
3. Haz clic en **"Editar"** en cada plan:
   * Pega el código correspondiente en el campo **`Stripe Price ID`** (`price_...`).
   * Guarda los cambios.
4. **¡Listo!** El catálogo público `/precios/` y el botón de checkout quedarán conectados inmediatamente a Stripe sin tocar ningún archivo ni reiniciar el servidor.

---

### Opción B: Cargar las Claves API en el archivo `.env`
Las 3 claves de conexión del sistema con Stripe se guardan en el archivo [`.env`](file:///home/jet/proyectos_lnx/proyectos/fobandor/.env) en la raíz del proyecto (líneas 8 a 11):

```env
# Stripe API Keys (Modo Test en desarrollo)
STRIPE_PUBLIC_KEY=pk_test_TU_CLAVE_PUBLICABLE_REAL
STRIPE_SECRET_KEY=sk_test_TU_CLAVE_SECRETA_REAL
STRIPE_WEBHOOK_SECRET=whsec_TU_SECRETO_DE_WEBHOOK_REAL
```

> **Reglas:** Sin comillas, sin espacios antes o después del signo `=`, en una sola línea.

---

### Opción C: Actualizar el Seeder de Base de Datos (Opcional para desarrollo)
Si deseas que los Price IDs queden guardados por defecto en el comando de inicialización, puedes pegarlos en:  
[`fobandor/billing/management/commands/seed_subscription_plans.py`](file:///home/jet/proyectos_lnx/proyectos/fobandor/fobandor/billing/management/commands/seed_subscription_plans.py)

En la lista `PLANS`:
```python
PLANS = [
    {
        'slug': 'impulso',
        'stripe_price_id': 'price_TU_ID_REAL_IMPULSO',  # <--- Aquí
        ...
    },
    {
        'slug': 'conversion',
        'stripe_price_id': 'price_TU_ID_REAL_CONVERSION', # <--- Aquí
        ...
    },
    {
        'slug': 'crecimiento',
        'stripe_price_id': 'price_TU_ID_REAL_CRECIMIENTO', # <--- Aquí
        ...
    },
]
```

Y luego ejecutar:
```bash
python manage.py seed_subscription_plans
```

---

## 5. Cómo probar Webhooks de Stripe en Localhost (Desarrollo)

Para recibir y probar los webhooks de Stripe directamente en tu máquina local (`localhost:8000`), utiliza la herramienta oficial **Stripe CLI**:

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
4. **Disparar un cobro mensual de prueba:**
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
3. Entra a `/backoffice/planes/` y pega los nuevos `price_live_...` directamente desde la web, o actualiza el `.env` del VPS con las claves `live`.
4. ¡El sistema estará cobrando en dólares reales con SLA automático de 7 días!

---

© 2026 FOBANDOR. Guía técnica de integración de pagos Stripe.
