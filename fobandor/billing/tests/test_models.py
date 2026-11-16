import pytest

from fobandor.billing.models import SubscriptionPlan


@pytest.mark.django_db
def test_subscription_plan_creation():
    plan = SubscriptionPlan.objects.create(
        slug="impulso", name_es="Impulso", name_en="Impulso", price_usd="697.00")
    assert str(plan) == "Impulso"
    assert plan.features_es == []
    assert plan.order_type == "MARKETING"
    assert plan.min_commitment_months == 1


@pytest.mark.django_db
def test_subscription_plan_extended_fields():
    plan = SubscriptionPlan.objects.create(
        slug="conversion", name_es="Conversión", name_en="Conversion",
        price_usd="1297.00", subtitle_es="Convierte", subtitle_en="Convert",
        min_commitment_months=3, target_audience_es="Ideal para...",
        disclaimer_es="*Aviso", disclaimer_en="*Disclaimer",
        features_es=["a", "b"], features_en=["x", "y"])
    assert plan.subtitle_es == "Convierte"
    assert plan.min_commitment_months == 3
    assert plan.features_es == ["a", "b"]
    assert plan.is_highlighted is False


@pytest.mark.django_db
def test_seed_subscription_plans_idempotent_and_legacy_cleanup():
    from django.core.management import call_command
    SubscriptionPlan.objects.create(
        slug="legacy", name_es="Legacy", name_en="Legacy", price_usd="1.00")
    call_command("seed_subscription_plans", verbosity=0)
    call_command("seed_subscription_plans", verbosity=0)

    active = SubscriptionPlan.objects.filter(is_active=True)
    assert list(active.values_list("slug", flat=True).order_by("slug")) == [
        "conversion", "crecimiento", "impulso"]
    assert SubscriptionPlan.objects.filter(slug="legacy", is_active=False).exists()
