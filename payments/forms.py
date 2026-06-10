from django.utils.translation import gettext_lazy as _
from django import forms
from django.core.exceptions import ValidationError
from .models import Invoice, InvoicePayment


class InvoiceCreateForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["total_amount", "notes"]
        widgets = {
            "total_amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "0.00"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Enter any billing notes..."}),
        }

    def clean_total_amount(self):
        amount = self.cleaned_data.get("total_amount")
        if amount is not None and amount <= 0:
            raise ValidationError(_("Total amount must be greater than zero."))
        return amount


class RecordPaymentForm(forms.ModelForm):
    class Meta:
        model = InvoicePayment
        fields = ["amount", "payment_method", "notes"]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "0.00"}),
            "payment_method": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Enter payment details..."}),
        }

    def __init__(self, *args, **kwargs):
        self.invoice = kwargs.pop("invoice", None)
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount <= 0:
            raise ValidationError(_("Payment amount must be greater than zero."))
        if self.invoice and amount is not None and amount > self.invoice.balance_due:
            raise ValidationError(_("Amount cannot exceed the remaining balance due of EGP {self.invoice.balance_due:.2f}."))
        return amount
