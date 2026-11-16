from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import translation


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return [
            ("core:home", "es"),
            ("core:home", "en"),
            ("billing:pricing", "es"),
            ("billing:pricing", "en"),
        ]

    def location(self, item):
        view_name, lang = item
        with translation.override(lang):
            return reverse(view_name)
