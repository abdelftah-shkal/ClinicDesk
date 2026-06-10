from django.utils.translation import gettext_lazy as _
import logging
from decimal import Decimal
from datetime import timedelta

import stripe

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from appointments.models import Appointment, AppointmentSlot
from .models import PaymentTransaction

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

REFUND_PERCENTAGE = Decimal("0.80")


def process_appointment_refund(appointment, refund_percentage=None):
    if refund_percentage is None:
        refund_percentage = REFUND_PERCENTAGE

    try:
        original_txn = PaymentTransaction.objects.get(
            appointment=appointment,
            status=PaymentTransaction.Status.PAID,
        )
    except PaymentTransaction.DoesNotExist:
        return None

    refund_amount = (original_txn.amount * refund_percentage).quantize(Decimal("0.01"))
    deducted_amount = original_txn.amount - refund_amount

    checkout_session = stripe.checkout.Session.retrieve(original_txn.stripe_checkout_id)
    if checkout_session.payment_intent:
        stripe.Refund.create(
            payment_intent=checkout_session.payment_intent,
            amount=int(refund_amount * 100),
        )

    PaymentTransaction.objects.create(
        appointment=appointment,
        stripe_checkout_id=f"refund_{original_txn.stripe_checkout_id}",
        amount=refund_amount,
        status=PaymentTransaction.Status.REFUNDED,
        paid_at=now(),
    )

    return {
        "refunded_amount": refund_amount,
        "deducted_amount": deducted_amount,
    }


@login_required
def CreateCheckoutSessionView(request, appointment_id):
    appointment = get_object_or_404(
        Appointment.objects.select_related("slot", "doctor", "doctor__doctor_profile"),
        id=appointment_id,
        patient=request.user,
        status=Appointment.Status.AWAITING_PAYMENT,
    )

    try:
        with transaction.atomic():
            appointment = (
                Appointment.objects.select_for_update()
                .select_related("slot", "doctor", "doctor__doctor_profile")
                .get(pk=appointment.pk)
            )
            slot = AppointmentSlot.objects.select_for_update().get(pk=appointment.slot_id)

            if slot.is_booked:
                raise ValidationError(_("The session is already booked by another user."))

            appointment.full_clean()
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
        return redirect("patient-booking")

    slot = appointment.slot
    consultation_fee = getattr(getattr(appointment.doctor, "doctor_profile", None), "consultation_fee", Decimal("0.00"))

    if consultation_fee <= 0:
        messages.error(request, _("This doctor does not have a valid consultation fee."))
        return redirect("patient-booking")

    success_url = request.build_absolute_uri("/payments/success/") + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = request.build_absolute_uri(f"/payments/cancel/{appointment.id}/")

    doctor_name = str(slot.doctor.get_full_name() or slot.doctor.username)
    slot_date = slot.date.strftime("%Y-%m-%d")
    slot_time = slot.start_time.strftime("%H:%M")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "egp",
                    "unit_amount": int(consultation_fee * 100),
                    "product_data": {
                        "name": f"Consultation with {doctor_name}",
                        "description": f"Appointment on {slot_date} at {slot_time} - EGP {consultation_fee}",
                    },
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        expires_at=int((now() + timedelta(minutes=30)).timestamp()),
        metadata={
            "appointment_id": str(appointment.id),
        },
    )
    
    PaymentTransaction.objects.get_or_create(
        appointment=appointment,
        defaults={
            'stripe_checkout_id': session.id,
            'amount': consultation_fee,
            'status': PaymentTransaction.Status.PENDING,
        }
    )

    return redirect(session.url)


@csrf_exempt
@require_POST
def StripeWebhookView(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        return HttpResponseBadRequest("Invalid payload")
    except stripe.error.SignatureVerificationError:
        return HttpResponseBadRequest("Invalid signature")

    if event.type == "checkout.session.completed":
        session = event.data.object
        appointment_id = getattr(session.metadata, "appointment_id", None)

        if not appointment_id:
            return HttpResponse(status=200)

        with transaction.atomic():
            try:
                appointment = Appointment.objects.select_for_update().get(id=appointment_id)
            except Appointment.DoesNotExist:
                return HttpResponse(status=200)

            # Already confirmed (duplicate webhook or same user paying from multiple tabs)
            if appointment.status == Appointment.Status.CONFIRMED:
                if session.payment_intent:
                    stripe.Refund.create(payment_intent=session.payment_intent)
                return HttpResponse(status=200)

            slot = AppointmentSlot.objects.select_for_update().get(id=appointment.slot_id)
            
            # Retrieve the transaction
            try:
                txn = PaymentTransaction.objects.get(
                    appointment=appointment,
                    status=PaymentTransaction.Status.PENDING,
                )
            except PaymentTransaction.DoesNotExist:
                txn = None

            if slot.is_booked:
                # Slot was taken by another user who paid first
                if session.payment_intent:
                    stripe.Refund.create(payment_intent=session.payment_intent)
                
                appointment.status = Appointment.Status.CANCELLED
                appointment.save(update_fields=["status"])
                if txn:
                    txn.status = PaymentTransaction.Status.FAILED
                    txn.save(update_fields=["status"])
                    
                return HttpResponse(status=200)

            # Slot is free! Book it.
            slot.is_booked = True
            slot.save(update_fields=["is_booked"])

            appointment.status = Appointment.Status.CONFIRMED
            appointment.save(update_fields=["status"])

            if txn:
                txn.stripe_checkout_id = session.id
                txn.status = PaymentTransaction.Status.PAID
                txn.paid_at = now()
                txn.save(update_fields=["stripe_checkout_id", "status", "paid_at"])

            # Legacy cleanup for any rows that predate the uniqueness guard.
            for other_appointment in (
                Appointment.objects.select_for_update()
                .filter(slot=slot, status=Appointment.Status.AWAITING_PAYMENT)
                .exclude(id=appointment.id)
            ):
                other_appointment.status = Appointment.Status.CANCELLED
                other_appointment.save(update_fields=["status", "active_slot"])

    elif event.type in ["checkout.session.expired", "checkout.session.async_payment_failed"]:
        session = event.data.object
        appointment_id = getattr(session.metadata, "appointment_id", None)
        
        if appointment_id:
            with transaction.atomic():
                try:
                    appointment = Appointment.objects.select_for_update().get(id=appointment_id)
                    appointment.status = Appointment.Status.CANCELLED
                    appointment.save(update_fields=["status"])
                    
                    PaymentTransaction.objects.filter(appointment=appointment).update(
                        status=PaymentTransaction.Status.FAILED
                    )
                except Appointment.DoesNotExist:
                    pass

    return HttpResponse(status=200)


@login_required
def PaymentSuccessView(request):
    return render(request, "payments/success.html", {
        "dashboard_title": "Payment Successful",
        "dashboard_subtitle": "Your appointment has been confirmed.",
    })


@login_required
def PaymentCancelView(request, appointment_id=None):
    if appointment_id:
        with transaction.atomic():
            try:
                appointment = Appointment.objects.select_for_update().get(
                    id=appointment_id,
                    patient=request.user,
                    status=Appointment.Status.AWAITING_PAYMENT,
                )
                appointment.status = Appointment.Status.CANCELLED
                appointment.save(update_fields=["status"])
                PaymentTransaction.objects.filter(
                    appointment=appointment,
                    status=PaymentTransaction.Status.PENDING,
                ).update(status=PaymentTransaction.Status.FAILED)
            except Appointment.DoesNotExist:
                pass

    return render(request, "payments/cancel.html", {
        "dashboard_title": "Payment Cancelled",
        "dashboard_subtitle": "Your appointment was not confirmed.",
    })


@login_required
def PatientPaymentHistoryView(request):
    payments_list = PaymentTransaction.objects.filter(
        appointment__patient=request.user
    ).select_related("appointment", "appointment__doctor", "appointment__slot").order_by("-created_at")
    
    paginator = Paginator(payments_list, 10)  # Show 10 payments per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    return render(request, "payments/history.html", {
        "payments": page_obj,
        "current_section": "payments",
        "dashboard_title": "Payment History",
        "dashboard_subtitle": "Review your bills, receipts, and refund records.",
    })


from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from .models import Invoice, InvoicePayment
from .forms import InvoiceCreateForm, RecordPaymentForm


class ReceptionistRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'RECEPTIONIST':
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class InvoiceCreateView(LoginRequiredMixin, ReceptionistRequiredMixin, View):
    def get(self, request, appointment_id):
        appointment = get_object_or_404(Appointment, pk=appointment_id)
        if hasattr(appointment, 'invoice'):
            messages.warning(request, _("An invoice already exists for this appointment: {appointment.invoice.invoice_number}"))
            return redirect('invoice-detail', pk=appointment.invoice.pk)
        
        consultation_fee = getattr(getattr(appointment.doctor, "doctor_profile", None), "consultation_fee", Decimal("0.00"))
        form = InvoiceCreateForm(initial={'total_amount': consultation_fee})
        
        return render(request, "payments/invoice_create.html", {
            "form": form,
            "appointment": appointment,
            "current_section": "billing",
        })

    def post(self, request, appointment_id):
        appointment = get_object_or_404(Appointment, pk=appointment_id)
        if hasattr(appointment, 'invoice'):
            messages.warning(request, _("An invoice already exists for this appointment: {appointment.invoice.invoice_number}"))
            return redirect('invoice-detail', pk=appointment.invoice.pk)
        
        form = InvoiceCreateForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.appointment = appointment
            invoice.patient = appointment.patient
            invoice.save()
            messages.success(request, _("Invoice {invoice.invoice_number} created successfully."))
            return redirect('invoice-detail', pk=invoice.pk)
        
        return render(request, "payments/invoice_create.html", {
            "form": form,
            "appointment": appointment,
            "current_section": "billing",
        })


class InvoiceDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        user = request.user
        if user.role not in ('RECEPTIONIST', 'ADMIN') and invoice.patient != user:
            return redirect('home')
        
        payments = invoice.payments.all().order_by("-created_at")
        form = RecordPaymentForm(invoice=invoice)
        
        return render(request, "payments/invoice_detail.html", {
            "invoice": invoice,
            "payments": payments,
            "form": form,
            "current_section": "billing",
        })


class InvoicePrintView(LoginRequiredMixin, View):
    def get(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        user = request.user
        if user.role not in ('RECEPTIONIST', 'ADMIN') and invoice.patient != user:
            return redirect('home')
        
        return render(request, "payments/invoice_print.html", {
            "invoice": invoice,
        })


class RecordPaymentView(LoginRequiredMixin, ReceptionistRequiredMixin, View):
    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        form = RecordPaymentForm(request.POST, invoice=invoice)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.received_by = request.user
            payment.save()
            messages.success(request, _("Payment of EGP {payment.amount} recorded successfully."))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, _("{field.capitalize()}: {error}"))
        return redirect("invoice-detail", pk=invoice.pk)


class BillingDashboardView(LoginRequiredMixin, ReceptionistRequiredMixin, View):
    def get(self, request):
        active_invoices = Invoice.objects.exclude(status=Invoice.Status.CANCELLED)
        total_invoiced = active_invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        total_collected = active_invoices.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')
        outstanding_balance = total_invoiced - total_collected
        
        invoices = Invoice.objects.select_related('patient', 'appointment', 'appointment__slot', 'appointment__doctor').order_by('-created_at')
        
        # Apply filters
        q = request.GET.get('q', '').strip()
        if q:
            search_filter = (
                Q(patient__first_name__icontains=q)
                | Q(patient__last_name__icontains=q)
                | Q(patient__username__icontains=q)
                | Q(patient__email__icontains=q)
                | Q(patient__phone_number__icontains=q)
                | Q(invoice_number__icontains=q)
            )
            if q.isdigit():
                search_filter |= Q(patient__id=int(q))
            invoices = invoices.filter(search_filter)
            
        status = request.GET.get('status', '').strip()
        if status:
            invoices = invoices.filter(status=status)
            
        start_date = request.GET.get('start_date', '').strip()
        if start_date:
            invoices = invoices.filter(created_at__date__gte=start_date)
            
        end_date = request.GET.get('end_date', '').strip()
        if end_date:
            invoices = invoices.filter(created_at__date__lte=end_date)
            
        paginator = Paginator(invoices, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        return render(request, "payments/billing_dashboard.html", {
            "invoices": page_obj,
            "page_obj": page_obj,
            "total_invoiced": total_invoiced,
            "total_collected": total_collected,
            "outstanding_balance": outstanding_balance,
            "search_query": q,
            "selected_status": status,
            "start_date": start_date,
            "end_date": end_date,
            "status_choices": Invoice.Status.choices,
            "current_section": "billing",
        })

