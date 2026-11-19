import datetime
import logging
from zoneinfo import ZoneInfo

import stripe
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from fobandor.users.models import User

logger = logging.getLogger(__name__)

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
    order, _ = FulfillmentOrder.objects.get_or_create(
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

    # Notificaciones transaccionales por correo (Etapa 9: Cliente y Equipo Interno)
    send_customer_purchase_email(user, invoice, plan, order)
    send_internal_purchase_alert(user, invoice, plan, order)


def send_customer_purchase_email(user, invoice_data, plan, order):
    """Envía al cliente el correo transaccional con resumen de compra y enlace a la factura oficial en PDF."""
    try:
        recipient = getattr(user, "email", None)
        if not recipient:
            return

        client_name = user.get_full_name() or user.email
        plan_name = plan.name_es if plan else "Plan FOBANDOR"
        service_name = order.get_order_type_display() if order else "Acompañamiento"
        amount_paid_raw = invoice_data.get("amount_paid", 0) or 0
        amount_paid = f"{amount_paid_raw / 100:.2f}"
        currency = (invoice_data.get("currency") or "usd").upper()
        invoice_pdf_url = invoice_data.get("invoice_pdf") or ""
        hosted_invoice_url = invoice_data.get("hosted_invoice_url") or ""

        site_domain = getattr(settings, "SITE_DOMAIN", "https://fobandor.com")
        if not site_domain.startswith("http"):
            site_domain = f"https://{site_domain}"
        portal_url = f"{site_domain.rstrip('/')}/es/portal/dashboard/"
        support_email = "admin@fobandor.com"

        context = {
            "client_name": client_name,
            "plan_name": plan_name,
            "service_name": service_name,
            "amount_paid": amount_paid,
            "currency": currency,
            "invoice_pdf_url": invoice_pdf_url,
            "hosted_invoice_url": hosted_invoice_url,
            "portal_url": portal_url,
            "support_email": support_email,
        }

        subject = "¡Gracias por tu compra! Tu factura y detalles del servicio — FOBANDOR"
        html_content = render_to_string("billing/email/customer_purchase_invoice.html", context)
        text_content = render_to_string("billing/email/customer_purchase_invoice.txt", context)

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "FOBANDOR <admin@fobandor.com>")
        msg = EmailMultiAlternatives(subject, text_content, from_email, [recipient])
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info(
            "Correo de confirmación de compra enviado al cliente %s (Factura: %s)",
            recipient,
            invoice_data.get("id"),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Fallo al enviar correo de compra al cliente %s — %s: %s",
            getattr(user, "email", "desconocido"),
            type(exc).__name__,
            exc,
        )


def send_internal_purchase_alert(user, invoice_data, plan, order):
    """Envía alerta de nueva compra al equipo interno (Staff + Grupo Content_Editors)."""
    try:
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()

        staff_emails = list(
            UserModel.objects.filter(is_staff=True).exclude(email="").values_list("email", flat=True)
        )
        editors_emails = list(
            UserModel.objects.filter(groups__name="Content_Editors").exclude(email="").values_list("email", flat=True)
        )
        recipients = sorted(list(set(filter(None, staff_emails + editors_emails))))

        if not recipients:
            logger.warning("No hay destinatarios internos (staff/Content_Editors) para alerta de compra.")
            return

        tz_ny = ZoneInfo("America/New_York")
        created_ts = invoice_data.get("created")
        if created_ts:
            dt_ny = datetime.datetime.fromtimestamp(created_ts, tz=datetime.timezone.utc).astimezone(tz_ny)
        elif order and order.paid_at:
            dt_ny = order.paid_at.astimezone(tz_ny)
        else:
            dt_ny = timezone.now().astimezone(tz_ny)
        fecha_hora_str = dt_ny.strftime("%Y-%m-%d %H:%M %Z")

        client_email = getattr(user, "email", "") or invoice_data.get("customer_email") or "Cliente"
        client_name = user.get_full_name() or client_email
        plan_name = plan.name_es if plan else "Plan"
        service_name = order.get_order_type_display() if order else "Servicio"
        servicio_y_plan = f"{service_name} ({plan_name})" if plan else service_name

        subject = f"Nueva compra de servicios - {fecha_hora_str} - {client_email} - {servicio_y_plan}"

        amount_paid_raw = invoice_data.get("amount_paid", 0) or 0
        amount_paid = f"{amount_paid_raw / 100:.2f}"
        currency = (invoice_data.get("currency") or "usd").upper()

        backoffice_url = "https://fobandor.com/en/backoffice/entregas/"
        due_date_str = (
            order.due_date.astimezone(tz_ny).strftime("%Y-%m-%d %H:%M %Z")
            if (order and order.due_date)
            else "SLA 7 días"
        )
        assignee_str = order.assigned_to.email if (order and order.assigned_to) else "Pendiente de asignación"

        context = {
            "fecha_hora": fecha_hora_str,
            "client_name": client_name,
            "client_email": client_email,
            "plan_name": plan_name,
            "service_name": service_name,
            "amount_paid": amount_paid,
            "currency": currency,
            "status_display": order.get_status_display() if order else "Pendiente de Producción",
            "due_date": due_date_str,
            "assignee": assignee_str,
            "backoffice_url": backoffice_url,
            "invoice_id": invoice_data.get("id", ""),
            "invoice_pdf_url": invoice_data.get("invoice_pdf") or "",
        }

        html_content = render_to_string("billing/email/internal_purchase_alert.html", context)
        text_content = render_to_string("billing/email/internal_purchase_alert.txt", context)

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "FOBANDOR <admin@fobandor.com>")
        msg = EmailMultiAlternatives(subject, text_content, from_email, recipients)
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info("Alerta interna de compra enviada a %d destinatarios: %s", len(recipients), recipients)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Fallo al enviar alerta interna de compra — %s: %s",
            type(exc).__name__,
            exc,
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
