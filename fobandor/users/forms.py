from django import forms

from fobandor.users.models import User

_INPUT_CLASS = (
    "w-full rounded-lg border border-gray-300 dark:border-white/20 "
    "px-3 py-2 bg-transparent"
)


def _text_input(placeholder=None):
    attrs = {"class": _INPUT_CLASS}
    if placeholder:
        attrs["placeholder"] = placeholder
    return forms.TextInput(attrs=attrs)


class AVSOnboardingForm(forms.ModelForm):
    """Captura la dirección de facturación y teléfono E.164 para el AVS de Stripe."""

    class Meta:
        model = User
        fields = [
            "billing_address_line1",
            "billing_address_line2",
            "billing_city",
            "billing_state",
            "billing_postal_code",
            "billing_country",
            "phone",
        ]
        widgets = {
            "billing_address_line1": _text_input(),
            "billing_address_line2": _text_input(),
            "billing_city": _text_input(),
            "billing_state": _text_input(),
            "billing_postal_code": _text_input(),
            "billing_country": _text_input("US"),
            "phone": _text_input("+14075551234"),
        }
