import stripe
from django.conf import settings
from django.utils import timezone

from fobandor.users.models import User

stripe.api_key = settings.STRIPE_SECRET_KEY


def get_or_create_stripe_customer(user):
    """Devuelve el stripe_customer_id del usuario, creándolo si no existe."""
    if user.stripe_customer_id:
        return user.stripe_customer_id
    customer = stripe.Customer.create(
        email=user.email,
        name=user.get_full_name() or user.email,
        metadata={"user_id": str(user.pk)},
    )
    user.stripe_customer_id = customer["id"]
    user.save(update_fields=["stripe_customer_id"])
    return customer["id"]


def create_checkout_session(user, plan, success_url, cancel_url):
    """Crea una sesión de Stripe Checkout en modo suscripción."""
    customer_id = get_or_create_stripe_customer(user)
    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
        allow_promotion_codes=True,
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(user.pk),
        metadata={"user_id": str(user.pk), "plan_id": str(plan.pk)},
        subscription_data={
            "metadata": {"user_id": str(user.pk), "plan_id": str(plan.pk)},
        },
    )
    return session


def create_customer_portal_session(user, return_url):
    """Crea una sesión del Stripe Customer Portal para autogestión."""
    customer_id = get_or_create_stripe_customer(user)
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )
    return session


def handle_checkout_completed(session):
    """Activa la suscripción, vincula stripe_customer_id y retroalimenta órdenes huérfanas."""
    from fobandor.billing.models import CustomerSubscription, SubscriptionPlan
    from fobandor.fulfillment.models import FulfillmentOrder

    customer_id = session.get("customer")
    subscription_id = session.get("subscription")
    user = User.objects.filter(stripe_customer_id=customer_id).first()
    if user is None:
        return

    plan = None
    plan_id = (session.get("metadata") or {}).get("plan_id")
    if plan_id:
        plan = SubscriptionPlan.objects.filter(pk=plan_id).first()

    subscription, _ = CustomerSubscription.objects.update_or_create(
        stripe_subscription_id=subscription_id,
        defaults={
            "user": user,
            "plan": plan,
            "status": "active",
        },
    )

    # Retroalimentación bidireccional: rellena órdenes huérfanas del usuario.
    if plan is not None:
        FulfillmentOrder.objects.filter(user=user, plan__isnull=True).update(
            plan=plan,
            subscription=subscription,
            order_type=plan.order_type,
        )


def _coerce_price_id(price):
    if isinstance(price, dict):
        return price.get("id")
    return price


def _price_id_from_lines(lines):
    data = (lines or {}).get("data") or []
    if data:
        return _coerce_price_id(data[0].get("price"))
    return None


def _extract_price_id_from_invoice(invoice):
    """Obtiene el price_id desde las líneas de la factura (payload o vía API)."""
    price_id = _price_id_from_lines(invoice.get("lines"))
    if price_id:
        return price_id
    invoice_id = invoice.get("id")
    if not invoice_id or not settings.STRIPE_SECRET_KEY:
        return None
    try:
        full = stripe.Invoice.retrieve(invoice_id, expand=["lines.data.price"])
    except Exception:
        return None
    return _price_id_from_lines(full.get("lines"))


def _extract_price_id_from_subscription(subscription_id):
    if not subscription_id or not settings.STRIPE_SECRET_KEY:
        return None
    try:
        sub = stripe.Subscription.retrieve(subscription_id, expand=["items.data.price"])
    except Exception:
        return None
    items = (sub.get("items") or {}).get("data") or []
    if items:
        return _coerce_price_id(items[0].get("price"))
    return None


def _resolve_plan_from_stripe(invoice, subscription_id):
    from fobandor.billing.models import SubscriptionPlan

    price_id = _extract_price_id_from_invoice(invoice)
    if not price_id:
        price_id = _extract_price_id_from_subscription(subscription_id)
    if price_id:
        return SubscriptionPlan.objects.filter(stripe_price_id=price_id).first()
    return None


def handle_invoice_paid(invoice):
    """Registra la factura y crea/renueva la FulfillmentOrder (fuente única de órdenes)."""
    from fobandor.billing.models import BillingInvoice, CustomerSubscription
    from fobandor.fulfillment.models import FulfillmentOrder

    invoice_id = invoice.get("id")
    customer_id = invoice.get("customer")
    subscription_id = invoice.get("subscription")

    user = User.objects.filter(stripe_customer_id=customer_id).first()
    if user is None or not invoice_id:
        return

    subscription = None
    plan = None
    if subscription_id:
        subscription = CustomerSubscription.objects.filter(
            stripe_subscription_id=subscription_id).first()
        if subscription and subscription.plan:
            plan = subscription.plan

    # Resolución multi-fuente inmune a la carrera de webhooks.
    if plan is None:
        plan = _resolve_plan_from_stripe(invoice, subscription_id)

    if plan is not None and subscription_id:
        subscription, _ = CustomerSubscription.objects.update_or_create(
            stripe_subscription_id=subscription_id,
            defaults={"user": user, "plan": plan, "status": "active"},
        )

    amount_paid = invoice.get("amount_paid", 0) or 0
    BillingInvoice.objects.get_or_create(
        stripe_invoice_id=invoice_id,
        defaults={
            "user": user,
            "amount_paid": amount_paid / 100,
            "currency": (invoice.get("currency") or "usd").upper(),
            "paid_at": timezone.now(),
            "invoice_pdf_url": invoice.get("invoice_pdf") or "",
        },
    )

    order_type = plan.order_type if plan else "WEB_DEV"
    assignee = None
    default_email = getattr(settings, "DEFAULT_ASSIGNEE_EMAIL", "for@fobandor.com")
    if default_email:
        assignee = User.objects.filter(email=default_email).first()
    FulfillmentOrder.objects.get_or_create(
        stripe_invoice_id=invoice_id,
        defaults={
            "user": user,
            "subscription": subscription,
            "plan": plan,
            "assigned_to": assignee,
            "order_type": order_type,
            "paid_at": timezone.now(),
            "status": "PENDIENTE_PRODUCCION",
        },
    )


def handle_subscription_deleted(subscription_obj):
    """Marca la suscripción local como cancelada."""
    from fobandor.billing.models import CustomerSubscription

    subscription_id = subscription_obj.get("id")
    CustomerSubscription.objects.filter(stripe_subscription_id=subscription_id).update(
        status="canceled")


def process_webhook_event(event):
    """Despacha el evento de Stripe al manejador correspondiente."""
    handlers = {
        "checkout.session.completed": handle_checkout_completed,
        "invoice.paid": handle_invoice_paid,
        "customer.subscription.deleted": handle_subscription_deleted,
    }
    handler = handlers.get(event.get("type"))
    if handler:
        handler(event.get("data", {}).get("object", {}))
