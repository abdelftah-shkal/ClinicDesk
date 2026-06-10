from django.contrib import admin
from .models import PaymentTransaction, Invoice, InvoicePayment


admin.site.register(PaymentTransaction)
admin.site.register(Invoice)
admin.site.register(InvoicePayment)

