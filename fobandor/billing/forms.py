from django import forms

from fobandor.billing.models import SubscriptionPlan


class SubscriptionPlanForm(forms.ModelForm):
    features_es_text = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 6}),
        required=False,
        label="Características (ES, una por línea)",
    )
    features_en_text = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 6}),
        required=False,
        label="Features (EN, one per line)",
    )

    class Meta:
        model = SubscriptionPlan
        fields = [
            "name_es", "name_en", "subtitle_es", "subtitle_en",
            "desc_es", "desc_en", "price_usd", "stripe_price_id",
            "min_commitment_months", "target_audience_es", "target_audience_en",
            "disclaimer_es", "disclaimer_en", "order_type", "order",
            "is_active", "is_highlighted",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["features_es_text"].initial = "\n".join(self.instance.features_es or [])
            self.fields["features_en_text"].initial = "\n".join(self.instance.features_en or [])

    def _clean_features(self, field_name):
        value = self.cleaned_data.get(field_name, "")
        return [line.strip() for line in value.splitlines() if line.strip()]

    def clean_features_es_text(self):
        return self._clean_features("features_es_text")

    def clean_features_en_text(self):
        return self._clean_features("features_en_text")

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.features_es = self.cleaned_data["features_es_text"]
        instance.features_en = self.cleaned_data["features_en_text"]
        if commit:
            instance.save()
        return instance
