import logging

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

logger = logging.getLogger(__name__)


class CustomAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return True

    def send_mail(self, template_prefix, email, context):
        """Blindaje resiliente contra fallos SMTP (ADR-021).

        Captura excepciones de red/SMTP para que nunca propaguen un HTTP 500
        al usuario. El fallo queda registrado en el log de advertencia.
        """
        try:
            super().send_mail(template_prefix, email, context)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "SMTP send_mail failed for %s — %s: %s",
                email,
                type(exc).__name__,
                exc,
            )


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Auto-verifica cuentas conectadas vía Google OAuth 2.0 (ADR-008)."""

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        if sociallogin.account.provider == "google" and not user.is_email_verified:
            user.is_email_verified = True
            user.save(update_fields=["is_email_verified"])
        return user
