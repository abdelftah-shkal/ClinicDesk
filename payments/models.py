from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class PaymentTransaction(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"
        FAILED = "FAILED", "Failed"
        REFUNDED = "REFUNDED", "Refunded"

    appointment = models.ForeignKey(
        "appointments.Appointment",
        on_delete=models.CASCADE,
        related_name="payment_transactions",
    )
    stripe_checkout_id = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.appointment} - {self.status}"


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ISSUED = "ISSUED", "Issued"
        PARTIALLY_PAID = "PARTIALLY_PAID", "Partially Paid"
        PAID = "PAID", "Paid"
        CANCELLED = "CANCELLED", "Cancelled"

    appointment = models.OneToOneField(
        "appointments.Appointment",
        on_delete=models.CASCADE,
        related_name="invoice",
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    invoice_number = models.CharField(max_length=50, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ISSUED,
    )
    issued_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def balance_due(self):
        return self.total_amount - self.paid_amount

    def generate_invoice_number(self):
        today_str = timezone.localtime(timezone.now()).strftime("%Y%m%d")
        prefix = f"INV-{today_str}-"
        today_invoices = self.__class__.objects.filter(invoice_number__startswith=prefix)
        if today_invoices.exists():
            numbers = []
            for inv in today_invoices:
                parts = inv.invoice_number.split("-")
                if len(parts) == 3:
                    try:
                        numbers.append(int(parts[2]))
                    except ValueError:
                        pass
            next_seq = max(numbers) + 1 if numbers else 1
        else:
            next_seq = 1
        return f"{prefix}{next_seq:04d}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        if self.status != self.Status.DRAFT and not self.issued_at:
            self.issued_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number} - {self.patient}"


class InvoicePayment(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = "CASH", "Cash"
        CARD = "CARD", "Card"
        STRIPE = "STRIPE", "Stripe"
        OTHER = "OTHER", "Other"

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
    )
    notes = models.TextField(blank=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_payments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        invoice = self.invoice
        total_paid = invoice.payments.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        invoice.paid_amount = total_paid

        if invoice.paid_amount >= invoice.total_amount:
            invoice.status = Invoice.Status.PAID
        elif invoice.paid_amount > 0:
            invoice.status = Invoice.Status.PARTIALLY_PAID
        elif invoice.status in (Invoice.Status.PARTIALLY_PAID, Invoice.Status.PAID):
            invoice.status = Invoice.Status.ISSUED

        invoice.save(update_fields=['paid_amount', 'status'])

    def __str__(self):
        return f"Payment {self.id} for {self.invoice.invoice_number} - EGP {self.amount}"

