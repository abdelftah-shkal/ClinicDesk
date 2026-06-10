from django.urls import path
from .views import (
    CreateCheckoutSessionView,
    StripeWebhookView,
    PaymentSuccessView,
    PaymentCancelView,
    PatientPaymentHistoryView,
    InvoiceCreateView,
    InvoiceDetailView,
    InvoicePrintView,
    RecordPaymentView,
    BillingDashboardView,
)

urlpatterns = [
    path("history/", PatientPaymentHistoryView, name="patient-payments"),
    path("checkout/<int:appointment_id>/", CreateCheckoutSessionView, name="stripe-checkout"),
    path("webhook/", StripeWebhookView, name="stripe-webhook"),
    path("success/", PaymentSuccessView, name="payment-success"),
    path("cancel/", PaymentCancelView, name="payment-cancel"),
    path("cancel/<int:appointment_id>/", PaymentCancelView, name="payment-cancel-appointment"),
    path("invoice/create/<int:appointment_id>/", InvoiceCreateView.as_view(), name="invoice-create"),
    path("invoice/<int:pk>/", InvoiceDetailView.as_view(), name="invoice-detail"),
    path("invoice/<int:pk>/print/", InvoicePrintView.as_view(), name="invoice-print"),
    path("invoice/<int:pk>/pay/", RecordPaymentView.as_view(), name="record-payment"),
    path("billing/", BillingDashboardView.as_view(), name="billing-dashboard"),
]

