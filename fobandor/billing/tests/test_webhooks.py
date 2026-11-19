import hashlib
import hmac
import json
import time

import pytest
import stripe
from django.contrib.auth.models import Group
from django.core import mail
from django.urls import reverse

from fobandor.billing.models import CustomerSubscription, SubscriptionPlan
from fobandor.fulfillment.models import FulfillmentOrder


def _sign(payload: bytes, secret: str) -> str:
    t = int(time.time())
    msg = f"{t}.".encode() + payload
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    return f"t={t},v1={sig}"


@pytest.mark.django_db
def test_webhook_rejects_invalid_signature(client, settings):
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
    response = client.post(
        reverse("stripe-webhook"),
        data=b"{}",
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="t=1,v1=invalidsignature",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_webhook_invoice_paid_creates_order(client, settings, django_user_model):
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
    user = django_user_model.objects.create_user(
        email="c@example.com", password="x", stripe_customer_id="cus_123")
    plan = SubscriptionPlan.objects.create(
        slug="starter", name_es="Starter", name_en="Starter",
        price_usd="199.00", order_type="WEB_DEV")
    CustomerSubscription.objects.create(
        user=user, plan=plan, stripe_subscription_id="sub_123")

    payload = json.dumps({
        "type": "invoice.paid",
        "data": {"object": {
            "id": "in_123",
            "customer": "cus_123",
            "subscription": "sub_123",
            "amount_paid": 19900,
            "currency": "usd",
            "invoice_pdf": "https://example.com/inv.pdf",
        }},
    }).encode()

    response = client.post(
        reverse("stripe-webhook"),
        data=payload,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=_sign(payload, "whsec_test"),
    )
    assert response.status_code == 200
    assert FulfillmentOrder.objects.filter(stripe_invoice_id="in_123").count() == 1

    order = FulfillmentOrder.objects.get(stripe_invoice_id="in_123")
    assert order.user == user
    assert order.plan == plan
    assert order.order_type == "WEB_DEV"


@pytest.mark.django_db
def test_webhook_invoice_paid_assigns_default_assignee(client, settings, django_user_model):
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
    settings.DEFAULT_ASSIGNEE_EMAIL = "for@fobandor.com"
    user = django_user_model.objects.create_user(
        email="c@example.com", password="x", stripe_customer_id="cus_123")
    assignee = django_user_model.objects.create_user(
        email="for@fobandor.com", password="x")
    plan = SubscriptionPlan.objects.create(
        slug="starter", name_es="Starter", name_en="Starter", price_usd="199.00")
    CustomerSubscription.objects.create(
        user=user, plan=plan, stripe_subscription_id="sub_123")

    payload = json.dumps({
        "type": "invoice.paid",
        "data": {"object": {
            "id": "in_456",
            "customer": "cus_123",
            "subscription": "sub_123",
            "amount_paid": 19900,
            "currency": "usd",
        }},
    }).encode()

    client.post(
        reverse("stripe-webhook"),
        data=payload,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=_sign(payload, "whsec_test"),
    )

    order = FulfillmentOrder.objects.get(stripe_invoice_id="in_456")
    assert order.assigned_to == assignee


@pytest.mark.django_db
def test_webhook_invoice_paid_idempotent(client, settings, django_user_model):
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
    user = django_user_model.objects.create_user(
        email="c@example.com", password="x", stripe_customer_id="cus_123")
    plan = SubscriptionPlan.objects.create(
        slug="starter", name_es="Starter", name_en="Starter", price_usd="199.00")
    CustomerSubscription.objects.create(
        user=user, plan=plan, stripe_subscription_id="sub_123")

    payload = json.dumps({
        "type": "invoice.paid",
        "data": {"object": {
            "id": "in_123",
            "customer": "cus_123",
            "subscription": "sub_123",
            "amount_paid": 19900,
            "currency": "usd",
        }},
    }).encode()

    for _ in range(2):
        client.post(
            reverse("stripe-webhook"),
            data=payload,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=_sign(payload, "whsec_test"),
        )

    assert FulfillmentOrder.objects.filter(stripe_invoice_id="in_123").count() == 1


@pytest.mark.django_db
def test_webhook_invoice_paid_resolves_plan_without_prior_subscription(
        client, settings, django_user_model, monkeypatch):
    """Simula la carrera: invoice.paid llega antes que checkout.session.completed."""
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
    settings.STRIPE_SECRET_KEY = "sk_test_fake"
    user = django_user_model.objects.create_user(
        email="c@example.com", password="x", stripe_customer_id="cus_123")
    plan = SubscriptionPlan.objects.create(
        slug="conversion", name_es="Conversión", name_en="Conversion",
        price_usd="1297.00", stripe_price_id="price_xyz", order_type="MARKETING")

    def fake_retrieve(invoice_id, expand=None):
        return {
            "id": invoice_id,
            "lines": {"data": [{"price": {"id": "price_xyz"}}]},
        }

    monkeypatch.setattr(stripe.Invoice, "retrieve", fake_retrieve)

    payload = json.dumps({
        "type": "invoice.paid",
        "data": {"object": {
            "id": "in_999",
            "customer": "cus_123",
            "subscription": "sub_999",
            "amount_paid": 129700,
            "currency": "usd",
        }},
    }).encode()

    response = client.post(
        reverse("stripe-webhook"),
        data=payload,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=_sign(payload, "whsec_test"),
    )
    assert response.status_code == 200

    order = FulfillmentOrder.objects.get(stripe_invoice_id="in_999")
    assert order.user == user
    assert order.plan == plan
    assert order.order_type == "MARKETING"
    assert CustomerSubscription.objects.filter(
        stripe_subscription_id="sub_999", plan=plan).exists()


@pytest.mark.django_db
def test_invoice_paid_sends_customer_invoice_and_internal_alert(
        client, settings, django_user_model):
    """Verifica que invoice.paid despacha el correo al cliente y la alerta interna (Etapa 9)."""
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
    mail.outbox.clear()

    # Staff y grupo Content_Editors
    admin_user = django_user_model.objects.create_user(
        email="admin_staff@fobandor.com", password="x", is_staff=True)
    editor_user = django_user_model.objects.create_user(
        email="editor_team@fobandor.com", password="x")
    group, _ = Group.objects.get_or_create(name="Content_Editors")
    editor_user.groups.add(group)

    # Cliente
    client_user = django_user_model.objects.create_user(
        email="cliente@example.com", password="x", stripe_customer_id="cus_mail_test")
    plan = SubscriptionPlan.objects.create(
        slug="impulso", name_es="Plan 1 • Impulso", name_en="Plan 1 • Boost",
        price_usd="697.00", order_type="MARKETING")
    CustomerSubscription.objects.create(
        user=client_user, plan=plan, stripe_subscription_id="sub_mail_test")

    payload = json.dumps({
        "type": "invoice.paid",
        "data": {"object": {
            "id": "in_mail_test",
            "customer": "cus_mail_test",
            "subscription": "sub_mail_test",
            "amount_paid": 69700,
            "currency": "usd",
            "created": 1795039755,
            "invoice_pdf": "https://pay.stripe.com/invoice/test/pdf",
            "hosted_invoice_url": "https://pay.stripe.com/invoice/test",
        }},
    }).encode()

    response = client.post(
        reverse("stripe-webhook"),
        data=payload,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=_sign(payload, "whsec_test"),
    )
    assert response.status_code == 200

    # Deben haberse enviado 2 correos: 1 al cliente y 1 interno al equipo
    assert len(mail.outbox) == 2

    # 1. Correo al cliente
    cust_mail = next(m for m in mail.outbox if client_user.email in m.to)
    assert "¡Gracias por tu compra!" in cust_mail.subject
    assert "https://pay.stripe.com/invoice/test/pdf" in cust_mail.body
    assert "Plan 1 • Impulso" in cust_mail.body
    assert "admin@fobandor.com" in cust_mail.body
    assert "/mi-cuenta/" in cust_mail.body
    assert "/portal/dashboard/" not in cust_mail.body

    # 2. Alerta interna
    team_mail = next(m for m in mail.outbox if admin_user.email in m.to)
    assert editor_user.email in team_mail.to
    assert "Nueva compra de servicios" in team_mail.subject
    assert "cliente@example.com" in team_mail.subject
    assert "https://fobandor.com/en/backoffice/entregas/" in team_mail.body


@pytest.mark.django_db
def test_webhook_invoice_paid_resolves_modern_stripe_pricing_structure(client, settings, django_user_model):
    """Certifica que el webhook resuelve correctamente el formato moderno de Stripe (pricing.price_details.price)."""
    settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
    user = django_user_model.objects.create_user(
        email="modern@example.com", password="x", stripe_customer_id="cus_modern_123")
    plan = SubscriptionPlan.objects.create(
        slug="impulso-modern", name_es="Plan 1 • Impulso", name_en="Plan 1 • Boost",
        price_usd="697.00", stripe_price_id="price_modern_697", order_type="MARKETING")

    # Nótese: NO existe CustomerSubscription previa en la BD (prueba condición de carrera pura).
    payload = json.dumps({
        "type": "invoice.paid",
        "data": {"object": {
            "id": "in_modern_123",
            "customer": "cus_modern_123",
            "subscription": "sub_modern_123",
            "amount_paid": 69700,
            "currency": "usd",
            "created": 1795050800,
            "invoice_pdf": "https://pay.stripe.com/invoice/modern/pdf",
            "hosted_invoice_url": "https://pay.stripe.com/invoice/modern",
            "lines": {
                "object": "list",
                "data": [
                    {
                        "id": "il_modern_1",
                        "price": None,  # Modern Stripe payload entrega price=null
                        "pricing": {
                            "type": "price_details",
                            "price_details": {
                                "price": "price_modern_697",
                                "product": "prod_modern_1",
                            },
                        },
                    }
                ],
            },
        }},
    }).encode()

    response = client.post(
        reverse("stripe-webhook"),
        data=payload,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=_sign(payload, "whsec_test"),
    )
    assert response.status_code == 200

    order = FulfillmentOrder.objects.filter(user=user).first()
    assert order is not None
    assert order.plan == plan
    assert order.order_type == "MARKETING"

    sub = CustomerSubscription.objects.filter(user=user).first()
    assert sub is not None
    assert sub.plan == plan
    assert sub.status == "active"
