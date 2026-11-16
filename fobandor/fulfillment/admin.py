from django.contrib import admin

from .models import FulfillmentOrder


@admin.register(FulfillmentOrder)
class FulfillmentOrderAdmin(admin.ModelAdmin):
    list_display = ("user", "order_type", "status", "paid_at", "due_date", "delivered_at")
    list_filter = ("status", "order_type")
    search_fields = ("user__email", "stripe_invoice_id")
    readonly_fields = ("created_at", "updated_at")
