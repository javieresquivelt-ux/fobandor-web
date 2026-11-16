from django.contrib import admin

from .models import BillingInvoice, CustomerSubscription, SubscriptionPlan


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name_es", "slug", "price_usd", "order_type", "is_active", "order")
    list_editable = ("order", "is_active")
    list_filter = ("is_active", "order_type")
    search_fields = ("name_es", "name_en", "slug", "stripe_price_id")
    prepopulated_fields = {"slug": ("name_es",)}


@admin.register(CustomerSubscription)
class CustomerSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "stripe_subscription_id", "current_period_end")
    list_filter = ("status", "plan")
    search_fields = ("user__email", "stripe_subscription_id")


@admin.register(BillingInvoice)
class BillingInvoiceAdmin(admin.ModelAdmin):
    list_display = ("stripe_invoice_id", "user", "amount_paid", "currency", "paid_at")
    list_filter = ("currency",)
    search_fields = ("stripe_invoice_id", "user__email")
