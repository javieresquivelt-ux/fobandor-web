from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return True


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Auto-verifica cuentas conectadas vía Google OAuth 2.0 (ADR-008)."""

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        if sociallogin.account.provider == "google" and not user.is_email_verified:
            user.is_email_verified = True
            user.save(update_fields=["is_email_verified"])
        return user
