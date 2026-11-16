import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_robots_txt_status_and_content(client):
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    content = response.content.decode()
    assert "User-agent: *" in content
    assert "Allow: /" in content
    assert "Disallow: /admin/" in content
    assert "Disallow: /backoffice/" in content
    assert "Disallow: /mi-cuenta/" in content
    assert "Disallow: /stripe/" in content
    assert "Sitemap: https://www.fobandor.com/sitemap.xml" in content


@pytest.mark.django_db
def test_sitemap_xml_status_and_urls(client):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert "xml" in response.headers["content-type"]
    content = response.content.decode()
    assert "<urlset" in content
    assert "/es/" in content
    assert "/en/" in content
    assert "/es/precios/" in content
    assert "/en/precios/" in content


@pytest.mark.django_db
def test_open_graph_meta_tags_rendered(client):
    response = client.get(reverse("core:home"))
    assert response.status_code == 200
    content = response.content.decode()
    assert 'property="og:site_name" content="FOBANDOR"' in content
    assert 'property="og:title"' in content
    assert 'property="og:description"' in content
    assert 'property="og:image"' in content
    assert 'name="twitter:card" content="summary_large_image"' in content
