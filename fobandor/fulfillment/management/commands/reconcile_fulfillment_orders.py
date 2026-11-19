from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from fobandor.billing.models import CustomerSubscription
from fobandor.billing.services import send_customer_purchase_email, send_internal_purchase_alert
from fobandor.fulfillment.models import FulfillmentOrder
from fobandor.users.models import User


class Command(BaseCommand):
    help = (
        "Reconcilia órdenes huérfanas (plan=null) y crea órdenes faltantes "
        "para suscripciones activas sin entrega. Idempotente."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--notify",
            action="store_true",
            help="Dispara las notificaciones por correo para las órdenes creadas.",
        )

    def handle(self, *args, **options):
        notify = options.get("notify", False)
        fixed = 0
        created = 0

        # 1. Reconciliar órdenes existentes sin plan
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

        # 2. Crear órdenes para suscripciones activas sin orden de entrega
        default_email = getattr(settings, "DEFAULT_ASSIGNEE_EMAIL", "for@fobandor.com")
        assignee = User.objects.filter(email=default_email).first() if default_email else None

        active_subs = (
            CustomerSubscription.objects.filter(status="active", plan__isnull=False)
            .select_related("user", "plan")
        )
        for sub in active_subs:
            has_order = FulfillmentOrder.objects.filter(subscription=sub).exists()
            if not has_order and sub.user:
                order = FulfillmentOrder.objects.create(
                    user=sub.user,
                    subscription=sub,
                    plan=sub.plan,
                    order_type=sub.plan.order_type,
                    assigned_to=assignee,
                    paid_at=sub.created_at or timezone.now(),
                    status="PENDIENTE_PRODUCCION",
                )
                created += 1
                if notify:
                    dummy_invoice = {
                        "amount_paid": int(sub.plan.price * 100) if sub.plan.price else 0,
                        "currency": "USD",
                        "invoice_pdf": "",
                        "hosted_invoice_url": "",
                    }
                    send_customer_purchase_email(sub.user, dummy_invoice, sub.plan, order)
                    send_internal_purchase_alert(sub.user, dummy_invoice, sub.plan, order)

        self.stdout.write(
            self.style.SUCCESS(f"✅ {fixed} órdenes actualizadas, {created} órdenes nuevas creadas.")
        )
