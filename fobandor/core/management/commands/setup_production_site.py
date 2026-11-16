from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand

import environ

env = environ.Env()


class Command(BaseCommand):
    help = "Configura el dominio del Site oficial para sitemaps, emails y allauth."

    def handle(self, *args, **options):
        site_id = getattr(settings, "SITE_ID", 1)
        domain = env("SITE_DOMAIN", default="www.fobandor.com")
        name = env("SITE_NAME", default="FOBANDOR")
        site, created = Site.objects.update_or_create(
            id=site_id,
            defaults={"domain": domain, "name": name},
        )
        action = "creado" if created else "actualizado"
        self.stdout.write(self.style.SUCCESS(f"Site ID {site_id} {action} a {domain} ({name})"))
