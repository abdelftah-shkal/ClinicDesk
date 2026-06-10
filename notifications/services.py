from django.urls import reverse
from django.contrib.auth import get_user_model
from notifications.models import Notification

User = get_user_model()


def format_date(d):
    if not d:
        return ""
    if isinstance(d, str):
        return d
    try:
        return d.strftime("%Y-%m-%d")
    except AttributeError:
        return str(d)


def format_time(t):
    if not t:
        return ""
    if isinstance(t, str):
        if len(t) >= 5:
            return t[:5]
        return t
    try:
        return t.strftime("%H:%M")
    except AttributeError:
        return str(t)


def notify_appointment_created(appointment):
    """
    Notifies the patient when a new appointment is booked.
    """
    doctor_name = appointment.doctor.get_full_name() or appointment.doctor.username
    date_str = format_date(appointment.slot.date)
    time_str = format_time(appointment.slot.start_time)

    Notification.create_notification(
        user=appointment.patient,
        title="Appointment Booked",
        message=f"Your appointment with Dr. {doctor_name} has been booked for {date_str} at {time_str}.",
        notification_type=Notification.NotificationType.APPOINTMENT,
        link=reverse("my-appointments"),
    )


def notify_appointment_status_changed(appointment, old_status, new_status):
    """
    Notifies the patient on appointment status updates.
    """
    doctor_name = appointment.doctor.get_full_name() or appointment.doctor.username
    date_str = format_date(appointment.slot.date)
    time_str = format_time(appointment.slot.start_time)

    status_display = appointment.get_status_display()

    if new_status == "CONFIRMED":
        title = "Appointment Confirmed"
        message = f"Your appointment with Dr. {doctor_name} on {date_str} at {time_str} is confirmed."
    elif new_status == "CHECKED_IN":
        title = "Checked In"
        message = f"You have successfully checked in for your appointment with Dr. {doctor_name}."
    elif new_status == "COMPLETED":
        title = "Appointment Completed"
        message = f"Your consultation with Dr. {doctor_name} has been completed. You can view your record online."
    else:
        title = "Appointment Status Updated"
        message = f"Your appointment with Dr. {doctor_name} status was updated to {status_display}."

    Notification.create_notification(
        user=appointment.patient,
        title=title,
        message=message,
        notification_type=Notification.NotificationType.APPOINTMENT,
        link=reverse("my-appointments"),
    )


def notify_appointment_cancelled(appointment):
    """
    Notifies both patient and doctor when an appointment is cancelled.
    """
    doctor_name = appointment.doctor.get_full_name() or appointment.doctor.username
    patient_name = appointment.patient.get_full_name() or appointment.patient.username
    date_str = format_date(appointment.slot.date)
    time_str = format_time(appointment.slot.start_time)

    # Notify patient
    Notification.create_notification(
        user=appointment.patient,
        title="Appointment Cancelled",
        message=f"Your appointment with Dr. {doctor_name} on {date_str} at {time_str} has been cancelled.",
        notification_type=Notification.NotificationType.APPOINTMENT,
        link=reverse("my-appointments"),
    )

    # Notify doctor
    Notification.create_notification(
        user=appointment.doctor,
        title="Appointment Cancelled",
        message=f"Appointment for patient {patient_name} on {date_str} at {time_str} has been cancelled.",
        notification_type=Notification.NotificationType.APPOINTMENT,
        link=reverse("emr:daily-queue"),
    )


def notify_payment_completed(transaction):
    """
    Notifies the patient and all receptionists when a payment transaction is successful.
    """
    appointment = transaction.appointment
    doctor_name = appointment.doctor.get_full_name() or appointment.doctor.username
    patient_name = appointment.patient.get_full_name() or appointment.patient.username

    # Notify patient
    Notification.create_notification(
        user=appointment.patient,
        title="Payment Successful",
        message=f"Your payment of ${transaction.amount} for appointment with Dr. {doctor_name} was received successfully.",
        notification_type=Notification.NotificationType.PAYMENT,
        link=reverse("patient-payments"),
    )

    # Notify receptionists
    receptionists = User.objects.filter(role="RECEPTIONIST")
    for receptionist in receptionists:
        Notification.create_notification(
            user=receptionist,
            title="Payment Received",
            message=f"Payment of ${transaction.amount} received for patient {patient_name}'s appointment with Dr. {doctor_name}.",
            notification_type=Notification.NotificationType.PAYMENT,
            link=reverse("dashboard"),
        )


def notify_payment_refunded(transaction):
    """
    Notifies the patient and all receptionists when a payment transaction is refunded.
    """
    appointment = transaction.appointment
    doctor_name = appointment.doctor.get_full_name() or appointment.doctor.username
    patient_name = appointment.patient.get_full_name() or appointment.patient.username

    # Notify patient
    Notification.create_notification(
        user=appointment.patient,
        title="Payment Refunded",
        message=f"Your payment of ${transaction.amount} for appointment with Dr. {doctor_name} has been refunded.",
        notification_type=Notification.NotificationType.PAYMENT,
        link=reverse("patient-payments"),
    )

    # Notify receptionists
    receptionists = User.objects.filter(role="RECEPTIONIST")
    for receptionist in receptionists:
        Notification.create_notification(
            user=receptionist,
            title="Payment Refunded",
            message=f"Payment of ${transaction.amount} was refunded for patient {patient_name}'s appointment with Dr. {doctor_name}.",
            notification_type=Notification.NotificationType.PAYMENT,
            link=reverse("dashboard"),
        )


def notify_payment_failed(transaction):
    """
    Notifies the patient when a payment transaction fails.
    """
    appointment = transaction.appointment
    doctor_name = appointment.doctor.get_full_name() or appointment.doctor.username

    Notification.create_notification(
        user=appointment.patient,
        title="Payment Failed",
        message=f"Your payment of ${transaction.amount} for appointment with Dr. {doctor_name} has failed.",
        notification_type=Notification.NotificationType.PAYMENT,
        link=reverse("patient-payments"),
    )
