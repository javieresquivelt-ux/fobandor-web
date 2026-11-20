---
name: stripe-integration
description: >-
  Guía de integración con Stripe para suscripciones recurrentes, Checkout Session,
  Webhooks firmados y Customer Portal. Incluye todas las lecciones críticas aprendidas
  en FOBANDOR: condición de carrera invoice.paid vs checkout.session.completed,
  compatibilidad con la API moderna de Stripe (StripeObject), tax_code requerido,
  diferencia entre prod_ y price_, y estrategia de Test Mode en producción.
  Usar cuando se implementa o debuggea la pasarela de pagos.
---

# Stripe Integration — Lecciones Críticas FOBANDOR

## Arquitectura Validada

```
Usuario → /precios/ → POST /checkout/{slug}/ → stripe.checkout.Session.create()
       → Stripe Checkout ← → /stripe/webhook/ (Firmado criptográfico)
       → invoice.paid + checkout.session.completed → FulfillmentOrder + Email
       → Cliente → /mi-cuenta/ → POST /billing/portal/ → Stripe Customer Portal
```

---

## Lecciones Críticas (Incidentes Reales en Producción)

### CRÍTICO 1: `prod_` ≠ `price_` — IDs de Stripe

> [!CAUTION]
> En Stripe, `prod_...` es el **Producto** comercial. `price_...` es la **Tarifa/Precio** recurrente.
> La API de Checkout Session requiere **siempre** `price_...`.

```python
# INCORRECTO ❌
stripe.checkout.Session.create(line_items=[{'price': 'prod_VeI9...'}])

# CORRECTO ✅
stripe.checkout.Session.create(line_items=[{'price': 'price_1UczZN...'}])
```

**Verificación:** En el Backoffice de Planes, el campo `stripe_price_id` debe contener el ID que comienza con `price_`, no `prod_`.

---

### CRÍTICO 2: `tax_code` Requerido por Stripe Managed Payments

> [!WARNING]
> Si la cuenta Stripe tiene Managed Payments habilitado (default), la creación de sesiones
> falla con: `Invalid line_items[0]: the product tax code is missing.`

**Solución:** Asignar `tax_code="txcd_10000000"` (Software/SaaS Services) a cada producto en Stripe.

```python
stripe.Product.modify(
    product_id,
    tax_code="txcd_10000000"
)
```

---

### CRÍTICO 3: Condición de Carrera `invoice.paid` vs `checkout.session.completed`

> [!IMPORTANT]
> Stripe despacha ambos eventos **concurrentemente**. `invoice.paid` llega antes que
> `checkout.session.completed` cree la `CustomerSubscription` en BD. El resultado:
> `FulfillmentOrder` creada sin `plan` vinculado (`plan = None`).

**Estrategia de Resiliencia Multi-Fuente validada:**

```python
def handle_invoice_paid(invoice_id, stripe_invoice):
    # 1. Resolver precio directamente desde líneas de factura (sin depender de CS)
    price_id = _extract_price_id_from_invoice(stripe_invoice)

    # 2. Si no hay precio en las líneas, consultar la suscripción en Stripe
    if not price_id and stripe_invoice.get('subscription'):
        price_id = _extract_price_id_from_subscription(stripe_invoice['subscription'])

    plan = SubscriptionPlan.objects.filter(stripe_price_id=price_id).first()

    # 3. Si la suscripción no existe en BD, crearla proactivamente (idempotente)
    if stripe_invoice.get('subscription'):
        subscription, _ = CustomerSubscription.objects.update_or_create(
            stripe_subscription_id=stripe_invoice['subscription'],
            defaults={'user': user, 'plan': plan, 'status': 'active'}
        )
```

**Salvaguarda bidireccional en `handle_checkout_completed`:**
```python
def handle_checkout_completed(session):
    # Retroalimentar órdenes huérfanas del mismo usuario
    FulfillmentOrder.objects.filter(
        user=user, plan__isnull=True
    ).update(plan=plan, subscription=subscription)
```

**Management command de reconciliación (en `entrypoint.sh`):**
```bash
python manage.py reconcile_fulfillment_orders || true
```

---

### CRÍTICO 4: API Moderna de Stripe — StripeObject no es dict

> [!CAUTION]
> En `stripe-python >= 11`, los objetos Stripe son `StripeObject`, NO diccionarios.
> Usar `.get()` directamente lanza `AttributeError`.

```python
# ERROR en stripe-python v11+ ❌
invoice.get('lines')  # AttributeError: use .to_dict()

# CORRECTO — Acceso jerárquico robusto ✅
def _extract_price_id_from_invoice(invoice):
    lines = invoice.get('lines') if isinstance(invoice, dict) else invoice.to_dict().get('lines', {})
    for item in lines.get('data', []):
        # Soporte para API 2024/2025/2026 (estructura jerárquica)
        price_id = (
            item.get('pricing', {}).get('price_details', {}).get('price')  # Nuevo ✅
            or item.get('price') if isinstance(item.get('price'), str) else None  # Legado
            or (item.get('price') or {}).get('id')  # Objeto precio expandido
        )
        if price_id:
            return price_id
    return None
```

---

### CRÍTICO 5: Error 405 en Checkout Post-Login

> [!IMPORTANT]
> Django redirige al `?next=` via GET tras el login OAuth, pero la vista de Checkout
> solo aceptaba POST. Resultado: HTTP 405 Method Not Allowed.

```python
class CreateCheckoutSessionView(LoginRequiredMixin, EmailVerifiedRequiredMixin, View):
    def post(self, request, slug):
        return self._handle(request, slug)

    def get(self, request, slug):
        """Permite que la redirección post-login (GET) también cree la sesión."""
        return self._handle(request, slug)

    def _handle(self, request, slug):
        plan = get_object_or_404(SubscriptionPlan, slug=slug, is_active=True)
        checkout_url = services.create_checkout_session(request, plan)
        return redirect(checkout_url)
```

---

## Webhooks Firmados: Implementación Segura

```python
# billing/views.py
class StripeWebhookView(View):
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except stripe.SignatureVerificationError:  # ← top-level en stripe v11+
            return HttpResponse(status=400)

        # Envolver en try/except para nunca retornar 500 a Stripe
        try:
            if event['type'] == 'invoice.paid':
                services.handle_invoice_paid(event['data']['object'])
            elif event['type'] == 'checkout.session.completed':
                services.handle_checkout_completed(event['data']['object'])
        except Exception:
            logger.exception("Error procesando webhook %s", event['type'])
            # Retornar 200 igualmente para evitar reintentos de Stripe ante errores internos
            return HttpResponse(status=200)

        return HttpResponse(status=200)
```

> [!WARNING]
> `stripe.error` ya no es importable en stripe v17+.
> Usar `stripe.SignatureVerificationError` directamente (top-level).

---

## Estrategia Test Mode en Producción

**Protocolo validado:**
1. Desplegar con claves `pk_test_` / `sk_test_` en el dominio productivo real.
2. Registrar el webhook en Stripe Workbench apuntando al dominio HTTPS real (no ngrok).
3. Validar el flujo E2E completo con tarjetas de prueba (`4242 4242 4242 4242`).
4. Transición a Live Mode: solo cambiar variables de entorno en EasyPanel + actualizar `stripe_price_id` en Backoffice.

---

## Variables de Entorno Requeridas

```bash
STRIPE_PUBLIC_KEY=pk_test_...     # o pk_live_...
STRIPE_SECRET_KEY=sk_test_...     # o sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...   # Generado en Stripe Workbench
```

---

## Checklist de Integración Stripe

- [ ] Verificar que `stripe_price_id` en BD comienza con `price_`, no `prod_`.
- [ ] Asignar `tax_code="txcd_10000000"` a todos los productos.
- [ ] Implementar `get()` en `CreateCheckoutSessionView` para manejar redirect post-login.
- [ ] Usar extracción jerárquica de `price_id` desde `pricing.price_details.price`.
- [ ] Envolver handlers en `try/except` con `logger.exception()`.
- [ ] Usar `stripe.SignatureVerificationError` (top-level), no `stripe.error.*`.
- [ ] Implementar `reconcile_fulfillment_orders` y agregar a `entrypoint.sh`.
- [ ] Configurar `metadata` en la suscripción: `{"user_id": ..., "plan_id": ...}`.

## Referencias

- [memory.md §23 — Condición de carrera Webhooks](../../memory.md)
- [memory.md §26 — Crash API Moderna Stripe](../../memory.md)
- [billing/services.py](../../fobandor/billing/services.py)
