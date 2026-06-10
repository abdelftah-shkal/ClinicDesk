from datetime import time
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from notifications.models import Notification
from appointments.models import Appointment, AppointmentSlot
from accounts.models import DoctorProfile
from payments.models import PaymentTransaction

User = get_user_model()


class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="patient1",
            email="patient1@example.com",
            password="password123",
            role="PATIENT",
        )

    def test_create_notification_method(self):
        notification = Notification.create_notification(
            user=self.user,
            title="Test Notification",
            message="This is a test notification message.",
            notification_type=Notification.NotificationType.APPOINTMENT,
            link="/appointments/1/",
        )
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, "Test Notification")
        self.assertEqual(notification.message, "This is a test notification message.")
        self.assertEqual(notification.notification_type, "APPOINTMENT")
        self.assertEqual(notification.link, "/appointments/1/")
        self.assertFalse(notification.is_read)
        self.assertIsNotNone(notification.created_at)
        self.assertEqual(str(notification), "Test Notification: This is a test notification message.")


class NotificationViewsTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="patient1",
            email="patient1@example.com",
            password="password123",
            role="PATIENT",
        )
        self.user2 = User.objects.create_user(
            username="patient2",
            email="patient2@example.com",
            password="password123",
            role="PATIENT",
        )
        self.n1 = Notification.create_notification(
            user=self.user1,
            title="Appointment Booked",
            message="Your appointment has been booked.",
            notification_type=Notification.NotificationType.APPOINTMENT,
        )
        self.n2 = Notification.create_notification(
            user=self.user1,
            title="Payment Received",
            message="Your payment was successful.",
            notification_type=Notification.NotificationType.PAYMENT,
        )
        self.n3 = Notification.create_notification(
            user=self.user2,
            title="Other User Notification",
            message="This should not be seen by user1.",
            notification_type=Notification.NotificationType.SYSTEM,
        )

    def test_list_view_requires_authentication(self):
        url = reverse("notifications:notification-list")
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)
        self.assertRedirects(response, f"/en/accounts/login/?next={url}")

    def test_list_view_shows_user_notifications(self):
        self.client.login(username="patient1", password="password123")
        url = reverse("notifications:notification-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Appointment Booked")
        self.assertContains(response, "Payment Received")
        self.assertNotContains(response, "Other User Notification")

    def test_mark_notification_read(self):
        self.client.login(username="patient1", password="password123")
        url = reverse("notifications:notification-mark-read", args=[self.n1.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success"})
        self.n1.refresh_from_db()
        self.assertTrue(self.n1.is_read)

    def test_mark_notification_read_unauthorized(self):
        self.client.login(username="patient2", password="password123")
        url = reverse("notifications:notification-mark-read", args=[self.n1.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_mark_all_read(self):
        self.client.login(username="patient1", password="password123")
        url = reverse("notifications:notification-mark-all-read")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success"})
        self.n1.refresh_from_db()
        self.n2.refresh_from_db()
        self.assertTrue(self.n1.is_read)
        self.assertTrue(self.n2.is_read)

    def test_unread_count(self):
        self.client.login(username="patient1", password="password123")
        url = reverse("notifications:notification-unread-count")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"count": 2})

        # Mark one read and check count again
        self.n1.is_read = True
        self.n1.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"count": 1})


class NotificationSignalsTest(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            username="patient_user",
            email="patient_user@example.com",
            password="password123",
            role="PATIENT",
        )
        self.doctor = User.objects.create_user(
            username="doctor_user",
            email="doctor_user@example.com",
            password="password123",
            role="DOCTOR",
        )
        DoctorProfile.objects.create(
            user=self.doctor,
            specialty="Cardiology",
            bio="Doctor Bio",
            consultation_fee=Decimal("150.00"),
        )
        self.slot = AppointmentSlot.objects.create(
            doctor=self.doctor,
            date=timezone.localdate(),
            start_time=time(10, 0),
            end_time=time(10, 30),
            is_booked=False,
        )
        self.receptionist = User.objects.create_user(
            username="receptionist_user",
            email="receptionist_user@example.com",
            password="password123",
            role="RECEPTIONIST",
        )

    def test_appointment_creation_triggers_notification(self):
        Notification.objects.all().delete()
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            slot=self.slot,
            status=Appointment.Status.REQUESTED,
        )
        patient_notifications = Notification.objects.filter(user=self.patient)
        self.assertEqual(patient_notifications.count(), 1)
        notif = patient_notifications.first()
        self.assertEqual(notif.notification_type, "APPOINTMENT")
        self.assertIn("booked", notif.message)
        self.assertEqual(notif.title, "Appointment Booked")

    def test_appointment_status_change_triggers_notification(self):
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            slot=self.slot,
            status=Appointment.Status.REQUESTED,
        )
        Notification.objects.all().delete()
        appointment.status = Appointment.Status.CONFIRMED
        appointment.save()
        patient_notifications = Notification.objects.filter(user=self.patient)
        self.assertEqual(patient_notifications.count(), 1)
        notif = patient_notifications.first()
        self.assertEqual(notif.title, "Appointment Confirmed")
        self.assertIn("confirmed", notif.message)

    def test_appointment_cancellation_triggers_patient_and_doctor_notifications(self):
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            slot=self.slot,
            status=Appointment.Status.REQUESTED,
        )
        Notification.objects.all().delete()
        appointment.status = Appointment.Status.CANCELLED
        appointment.save()
        patient_notifications = Notification.objects.filter(user=self.patient)
        self.assertEqual(patient_notifications.count(), 1)
        self.assertEqual(patient_notifications.first().title, "Appointment Cancelled")
        doctor_notifications = Notification.objects.filter(user=self.doctor)
        self.assertEqual(doctor_notifications.count(), 1)
        self.assertEqual(doctor_notifications.first().title, "Appointment Cancelled")

    def test_payment_success_triggers_notifications(self):
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            slot=self.slot,
            status=Appointment.Status.REQUESTED,
        )
        transaction = PaymentTransaction.objects.create(
            appointment=appointment,
            stripe_checkout_id="session_123",
            amount=Decimal("150.00"),
            status=PaymentTransaction.Status.PENDING,
        )
        Notification.objects.all().delete()
        transaction.status = PaymentTransaction.Status.PAID
        transaction.save()
        patient_notifications = Notification.objects.filter(user=self.patient)
        self.assertEqual(patient_notifications.count(), 1)
        self.assertEqual(patient_notifications.first().title, "Payment Successful")
        receptionist_notifications = Notification.objects.filter(user=self.receptionist)
        self.assertEqual(receptionist_notifications.count(), 1)
        self.assertEqual(receptionist_notifications.first().title, "Payment Received")

    def test_payment_refund_triggers_notifications(self):
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            slot=self.slot,
            status=Appointment.Status.REQUESTED,
        )
        transaction = PaymentTransaction.objects.create(
            appointment=appointment,
            stripe_checkout_id="session_123",
            amount=Decimal("150.00"),
            status=PaymentTransaction.Status.PAID,
        )
        Notification.objects.all().delete()
        transaction.status = PaymentTransaction.Status.REFUNDED
        transaction.save()
        patient_notifications = Notification.objects.filter(user=self.patient)
        self.assertEqual(patient_notifications.count(), 1)
        self.assertEqual(patient_notifications.first().title, "Payment Refunded")
        receptionist_notifications = Notification.objects.filter(user=self.receptionist)
        self.assertEqual(receptionist_notifications.count(), 1)
        self.assertEqual(receptionist_notifications.first().title, "Payment Refunded")

    def test_payment_failure_triggers_notification(self):
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            slot=self.slot,
            status=Appointment.Status.REQUESTED,
        )
        transaction = PaymentTransaction.objects.create(
            appointment=appointment,
            stripe_checkout_id="session_123",
            amount=Decimal("150.00"),
            status=PaymentTransaction.Status.PENDING,
        )
        Notification.objects.all().delete()
        transaction.status = PaymentTransaction.Status.FAILED
        transaction.save()
        patient_notifications = Notification.objects.filter(user=self.patient)
        self.assertEqual(patient_notifications.count(), 1)
        self.assertEqual(patient_notifications.first().title, "Payment Failed")


class SendRemindersCommandTest(TestCase):
    def setUp(self):
        import datetime
        self.patient = User.objects.create_user(
            username="patient_user_rem",
            email="patient_user_rem@example.com",
            password="password123",
            role="PATIENT",
        )
        self.doctor = User.objects.create_user(
            username="doctor_user_rem",
            email="doctor_user_rem@example.com",
            password="password123",
            role="DOCTOR",
        )
        DoctorProfile.objects.create(
            user=self.doctor,
            specialty="Cardiology",
            bio="Doctor Bio",
            consultation_fee=Decimal("150.00"),
        )
        # Tomorrow's slot
        self.tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        self.slot_tomorrow = AppointmentSlot.objects.create(
            doctor=self.doctor,
            date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(10, 30),
            is_booked=True,
        )
        # Today's slot (should not trigger reminder)
        self.slot_today = AppointmentSlot.objects.create(
            doctor=self.doctor,
            date=timezone.localdate(),
            start_time=time(11, 0),
            end_time=time(11, 30),
            is_booked=True,
        )

    def test_send_reminders_success(self):
        from django.core.management import call_command
        from django.core import mail
        from io import StringIO
        
        # Create appointment for tomorrow
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            slot=self.slot_tomorrow,
            status=Appointment.Status.CONFIRMED,
        )
        # Create appointment for today
        appointment_today = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            slot=self.slot_today,
            status=Appointment.Status.CONFIRMED,
        )
        
        # Clear outbox and notifications
        mail.outbox = []
        Notification.objects.filter(notification_type=Notification.NotificationType.REMINDER).delete()
        
        # Call command
        out = StringIO()
        call_command("send_reminders", stdout=out)
        
        # Check command output
        output_str = out.getvalue()
        self.assertIn("Found 1 active appointments for tomorrow", output_str)
        self.assertIn("Successfully sent reminder", output_str)
        
        # Check mail sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.patient.email])
        self.assertIn("Appointment Reminder", email.subject)
        
        # Check notification created
        reminders = Notification.objects.filter(
            user=self.patient,
            notification_type=Notification.NotificationType.REMINDER
        )
        self.assertEqual(reminders.count(), 1)
        self.assertEqual(reminders.first().link, f"/appointments/my/?id={appointment.id}")

    def test_send_reminders_idempotency(self):
        from django.core.management import call_command
        from django.core import mail
        from io import StringIO
        
        # Create appointment for tomorrow
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            slot=self.slot_tomorrow,
            status=Appointment.Status.CONFIRMED,
        )
        
        # Clear mail outbox
        mail.outbox = []
        Notification.objects.filter(notification_type=Notification.NotificationType.REMINDER).delete()
        
        # Call once
        out1 = StringIO()
        call_command("send_reminders", stdout=out1)
        self.assertEqual(Notification.objects.filter(notification_type=Notification.NotificationType.REMINDER).count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        
        # Call twice
        out2 = StringIO()
        call_command("send_reminders", stdout=out2)
        # Should not increase
        self.assertEqual(Notification.objects.filter(notification_type=Notification.NotificationType.REMINDER).count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Skipping appointment", out2.getvalue())

    def test_send_reminders_dry_run(self):
        from django.core.management import call_command
        from django.core import mail
        from io import StringIO
        
        # Create appointment for tomorrow
        appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            slot=self.slot_tomorrow,
            status=Appointment.Status.CONFIRMED,
        )
        
        mail.outbox = []
        Notification.objects.filter(notification_type=Notification.NotificationType.REMINDER).delete()
        
        out = StringIO()
        call_command("send_reminders", dry_run=True, stdout=out)
        
        self.assertIn("[Dry-run] Would send reminder", out.getvalue())
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(Notification.objects.filter(notification_type=Notification.NotificationType.REMINDER).count(), 0)

