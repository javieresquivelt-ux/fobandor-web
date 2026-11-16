"""Configuración de URLs raíz de FOBANDOR."""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from fobandor.billing.views import StripeWebhookView
from fobandor.core.sitemaps import StaticViewSitemap

sitemaps = {
    "static": StaticViewSitemap,
}

urlpatterns = [
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("i18n/", include("django.conf.urls.i18n")),
    path("accounts/", include("allauth.urls")),
    path("stripe/webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("backoffice/", include("fobandor.backoffice.urls", namespace="backoffice")),
    path("precios/", include("fobandor.billing.urls")),
    path("mi-cuenta/", include("fobandor.portal.urls")),
    path("", include("fobandor.core.urls")),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
