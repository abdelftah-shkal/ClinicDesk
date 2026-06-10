import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from appointments.models import Appointment
from notifications.models import Notification


class Command(BaseCommand):
    help = "Send email and in-app reminders for tomorrow's appointments"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what reminders would be sent without actually sending them or creating notifications",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        
        appointments = Appointment.objects.filter(
            slot__date=tomorrow,
            status__in=["REQUESTED", "CONFIRMED"]
        ).select_related("patient", "doctor", "slot")
        
        self.stdout.write(f"Found {appointments.count()} active appointments for tomorrow ({tomorrow}).")
        
        reminders_sent = 0
        reminders_skipped = 0
        
        for appointment in appointments:
            link = f"/appointments/my/?id={appointment.id}"
            
            # Idempotency check: see if a reminder notification already exists for this appointment
            already_sent = Notification.objects.filter(
                user=appointment.patient,
                notification_type=Notification.NotificationType.REMINDER,
                link=link
            ).exists()
            
            if already_sent:
                reminders_skipped += 1
                self.stdout.write(f"Skipping appointment {appointment.id} - reminder already sent.")
                continue
            
            patient_name = appointment.patient.get_full_name() or appointment.patient.username
            doctor_name = appointment.doctor.get_full_name() or appointment.doctor.username
            specialty = "Specialist"
            if hasattr(appointment.doctor, "doctor_profile") and appointment.doctor.doctor_profile:
                specialty = appointment.doctor.doctor_profile.specialty
            
            date_str = appointment.slot.date.strftime("%B %d, %Y")
            time_str = appointment.slot.start_time.strftime("%I:%M %p")
            
            site_url = getattr(settings, "SITE_URL", "http://localhost:8000")
            appointment_url = f"{site_url.rstrip('/')}{link}"
            
            if dry_run:
                self.stdout.write(
                    f"[Dry-run] Would send reminder to {appointment.patient.email} for appointment with Dr. {doctor_name} at {time_str}"
                )
                reminders_sent += 1
                continue
                
            # Render and send HTML email
            context = {
                "patient_name": patient_name,
                "doctor_name": doctor_name,
                "specialty": specialty,
                "date": date_str,
                "time": time_str,
                "appointment_url": appointment_url,
            }
            
            html_content = render_to_string("emails/appointment_reminder.html", context)
            subject = f"Appointment Reminder: Dr. {doctor_name} on {date_str}"
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=f"Hello {patient_name}, this is a reminder for your appointment on {date_str} at {time_str}.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[appointment.patient.email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            # Create in-app Notification
            Notification.create_notification(
                user=appointment.patient,
                title="Appointment Reminder",
                message=f"Reminder: You have an appointment with Dr. {doctor_name} tomorrow, {date_str} at {time_str}.",
                notification_type=Notification.NotificationType.REMINDER,
                link=link,
            )
            
            reminders_sent += 1
            self.stdout.write(f"Successfully sent reminder for appointment {appointment.id} to {appointment.patient.email}.")
            
        self.stdout.write(
            self.style.SUCCESS(
                f"Completed. Reminders sent/processed: {reminders_sent}, Skipped: {reminders_skipped} (Dry-run: {dry_run})"
            )
        )
