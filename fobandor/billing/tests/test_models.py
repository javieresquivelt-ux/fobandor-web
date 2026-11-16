import pytest

from fobandor.billing.models import SubscriptionPlan


@pytest.mark.django_db
def test_subscription_plan_creation():
    plan = SubscriptionPlan.objects.create(
        slug="starter", name_es="Starter", name_en="Starter", price_usd="199.00")
    assert str(plan) == "Starter"
    assert plan.features_es == []
    assert plan.order_type == "WEB_DEV"


@pytest.mark.django_db
def test_seed_subscription_plans_idempotent():
    from django.core.management import call_command
    call_command("seed_subscription_plans", verbosity=0)
    count = SubscriptionPlan.objects.count()
    call_command("seed_subscription_plans", verbosity=0)
    assert SubscriptionPlan.objects.count() == count == 3
