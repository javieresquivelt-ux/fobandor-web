import pytest
from django.urls import reverse

from fobandor.billing import services
from fobandor.billing.models import SubscriptionPlan
from fobandor.cms.models import CompanyProfile


@pytest.mark.django_db
def test_pricing_view_injects_formspree_endpoint(client, settings):
    settings.FORMSPREE_ENDPOINT = "https://formspree.io/f/testid"
    response = client.get(reverse("billing:pricing"))
    assert response.status_code == 200
    content = response.content.decode()
    assert 'action="https://formspree.io/f/testid"' in content
    assert 'name="_gotcha"' in content
    assert 'name="_subject"' in content
    assert "@submit.prevent" in content


@pytest.mark.django_db
def test_pricing_view_lists_active_plans(client):
    SubscriptionPlan.objects.create(
        slug="impulso", name_es="Impulso", name_en="Impulso", price_usd="697.00", order=1)
    response = client.get(reverse("billing:pricing"))
    assert response.status_code == 200
    assert "Impulso" in response.content.decode()


@pytest.mark.django_db
def test_pricing_view_uses_company_profile_diag_texts(client):
    profile = CompanyProfile.load()
    profile.diag_form_subject = "Asunto de prueba"
    profile.diag_modal_title_es = "Título enviado"
    profile.diag_modal_title_en = "Title sent"
    profile.diag_success_msg_es = "Mensaje de éxito ES"
    profile.diag_success_msg_en = "Success message EN"
    profile.save()

    response = client.get(reverse("billing:pricing"))
    assert response.status_code == 200
    content = response.content.decode()
    assert 'value="Asunto de prueba"' in content
    assert "Título enviado" in content
    assert "Mensaje de éxito ES" in content


class _FakeCheckoutSession:
    url = "https://checkout.stripe.com/pay/test_session"


@pytest.mark.django_db
def test_checkout_get_redirects_to_stripe(client, django_user_model, monkeypatch, settings):
    settings.STRIPE_SECRET_KEY = "sk_test_fake"
    user = django_user_model.objects.create_user(
        email="c@example.com", password="x", is_email_verified=True)
    plan = SubscriptionPlan.objects.create(
        slug="impulso", name_es="Impulso", name_en="Impulso",
        price_usd="697.00", stripe_price_id="price_123")
    client.force_login(user)

    monkeypatch.setattr(
        services, "create_checkout_session",
        lambda u, p, s, c: _FakeCheckoutSession())

    response = client.get(reverse("billing:checkout", args=[plan.slug]))
    assert response.status_code == 302
    assert response.url == "https://checkout.stripe.com/pay/test_session"


@pytest.mark.django_db
def test_customer_portal_builds_canonical_return_url(client, django_user_model, monkeypatch):
    user = django_user_model.objects.create_user(email="c@example.com", password="x")
    client.force_login(user)

    captured = {}

    class _FakePortalSession:
        url = "https://billing.stripe.com/session/test"

    def fake(user, return_url):
        captured["return_url"] = return_url
        return _FakePortalSession()

    monkeypatch.setattr(services, "create_customer_portal_session", fake)

    response = client.post(reverse("billing:portal"))
    assert response.status_code == 302
    assert "/mi-cuenta/" in captured["return_url"]
