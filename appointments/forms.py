from django.utils.translation import gettext_lazy as _
from django import forms


class AppointmentCancellationForm(forms.Form):
    reason = forms.CharField(
        label=_("Cancellation reason"),
        widget=forms.Textarea(attrs={
            "rows": 3,
            "placeholder": "Tell the clinic why you need to cancel this appointment.",
        }),
        strip=True,
    )
