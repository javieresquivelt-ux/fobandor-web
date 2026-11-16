from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("", views.CustomerDashboardView.as_view(), name="dashboard"),
    path("onboarding/", views.OnboardingAVSView.as_view(), name="onboarding-avs"),
]
