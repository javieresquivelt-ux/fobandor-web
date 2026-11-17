import pytest
from django.urls import reverse

from fobandor.billing.models import SubscriptionPlan


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
