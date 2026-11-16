from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("", views.PricingCatalogView.as_view(), name="pricing"),
    path("checkout/<slug:slug>/", views.CreateCheckoutSessionView.as_view(), name="checkout"),
    path("portal/", views.StripeCustomerPortalView.as_view(), name="portal"),
]
