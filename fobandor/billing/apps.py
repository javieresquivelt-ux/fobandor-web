from django.apps import AppConfig


class BillingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fobandor.billing"
    label = "billing"
    verbose_name = "Facturación"
