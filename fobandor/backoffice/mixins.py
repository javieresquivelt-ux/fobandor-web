from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.urls import reverse


class StaffRequiredMixin(AccessMixin):
    """Permite el acceso solo a usuarios autenticados con is_staff=True."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_staff:
            return redirect(reverse('core:home'))
        return super().dispatch(request, *args, **kwargs)
