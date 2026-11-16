import pytest
from django.urls import reverse

from fobandor.billing.models import SubscriptionPlan
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
