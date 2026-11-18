from django.core.management.base import BaseCommand

from fobandor.billing.models import CustomerSubscription
from fobandor.fulfillment.models import FulfillmentOrder


class Command(BaseCommand):
    help = (
        "Reconcilia órdenes huérfanas (plan=null) vinculándolas a la suscripción "
        "y plan del cliente. Idempotente."
    )

    def handle(self, *args, **options):
        fixed = 0
        for order in FulfillmentOrder.objects.filter(plan__isnull=True).select_related("user"):
            subscription = CustomerSubscription.objects.filter(
                user=order.user, plan__isnull=False).first()
            if not subscription:
                continue
            order.plan = subscription.plan
            order.subscription = subscription
            order.order_type = subscription.plan.order_type
            order.save(update_fields=["plan", "subscription", "order_type"])
            fixed += 1
        self.stdout.write(self.style.SUCCESS(f"✅ {fixed} órdenes reconciliadas."))
