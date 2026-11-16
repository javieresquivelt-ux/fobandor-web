from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView, UpdateView

from fobandor.billing.models import CustomerSubscription
from fobandor.fulfillment.models import FulfillmentOrder
from fobandor.users.forms import AVSOnboardingForm


class CustomerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "portal/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["subscription"] = (
            CustomerSubscription.objects.filter(user=user)
            .select_related("plan").order_by("-created_at").first()
        )
        ctx["orders"] = FulfillmentOrder.objects.filter(user=user).order_by("-created_at")
        ctx["active_order"] = (
            ctx["orders"].filter(status__in=["PENDIENTE_PRODUCCION", "EN_PROCESO"]).first()
        )
        ctx["needs_onboarding"] = not (
            user.billing_address_line1 and user.billing_city and user.billing_country and user.phone
        )
        return ctx


class OnboardingAVSView(LoginRequiredMixin, UpdateView):
    template_name = "portal/onboarding_avs.html"
    form_class = AVSOnboardingForm
    success_url = reverse_lazy("portal:dashboard")

    def get_object(self, queryset=None):
        return self.request.user
