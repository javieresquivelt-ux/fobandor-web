from datetime import timedelta

from django.db import models
from django.utils import timezone

from fobandor.billing.models import CustomerSubscription
from fobandor.users.models import User


class FulfillmentOrder(models.Model):
    """Orden de entrega con compromiso de servicio (SLA de 7 días)."""

    ORDER_TYPES = [
        ("WEB_DEV", "Desarrollo Web con IA"),
        ("APP_DEV", "Desarrollo de Apps con IA"),
        ("ADS_AI", "Publicidad con IA"),
        ("STUDIOS", "Fobandor Studios"),
        ("MARKETING", "Acompañamiento de Marketing"),
    ]

    STATUS_CHOICES = [
        ("PENDIENTE_PRODUCCION", "Pendiente de Producción"),
        ("EN_PROCESO", "En Proceso"),
        ("ENTREGADA", "Entregada"),
        ("VENCIDA", "Vencida"),
        ("CANCELADA", "Cancelada"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="fulfillment_orders")
    subscription = models.ForeignKey(
        CustomerSubscription, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="fulfillment_orders")
    plan = models.ForeignKey(
        'billing.SubscriptionPlan', on_delete=models.SET_NULL, null=True, blank=True,
        related_name="fulfillment_orders", verbose_name="Plan de Suscripción")
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="assigned_orders", verbose_name="Asignado a")
    order_type = models.CharField(
        "Línea de servicio", max_length=20, choices=ORDER_TYPES, default="WEB_DEV")
    stripe_invoice_id = models.CharField(
        "Stripe Invoice ID", max_length=100, unique=True, null=True, blank=True)
    status = models.CharField(
        "Estado", max_length=25, choices=STATUS_CHOICES, default="PENDIENTE_PRODUCCION")
    paid_at = models.DateTimeField("Fecha de pago", default=timezone.now)
    due_date = models.DateTimeField("Fecha límite", null=True, blank=True)
    delivered_at = models.DateTimeField("Fecha de entrega", null=True, blank=True)
    deliverable_file = models.FileField("Entregable", upload_to="deliverables/", blank=True)
    deliverable_url = models.URLField("URL del entregable", blank=True)
    internal_notes = models.TextField("Notas internas", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_date", "-created_at"]
        verbose_name = "Orden de Entrega"
        verbose_name_plural = "Órdenes de Entrega"

    def __str__(self):
        return f"{self.user.email} → {self.get_order_type_display()} [{self.status}]"

    def save(self, *args, **kwargs):
        if self.paid_at and not self.due_date:
            self.due_date = self.paid_at + timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def days_remaining(self):
        if self.status in ("ENTREGADA", "CANCELADA"):
            return 0
        if not self.due_date:
            return 7
        delta = self.due_date - timezone.now()
        return max(0, delta.days)

    @property
    def is_overdue(self):
        if self.status in ("ENTREGADA", "CANCELADA", "VENCIDA"):
            return False
        return bool(self.due_date and self.due_date < timezone.now())

    @property
    def sla_level(self):
        """Semáforo del SLA: 'green' holgado, 'yellow' <= 2 días, 'red' vencida."""
        if self.status in ("ENTREGADA", "CANCELADA"):
            return "done"
        if self.status == "VENCIDA" or self.is_overdue:
            return "red"
        if self.days_remaining <= 2:
            return "yellow"
        return "green"
