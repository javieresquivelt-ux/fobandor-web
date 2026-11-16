from django.core.management.base import BaseCommand

from fobandor.billing.models import SubscriptionPlan


DISCLAIMER_ES = (
    "*La inversión publicitaria en Meta Ads y las herramientas de terceros no están "
    "incluidas. Los valores base consideran 1 negocio, 1 ubicación y 1 oferta principal."
)
DISCLAIMER_EN = (
    "*Meta Ads ad spend and third-party tools are not included. Base pricing covers "
    "1 business, 1 location and 1 main offer."
)

PLANS = [
    {
        "slug": "impulso",
        "name_es": "Plan 1 • Impulso",
        "name_en": "Plan 1 • Momentum",
        "subtitle_es": "Genera demanda",
        "subtitle_en": "Generate demand",
        "desc_es": "Acompañamiento de Marketing Digital & Ventas para negocios locales.",
        "desc_en": "Digital Marketing & Sales support for local businesses.",
        "price_usd": "697.00",
        "min_commitment_months": 2,
        "target_audience_es": "Ideal para negocios que necesitan atraer interesados.",
        "target_audience_en": "Ideal for businesses that need to attract prospects.",
        "order_type": "MARKETING",
        "order": 1,
        "is_highlighted": False,
        "features_es": [
            "Diagnóstico comercial inicial",
            "Definición de oferta, buyer y canal",
            "Revisión de Meta Business Suite",
            "Configuración y lanzamiento de Meta Ads",
            "Testeo de anuncios y creativos",
            "Análisis de resultados y optimización",
            "Recomendación del mejor destino: web, booking, formulario o WhatsApp",
        ],
        "features_en": [
            "Initial business diagnosis",
            "Offer, buyer and channel definition",
            "Meta Business Suite review",
            "Meta Ads setup and launch",
            "Ad and creative testing",
            "Results analysis and optimization",
            "Best destination recommendation: web, booking, form or WhatsApp",
        ],
        "disclaimer_es": DISCLAIMER_ES,
        "disclaimer_en": DISCLAIMER_EN,
    },
    {
        "slug": "conversion",
        "name_es": "Plan 2 • Conversión",
        "name_en": "Plan 2 • Conversion",
        "subtitle_es": "Convierte oportunidades",
        "subtitle_en": "Convert opportunities",
        "desc_es": "Acompañamiento de Marketing Digital & Ventas para negocios locales.",
        "desc_en": "Digital Marketing & Sales support for local businesses.",
        "price_usd": "1297.00",
        "min_commitment_months": 3,
        "target_audience_es": "Ideal para negocios que reciben consultas, pero pierden oportunidades.",
        "target_audience_en": "Ideal for businesses that receive inquiries but lose opportunities.",
        "order_type": "MARKETING",
        "order": 2,
        "is_highlighted": True,
        "features_es": [
            "Todo lo del Plan Impulso",
            "Diseño del embudo de conversión",
            "CRM / pipeline comercial básico",
            "Automatización de respuestas y seguimiento",
            "Agenda, confirmaciones y recordatorios",
            "Guión comercial de atención y cierre",
            "Métricas de conversión: citas, show rate, close rate y CAC",
        ],
        "features_en": [
            "Everything in the Impulso Plan",
            "Conversion funnel design",
            "Basic CRM / sales pipeline",
            "Response and follow-up automation",
            "Scheduling, confirmations and reminders",
            "Sales script for service and closing",
            "Conversion metrics: appointments, show rate, close rate and CAC",
        ],
        "disclaimer_es": DISCLAIMER_ES,
        "disclaimer_en": DISCLAIMER_EN,
    },
    {
        "slug": "crecimiento",
        "name_es": "Plan 3 • Crecimiento",
        "name_en": "Plan 3 • Growth",
        "subtitle_es": "Vende más y fideliza",
        "subtitle_en": "Sell more and retain",
        "desc_es": "Acompañamiento de Marketing Digital & Ventas para negocios locales.",
        "desc_en": "Digital Marketing & Sales support for local businesses.",
        "price_usd": "1997.00",
        "min_commitment_months": 3,
        "target_audience_es": "Ideal para negocios que ya venden y quieren crecer con su base de clientes.",
        "target_audience_en": "Ideal for businesses that already sell and want to grow their client base.",
        "order_type": "MARKETING",
        "order": 3,
        "is_highlighted": False,
        "features_es": [
            "Todo lo del Plan Conversión",
            "Estrategias de recompra y postventa",
            "Reactivación de clientes antiguos",
            "Solicitud de reseñas y referidos",
            "Upsell y cross-sell",
            "Segmentación de base de clientes",
            "Métricas de crecimiento: recompra, LTV y escalamiento",
        ],
        "features_en": [
            "Everything in the Conversión Plan",
            "Repurchase and after-sales strategies",
            "Reactivation of former clients",
            "Reviews and referrals requests",
            "Upsell and cross-sell",
            "Client base segmentation",
            "Growth metrics: repurchase, LTV and scaling",
        ],
        "disclaimer_es": DISCLAIMER_ES,
        "disclaimer_en": DISCLAIMER_EN,
    },
]


class Command(BaseCommand):
    help = (
        "Siembra los planes de acompañamiento reales de FOBANDOR y desactiva los "
        "planes legacy (idempotente)."
    )

    def handle(self, *args, **options):
        slugs = []
        for data in PLANS:
            obj, created = SubscriptionPlan.objects.get_or_create(
                slug=data["slug"], defaults=data)
            if not created:
                SubscriptionPlan.objects.filter(slug=data["slug"]).update(**data)
            slugs.append(obj.slug)
            status = "CREADO" if created else "ACTUALIZADO"
            self.stdout.write(f"  [{status}] {obj.name_es} (${obj.price_usd})")

        deactivated = SubscriptionPlan.objects.exclude(slug__in=slugs).update(is_active=False)
        if deactivated:
            self.stdout.write(f"  [OK] {deactivated} plan(es) legacy desactivado(s).")

        self.stdout.write(self.style.SUCCESS("✅ seed_subscription_plans completado."))
