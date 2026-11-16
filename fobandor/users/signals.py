from allauth.account.signals import email_confirmed
from django.dispatch import receiver


@receiver(email_confirmed)
def mark_user_email_verified(sender, request, email_address, **kwargs):
    """Marca el CustomUser como verificado cuando allauth confirma el email (ADR-006)."""
    user = getattr(email_address, "user", None)
    if user is not None and not user.is_email_verified:
        user.is_email_verified = True
        user.save(update_fields=["is_email_verified"])
