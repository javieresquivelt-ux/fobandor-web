from django.db import models
from django.utils.translation import gettext_lazy as _

from fobandor.users.models import User


class SubscriptionPlan(models.Model):
    """Catálogo de planes de suscripción mensual."""

    ORDER_TYPE_CHOICES = [
        ("WEB_DEV", _("Desarrollo Web con IA")),
        ("APP_DEV", _("Desarrollo de Apps con IA")),
        ("ADS_AI", _("Publicidad con IA")),
        ("STUDIOS", _("Fobandor Studios")),
        ("MARKETING", _("Acompañamiento de Marketing")),
    ]

    slug = models.SlugField(max_length=60, unique=True)
    name_es = models.CharField("Nombre (ES)", max_length=120)
    name_en = models.CharField("Name (EN)", max_length=120)
    subtitle_es = models.CharField("Subtítulo (ES)", max_length=150, blank=True)
    subtitle_en = models.CharField("Subtitle (EN)", max_length=150, blank=True)
    desc_es = models.TextField("Descripción (ES)", blank=True)
    desc_en = models.TextField("Description (EN)", blank=True)
    price_usd = models.DecimalField("Precio (USD)", max_digits=8, decimal_places=2)
    stripe_price_id = models.CharField("Stripe Price ID", max_length=100, blank=True)
    features_es = models.JSONField("Características (ES)", default=list, blank=True)
    features_en = models.JSONField("Features (EN)", default=list, blank=True)
    min_commitment_months = models.PositiveSmallIntegerField(
        "Compromiso mínimo (meses)", default=1,
        help_text="Acompañamiento mínimo exigido (ej. 2 o 3 meses). Informativo.")
    target_audience_es = models.TextField("Público objetivo (ES)", blank=True)
    target_audience_en = models.TextField("Target audience (EN)", blank=True)
    disclaimer_es = models.TextField("Aviso legal (ES)", blank=True)
    disclaimer_en = models.TextField("Legal disclaimer (EN)", blank=True)
    order_type = models.CharField(
        "Línea de servicio", max_length=20, choices=ORDER_TYPE_CHOICES, default="MARKETING")
    order = models.PositiveSmallIntegerField("Orden", default=0)
    is_active = models.BooleanField("Activo", default=True)
    is_highlighted = models.BooleanField("Destacado", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "Plan de Suscripción"
        verbose_name_plural = "Planes de Suscripción"

    def __str__(self):
        return self.name_es


class CustomerSubscription(models.Model):
    """Estado local sincronizado de la suscripción del cliente en Stripe."""

    STATUS_CHOICES = [
        ("active", "Activa"),
        ("past_due", "En mora"),
        ("unpaid", "Impaga"),
        ("trialing", "En prueba"),
        ("canceled", "Cancelada"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="subscriptions")
    stripe_subscription_id = models.CharField(
        "Stripe Subscription ID", max_length=100, unique=True)
    status = models.CharField("Estado", max_length=20, choices=STATUS_CHOICES, default="active")
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Suscripción de Cliente"
        verbose_name_plural = "Suscripciones de Clientes"

    def __str__(self):
        return f"{self.user.email} → {self.stripe_subscription_id}"


class BillingInvoice(models.Model):
    """Historial de facturas y cobros sincronizados desde Stripe."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="invoices")
    stripe_invoice_id = models.CharField("Stripe Invoice ID", max_length=100, unique=True)
    amount_paid = models.DecimalField("Monto pagado", max_digits=10, decimal_places=2)
    currency = models.CharField("Moneda", max_length=3, default="usd")
    paid_at = models.DateTimeField("Fecha de pago", null=True, blank=True)
    invoice_pdf_url = models.URLField("URL del PDF", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-paid_at"]
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"

    def __str__(self):
        return self.stripe_invoice_id
