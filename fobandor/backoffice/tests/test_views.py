import pytest
from django.urls import reverse


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
