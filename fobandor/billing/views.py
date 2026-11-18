import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from fobandor.billing import services
from fobandor.billing.models import SubscriptionPlan
from fobandor.users.mixins import EmailVerifiedRequiredMixin


class PricingCatalogView(ListView):
    model = SubscriptionPlan
    template_name = "billing/pricing.html"
    context_object_name = "plans"

    def get_queryset(self):
        return SubscriptionPlan.objects.filter(is_active=True).order_by("order")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["formspree_endpoint"] = settings.FORMSPREE_ENDPOINT
        return ctx


class CreateCheckoutSessionView(LoginRequiredMixin, EmailVerifiedRequiredMixin, View):
    def get(self, request, slug):
        return self.post(request, slug)

    def post(self, request, slug):
        plan = get_object_or_404(SubscriptionPlan, slug=slug, is_active=True)
        if not settings.STRIPE_SECRET_KEY or not plan.stripe_price_id:
            messages.error(request, "La pasarela de pagos no está configurada (modo test).")
            return redirect("billing:pricing")
        success_url = request.build_absolute_uri(reverse("portal:dashboard"))
        cancel_url = request.build_absolute_uri(reverse("billing:pricing"))
        session = services.create_checkout_session(request.user, plan, success_url, cancel_url)
        return redirect(session.url)


class StripeCustomerPortalView(LoginRequiredMixin, View):
    def post(self, request):
        return_url = request.build_absolute_uri(reverse("portal:dashboard"))
        session = services.create_customer_portal_session(request.user, return_url)
        return redirect(session.url)


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(require_POST, name="dispatch")
class StripeWebhookView(View):
    def post(self, request):
        payload = request.body
        sig_header = request.headers.get("Stripe-Signature", "")
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        except (ValueError, stripe.SignatureVerificationError):
            return HttpResponse(status=400)

        services.process_webhook_event(event.to_dict())
        return HttpResponse(status=200)
