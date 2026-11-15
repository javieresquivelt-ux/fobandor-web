from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from fobandor.users.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "is_staff", "is_email_verified")
    search_fields = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Información Personal", {"fields": ("first_name", "last_name", "phone")}),
        (
            "Perfil de Negocio",
            {
                "fields": (
                    "company_name",
                    "social_handle",
                    "tax_id",
                    "preferred_language",
                )
            },
        ),
        (
            "Facturación (AVS)",
            {
                "fields": (
                    "billing_address_line1",
                    "billing_address_line2",
                    "billing_city",
                    "billing_state",
                    "billing_postal_code",
                    "billing_country",
                )
            },
        ),
        (
            "Seguridad y Cumplimiento",
            {"fields": ("is_email_verified", "terms_accepted_at", "marketing_consent")},
        ),
        (
            "Stripe",
            {"fields": ("stripe_customer_id",)},
        ),
        (
            "Permisos",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Fechas Importantes", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
