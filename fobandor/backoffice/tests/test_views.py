import pytest
from django.urls import reverse

from fobandor.billing.models import SubscriptionPlan


@pytest.mark.django_db
def test_dashboard_anonymous_redirects(client):
    url = reverse('backoffice:dashboard')
    response = client.get(url, follow=False)
    assert response.status_code in (302, 301)


@pytest.mark.django_db
def test_dashboard_staff_access(client, django_user_model):
    user = django_user_model.objects.create_user(
        email='staff@fobandor.com', password='Test1234!', is_staff=True)
    client.force_login(user)
    url = reverse('backoffice:dashboard')
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_dashboard_non_staff_redirects(client, django_user_model):
    user = django_user_model.objects.create_user(
        email='client@example.com', password='Test1234!', is_staff=False)
    client.force_login(user)
    url = reverse('backoffice:dashboard')
    response = client.get(url, follow=False)
    assert response.status_code in (302, 301)


@pytest.mark.django_db
def test_plan_list_staff_access(client, django_user_model):
    user = django_user_model.objects.create_user(
        email='staff@fobandor.com', password='Test1234!', is_staff=True)
    client.force_login(user)
    response = client.get(reverse('backoffice:plan-list'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_plan_list_anonymous_redirects(client):
    response = client.get(reverse('backoffice:plan-list'), follow=False)
    assert response.status_code in (302, 301)


@pytest.mark.django_db
def test_plan_update_staff_access(client, django_user_model):
    user = django_user_model.objects.create_user(
        email='staff@fobandor.com', password='Test1234!', is_staff=True)
    client.force_login(user)
    plan = SubscriptionPlan.objects.create(
        slug='impulso', name_es='Impulso', name_en='Impulso', price_usd='697.00')
    response = client.get(reverse('backoffice:plan-update', args=[plan.pk]))
    assert response.status_code == 200
