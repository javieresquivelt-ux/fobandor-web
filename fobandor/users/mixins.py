from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _


class EmailVerifiedRequiredMixin(AccessMixin):
    """Bloquea el acceso a Checkout si el usuario no tiene email verificado (ADR-006)."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_email_verified:
            messages.warning(request, _("Debes verificar tu correo antes de contratar un plan."))
            return redirect("account_email")
        return super().dispatch(request, *args, **kwargs)
