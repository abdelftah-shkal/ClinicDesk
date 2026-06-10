from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from appointments.models import Appointment
from payments.models import PaymentTransaction
from .services import (
    notify_appointment_created,
    notify_appointment_status_changed,
    notify_appointment_cancelled,
    notify_payment_completed,
    notify_payment_refunded,
    notify_payment_failed,
)

@receiver(pre_save, sender=Appointment)
def appointment_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            original = Appointment.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except Appointment.DoesNotExist:
            instance._original_status = None
    else:
        instance._original_status = None

@receiver(post_save, sender=Appointment)
def appointment_post_save(sender, instance, created, **kwargs):
    if created:
        notify_appointment_created(instance)
    else:
        old_status = getattr(instance, "_original_status", None)
        new_status = instance.status
        if old_status and old_status != new_status:
            if new_status == Appointment.Status.CANCELLED:
                notify_appointment_cancelled(instance)
            else:
                notify_appointment_status_changed(instance, old_status, new_status)

@receiver(pre_save, sender=PaymentTransaction)
def payment_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            original = PaymentTransaction.objects.get(pk=instance.pk)
            instance._original_status = original.status
        except PaymentTransaction.DoesNotExist:
            instance._original_status = None
    else:
        instance._original_status = None

@receiver(post_save, sender=PaymentTransaction)
def payment_post_save(sender, instance, created, **kwargs):
    old_status = getattr(instance, "_original_status", None)
    new_status = instance.status
    if created or (old_status != new_status):
        if new_status == PaymentTransaction.Status.PAID:
            notify_payment_completed(instance)
        elif new_status == PaymentTransaction.Status.REFUNDED:
            notify_payment_refunded(instance)
        elif new_status == PaymentTransaction.Status.FAILED:
            notify_payment_failed(instance)
