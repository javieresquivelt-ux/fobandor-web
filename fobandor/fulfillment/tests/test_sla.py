from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from fobandor.fulfillment.models import FulfillmentOrder


@pytest.mark.django_db
def test_due_date_is_seven_days_after_payment(django_user_model):
    user = django_user_model.objects.create_user(email="c@example.com", password="x")
    paid_at = timezone.now()
    order = FulfillmentOrder.objects.create(user=user, paid_at=paid_at)
    assert order.due_date == paid_at + timedelta(days=7)


@pytest.mark.django_db
def test_check_overdue_orders_marks_overdue(django_user_model):
    user = django_user_model.objects.create_user(email="c@example.com", password="x")
    order = FulfillmentOrder.objects.create(
        user=user,
        paid_at=timezone.now() - timedelta(days=10),
        due_date=timezone.now() - timedelta(days=3),
        status="PENDIENTE_PRODUCCION",
    )
    call_command("check_overdue_orders", verbosity=0)
    order.refresh_from_db()
    assert order.status == "VENCIDA"


@pytest.mark.django_db
def test_deliver_marks_delivered(django_user_model):
    user = django_user_model.objects.create_user(email="c@example.com", password="x")
    order = FulfillmentOrder.objects.create(user=user)
    order.status = "ENTREGADA"
    order.delivered_at = timezone.now()
    order.save()
    order.refresh_from_db()
    assert order.status == "ENTREGADA"
    assert order.delivered_at is not None


@pytest.mark.django_db
def test_sla_level_semaphore(django_user_model):
    user = django_user_model.objects.create_user(email="c@example.com", password="x")
    overdue = FulfillmentOrder.objects.create(
        user=user, paid_at=timezone.now() - timedelta(days=10),
        due_date=timezone.now() - timedelta(days=1))
    assert overdue.sla_level == "red"

    tight = FulfillmentOrder.objects.create(
        user=user, paid_at=timezone.now(),
        due_date=timezone.now() + timedelta(days=1))
    assert tight.sla_level == "yellow"

    relaxed = FulfillmentOrder.objects.create(
        user=user, paid_at=timezone.now(),
        due_date=timezone.now() + timedelta(days=6))
    assert relaxed.sla_level == "green"
