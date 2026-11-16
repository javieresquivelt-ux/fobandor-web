from django.core.management.base import BaseCommand

from fobandor.billing.models import SubscriptionPlan


PLANS = [
    {
        "slug": "starter",
        "name_es": "Starter",
        "name_en": "Starter",
        "desc_es": "Desarrollo Web y contenido base impulsado por IA.",
        "desc_en": "AI-powered web development and base content.",
        "price_usd": "199.00",
        "features_es": ["Sitio web corporativo", "Landing pages", "Contenido mensual base"],
        "features_en": ["Corporate website", "Landing pages", "Monthly base content"],
        "order_type": "WEB_DEV",
        "order": 1,
        "is_highlighted": False,
    },
    {
        "slug": "pro",
        "name_es": "Pro",
        "name_en": "Pro",
        "desc_es": "Web + Apps + Publicidad IA mensual.",
        "desc_en": "Web + Apps + monthly AI advertising.",
        "price_usd": "499.00",
        "features_es": ["Web + Apps", "Publicidad IA mensual", "Campañas y creatividades"],
        "features_en": ["Web + Apps", "Monthly AI advertising", "Campaigns and creatives"],
        "order_type": "ADS_AI",
        "order": 2,
        "is_highlighted": True,
    },
    {
        "slug": "enterprise",
        "name_es": "Enterprise",
        "name_en": "Enterprise",
        "desc_es": "Solución Full Stack + Fobandor Studios.",
        "desc_en": "Full Stack solution + Fobandor Studios.",
        "price_usd": "999.00",
        "features_es": ["Solución Full Stack", "Fobandor Studios", "Producción audiovisual IA"],
        "features_en": ["Full Stack solution", "Fobandor Studios", "AI audiovisual production"],
        "order_type": "STUDIOS",
        "order": 3,
        "is_highlighted": False,
    },
]


class Command(BaseCommand):
    help = "Siembra los 3 planes de suscripción base (idempotente — usa get_or_create)."

    def handle(self, *args, **options):
        for data in PLANS:
            obj, created = SubscriptionPlan.objects.get_or_create(
                slug=data["slug"], defaults=data)
            status = "CREADO" if created else "YA EXISTE"
            self.stdout.write(f"  [{status}] {obj.name_es} (${obj.price_usd})")
        self.stdout.write(self.style.SUCCESS("✅ seed_subscription_plans completado."))
