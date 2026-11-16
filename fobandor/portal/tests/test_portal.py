import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_portal_dashboard_anonymous_redirects(client):
    url = reverse("portal:dashboard")
    response = client.get(url, follow=False)
    assert response.status_code in (302, 301)


@pytest.mark.django_db
def test_portal_dashboard_authenticated(client, django_user_model):
    user = django_user_model.objects.create_user(email="c@example.com", password="x")
    client.force_login(user)
    response = client.get(reverse("portal:dashboard"))
    assert response.status_code == 200
