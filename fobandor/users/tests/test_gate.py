import pytest
from django.urls import reverse
from unittest.mock import patch

from fobandor.billing.models import SubscriptionPlan
from fobandor.users.adapters import CustomAccountAdapter
from fobandor.users.signals import mark_user_email_verified


@pytest.mark.django_db
def test_checkout_blocked_without_verified_email(client, django_user_model):
    user = django_user_model.objects.create_user(email="c@example.com", password="x")
    plan = SubscriptionPlan.objects.create(
        slug="starter", name_es="Starter", name_en="Starter", price_usd="199.00")
    client.force_login(user)
    response = client.post(reverse("billing:checkout", args=[plan.slug]))
    assert response.status_code == 302
    assert "email" in response.url


@pytest.mark.django_db
def test_checkout_passes_gate_with_verified_email(client, django_user_model):
    user = django_user_model.objects.create_user(
        email="c@example.com", password="x", is_email_verified=True)
    plan = SubscriptionPlan.objects.create(
        slug="starter", name_es="Starter", name_en="Starter", price_usd="199.00")
    client.force_login(user)
    response = client.post(reverse("billing:checkout", args=[plan.slug]))
    assert response.status_code == 302
    assert "email" not in response.url


@pytest.mark.django_db
def test_email_confirmed_signal_marks_user_verified(django_user_model):
    user = django_user_model.objects.create_user(email="c@example.com", password="x")

    class FakeEmailAddress:
        pass

    email_address = FakeEmailAddress()
    email_address.user = user

    mark_user_email_verified(sender=None, request=None, email_address=email_address)
    user.refresh_from_db()
    assert user.is_email_verified is True


# ---------------------------------------------------------------------------
# Etapa 7 — Blindaje SMTP: CustomAccountAdapter.send_mail no propaga 500
# ---------------------------------------------------------------------------

def test_adapter_send_mail_swallows_smtp_exception(rf):
    """Si el backend SMTP lanza una excepción, send_mail la captura y NO relanza."""
    adapter = CustomAccountAdapter(request=rf.get("/"))
    with patch(
        "allauth.account.adapter.DefaultAccountAdapter.send_mail",
        side_effect=OSError("Connection refused"),
    ):
        # No debe lanzar ninguna excepción
        adapter.send_mail("account/email/email_confirmation", "test@example.com", {})


@pytest.mark.django_db
def test_signup_no_500_when_smtp_unavailable(client, settings):
    """POST /accounts/signup/ con SMTP no configurado no debe devolver 500."""
    settings.ACCOUNT_EMAIL_VERIFICATION = "optional"
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    url = reverse("account_signup")
    data = {
        "email": "nuevo@example.com",
        "password1": "TestPass!2025",
        "password2": "TestPass!2025",
    }
    response = client.post(url, data)
    assert response.status_code != 500, (
        f"El endpoint de signup devolvió 500. Status: {response.status_code}"
    )
