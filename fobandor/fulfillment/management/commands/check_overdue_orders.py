from django.core.management.base import BaseCommand
from django.utils import timezone

from fobandor.fulfillment.models import FulfillmentOrder


class Command(BaseCommand):
    help = "Marca como VENCIDA las órdenes cuyo due_date ya venció (ADR-009). Idempotente."

    def handle(self, *args, **options):
        now = timezone.now()
        overdue = FulfillmentOrder.objects.filter(
            status__in=["PENDIENTE_PRODUCCION", "EN_PROCESO"],
            due_date__lt=now,
        )
        count = overdue.update(status="VENCIDA")
        self.stdout.write(self.style.SUCCESS(f"✅ {count} orden(es) marcada(s) como VENCIDA."))
