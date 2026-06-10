from datetime import date, time

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import CustomUser, PatientProfile
from appointments.models import Appointment, AppointmentSlot


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ReceptionPatientCrudTests(TestCase):
    def setUp(self):
        self.receptionist = CustomUser.objects.create_user(
            username="reception",
            email="reception@example.com",
            password="pass12345",
            role=CustomUser.Role.RECEPTIONIST,
        )
        self.patient = CustomUser.objects.create_user(
            username="patient1",
            email="patient1@example.com",
            password="pass12345",
            first_name="Nora",
            last_name="Ali",
            phone_number="01000000001",
            role=CustomUser.Role.PATIENT,
        )
        self.profile = PatientProfile.objects.create(
            user=self.patient,
            date_of_birth=date(1995, 4, 12),
            blood_type="O+",
            gender="FEMALE",
            allergies="Penicillin",
            medical_history="Asthma",
            address="Mansoura",
            emergency_contact_name="Hana Ali",
            emergency_contact_phone="01000000002",
        )

    def test_patient_list_requires_receptionist(self):
        response = self.client.get(reverse("reception:patient-list"))
        self.assertEqual(response.status_code, 302)

        self.client.force_login(self.patient)
        response = self.client.get(reverse("reception:patient-list"))
        self.assertRedirects(response, reverse("home"))

    def test_patient_list_searches_and_filters_patients(self):
        self.client.force_login(self.receptionist)
        response = self.client.get(reverse("reception:patient-list"), {"q": "Nora", "blood_type": "O+", "gender": "FEMALE"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nora Ali")
        self.assertContains(response, "patient1@example.com")

    def test_receptionist_can_create_patient(self):
        self.client.force_login(self.receptionist)
        response = self.client.post(
            reverse("reception:patient-create"),
            {
                "first_name": "Omar",
                "last_name": "Said",
                "email": "omar@example.com",
                "phone_number": "01000000003",
                "date_of_birth": "1990-01-15",
                "blood_type": "A+",
                "gender": "MALE",
                "allergies": "None",
                "medical_history": "Hypertension",
                "address": "Talkha",
                "emergency_contact_name": "Sara Said",
                "emergency_contact_phone": "01000000004",
            },
        )

        self.assertRedirects(response, reverse("reception:patient-list"))
        patient = CustomUser.objects.get(email="omar@example.com")
        self.assertEqual(patient.role, CustomUser.Role.PATIENT)
        self.assertFalse(patient.is_active)
        self.assertEqual(patient.patient_profile.medical_history, "Hypertension")
        self.assertEqual(len(mail.outbox), 1)

    def test_duplicate_email_validation(self):
        self.client.force_login(self.receptionist)
        response = self.client.post(
            reverse("reception:patient-create"),
            {
                "first_name": "Nora",
                "last_name": "Copy",
                "email": "patient1@example.com",
                "date_of_birth": "1995-04-12",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A user with this email already exists.")

    def test_receptionist_can_edit_patient(self):
        self.client.force_login(self.receptionist)
        response = self.client.post(
            reverse("reception:patient-edit", args=[self.patient.pk]),
            {
                "first_name": "Nora",
                "last_name": "Hassan",
                "phone_number": "01000000009",
                "date_of_birth": "1995-04-12",
                "blood_type": "AB+",
                "gender": "FEMALE",
                "allergies": "Latex",
                "medical_history": "No chronic illness",
                "address": "Mansoura City",
                "emergency_contact_name": "Hana Hassan",
                "emergency_contact_phone": "01000000010",
            },
        )

        self.assertRedirects(response, reverse("reception:patient-detail", args=[self.patient.pk]))
        self.patient.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.patient.last_name, "Hassan")
        self.assertEqual(self.profile.blood_type, "AB+")
        self.assertEqual(self.profile.allergies, "Latex")

    def test_patient_detail_shows_profile_and_recent_appointments(self):
        doctor = CustomUser.objects.create_user(
            username="doctor",
            email="doctor@example.com",
            password="pass12345",
            first_name="Mina",
            last_name="Youssef",
            role=CustomUser.Role.DOCTOR,
        )
        slot = AppointmentSlot.objects.create(
            doctor=doctor,
            date=date(2026, 1, 10),
            start_time=time(9, 0),
            end_time=time(9, 30),
        )
        Appointment.objects.create(
            patient=self.patient,
            doctor=doctor,
            slot=slot,
            status=Appointment.Status.CONFIRMED,
        )

        self.client.force_login(self.receptionist)
        response = self.client.get(reverse("reception:patient-detail", args=[self.patient.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Penicillin")
        self.assertContains(response, "Asthma")
        self.assertContains(response, "Confirmed")
