from datetime import time

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from appointments.models import Appointment, AppointmentSlot
from .models import Consultation, Prescription


class ConsultationWorkflowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.doctor = User.objects.create_user(
            username="doctor",
            email="doctor@example.com",
            password="pass12345",
            role="DOCTOR",
        )
        self.other_doctor = User.objects.create_user(
            username="other-doctor",
            email="other-doctor@example.com",
            password="pass12345",
            role="DOCTOR",
        )
        self.patient = User.objects.create_user(
            username="patient",
            email="patient@example.com",
            password="pass12345",
            role="PATIENT",
        )
        self.other_patient = User.objects.create_user(
            username="other-patient",
            email="other-patient@example.com",
            password="pass12345",
            role="PATIENT",
        )
        self.client.force_login(self.doctor)
        self.slot_count = 0

    def create_appointment(self, status=Appointment.Status.CHECKED_IN, doctor=None):
        self.slot_count += 1
        slot = AppointmentSlot.objects.create(
            doctor=doctor or self.doctor,
            date=timezone.now().date(),
            start_time=time(9 + self.slot_count, 0),
            end_time=time(9 + self.slot_count, 30),
            is_booked=True,
        )
        return Appointment.objects.create(
            patient=self.patient,
            doctor=doctor or self.doctor,
            slot=slot,
            status=status,
        )

    def consultation_url(self, appointment):
        return reverse("emr:consultation-create", args=[appointment.id])

    def patient_summary_url(self, appointment):
        return reverse("emr:patient-consultation-summary", args=[appointment.id])

    def post_data(self, prescriptions=None, consultation=None):
        if prescriptions is None:
            prescriptions = [
                {"medication_name": "Amoxicillin", "dosage": "500 mg", "duration": "7 days"},
            ]
        data = {
            "symptoms_notes": "Fever and cough",
            "diagnosis": "Upper respiratory infection",
            "prescriptions-TOTAL_FORMS": str(len(prescriptions)),
            "prescriptions-INITIAL_FORMS": "0" if consultation is None else str(consultation.prescriptions.count()),
            "prescriptions-MIN_NUM_FORMS": "1",
            "prescriptions-MAX_NUM_FORMS": "1000",
            "reports-TOTAL_FORMS": "0" if consultation is None else str(consultation.reports.count()),
            "reports-INITIAL_FORMS": "0" if consultation is None else str(consultation.reports.count()),
            "reports-MIN_NUM_FORMS": "0",
            "reports-MAX_NUM_FORMS": "1000",
        }
        existing = list(consultation.prescriptions.order_by("id")) if consultation else []
        for index, prescription in enumerate(prescriptions):
            data[f"prescriptions-{index}-medication_name"] = prescription.get("medication_name", "")
            data[f"prescriptions-{index}-dosage"] = prescription.get("dosage", "")
            data[f"prescriptions-{index}-duration"] = prescription.get("duration", "")
            if index < len(existing):
                data[f"prescriptions-{index}-id"] = str(existing[index].id)
                data[f"prescriptions-{index}-consultation"] = str(consultation.id)
        return data

    def test_checked_in_appointment_creates_consultation_with_multiple_prescriptions(self):
        appointment = self.create_appointment()

        response = self.client.post(self.consultation_url(appointment), self.post_data([
            {"medication_name": "Amoxicillin", "dosage": "500 mg", "duration": "7 days"},
            {"medication_name": "Ibuprofen", "dosage": "200 mg", "duration": "3 days"},
        ]))

        self.assertRedirects(response, reverse("emr:daily-queue"))
        consultation = Consultation.objects.get(appointment=appointment)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.COMPLETED)
        self.assertEqual(consultation.doctor, self.doctor)
        self.assertEqual(consultation.patient, self.patient)
        self.assertEqual(consultation.prescriptions.count(), 2)
        self.assertTrue(
            consultation.prescriptions.filter(
                medication_name="Ibuprofen",
                dosage="200 mg",
                duration="3 days",
            ).exists()
        )

    def test_completed_appointment_with_existing_consultation_can_be_edited(self):
        appointment = self.create_appointment(status=Appointment.Status.COMPLETED)
        consultation = Consultation.objects.create(
            appointment=appointment,
            doctor=self.doctor,
            patient=self.patient,
            symptoms_notes="Old notes",
            diagnosis="Old diagnosis",
        )
        prescription = Prescription.objects.create(
            consultation=consultation,
            medication_name="Old medication",
            dosage="10 mg",
            duration="1 day",
        )

        response = self.client.get(self.consultation_url(appointment))
        self.assertContains(response, "Old notes")
        self.assertContains(response, "Old medication")

        data = self.post_data([
            {"medication_name": "Updated medication", "dosage": "20 mg", "duration": "5 days"},
        ], consultation=consultation)
        data["symptoms_notes"] = "Updated notes"
        data["diagnosis"] = "Updated diagnosis"
        response = self.client.post(self.consultation_url(appointment), data)

        self.assertRedirects(response, reverse("emr:daily-queue"))
        consultation.refresh_from_db()
        prescription.refresh_from_db()
        self.assertEqual(consultation.symptoms_notes, "Updated notes")
        self.assertEqual(consultation.diagnosis, "Updated diagnosis")
        self.assertEqual(prescription.medication_name, "Updated medication")
        self.assertEqual(prescription.dosage, "20 mg")
        self.assertEqual(prescription.duration, "5 days")
        self.assertEqual(Consultation.objects.filter(appointment=appointment).count(), 1)

    def test_unsupported_statuses_cannot_access_consultation_form(self):
        unsupported_statuses = [
            Appointment.Status.REQUESTED,
            Appointment.Status.AWAITING_PAYMENT,
            Appointment.Status.CONFIRMED,
            Appointment.Status.CANCELLED,
        ]

        for status in unsupported_statuses:
            with self.subTest(status=status):
                appointment = self.create_appointment(status=status)
                response = self.client.get(self.consultation_url(appointment))
                self.assertEqual(response.status_code, 404)
                slot = appointment.slot
                appointment.delete()
                slot.delete()

    def test_other_doctor_cannot_access_consultation_form(self):
        appointment = self.create_appointment(doctor=self.other_doctor)

        response = self.client.get(self.consultation_url(appointment))

        self.assertEqual(response.status_code, 404)

    def test_invalid_prescription_data_does_not_create_partial_records(self):
        appointment = self.create_appointment()

        response = self.client.post(self.consultation_url(appointment), self.post_data([
            {"medication_name": "Amoxicillin", "dosage": "", "duration": "7 days"},
        ]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Consultation.objects.filter(appointment=appointment).exists())
        self.assertEqual(Prescription.objects.count(), 0)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, Appointment.Status.CHECKED_IN)

    def test_at_least_one_prescription_is_required(self):
        appointment = self.create_appointment()
        data = self.post_data([])
        data["prescriptions-TOTAL_FORMS"] = "0"

        response = self.client.post(self.consultation_url(appointment), data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please submit at least 1 form.")
        self.assertFalse(Consultation.objects.filter(appointment=appointment).exists())

    def test_patient_can_view_read_only_consultation_summary(self):
        appointment = self.create_appointment(status=Appointment.Status.COMPLETED)
        consultation = Consultation.objects.create(
            appointment=appointment,
            doctor=self.doctor,
            patient=self.patient,
            symptoms_notes="Patient had fever for three days.",
            diagnosis="Viral infection",
        )
        Prescription.objects.create(
            consultation=consultation,
            medication_name="Paracetamol",
            dosage="500 mg",
            duration="3 days",
        )

        self.client.force_login(self.patient)
        response = self.client.get(self.patient_summary_url(appointment))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Viral infection")
        self.assertContains(response, "Paracetamol")
        self.assertNotContains(response, '<form method="post" novalidate')

    def test_other_patient_cannot_view_consultation_summary(self):
        appointment = self.create_appointment(status=Appointment.Status.COMPLETED)
        Consultation.objects.create(
            appointment=appointment,
            doctor=self.doctor,
            patient=self.patient,
            symptoms_notes="Private notes",
            diagnosis="Private diagnosis",
        )

        self.client.force_login(self.other_patient)
        response = self.client.get(self.patient_summary_url(appointment))

        self.assertEqual(response.status_code, 404)

    def test_doctor_cannot_use_patient_summary_view(self):
        appointment = self.create_appointment(status=Appointment.Status.COMPLETED)
        Consultation.objects.create(
            appointment=appointment,
            doctor=self.doctor,
            patient=self.patient,
            symptoms_notes="Notes",
            diagnosis="Diagnosis",
        )

        self.client.force_login(self.doctor)
        response = self.client.get(self.patient_summary_url(appointment))

        self.assertEqual(response.status_code, 403)

    def test_consultation_form_saves_lab_and_test_results_and_reports(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        appointment = self.create_appointment()
        
        # Build post data
        data = self.post_data([
            {"medication_name": "Amoxicillin", "dosage": "500 mg", "duration": "7 days"},
        ])
        
        # Add lab results and test results
        data["lab_results"] = "Blood count normal"
        data["test_results"] = "Chest X-Ray shows clear lungs"
        
        # Add report formset management data
        data["reports-TOTAL_FORMS"] = "1"
        data["reports-INITIAL_FORMS"] = "0"
        data["reports-MIN_NUM_FORMS"] = "0"
        data["reports-MAX_NUM_FORMS"] = "1000"
        data["reports-0-title"] = "Blood Test Result"
        data["reports-0-report_type"] = "LAB"
        
        # Create a mock file
        mock_file = SimpleUploadedFile("blood_test.pdf", b"pdf content", content_type="application/pdf")
        data["reports-0-file"] = mock_file
        
        response = self.client.post(self.consultation_url(appointment), data)
        self.assertRedirects(response, reverse("emr:daily-queue"))
        
        consultation = Consultation.objects.get(appointment=appointment)
        self.assertEqual(consultation.lab_results, "Blood count normal")
        self.assertEqual(consultation.test_results, "Chest X-Ray shows clear lungs")
        
        # Verify MedicalReport is created
        self.assertEqual(consultation.reports.count(), 1)
        report = consultation.reports.first()
        self.assertEqual(report.title, "Blood Test Result")
        self.assertEqual(report.report_type, "LAB")
        self.assertTrue(report.file.name.startswith("medical_reports/blood_test"))
        
        # Clean up uploaded file
        if report.file:
            report.file.delete(save=False)

    def test_doctor_can_view_patient_medical_history(self):
        # Create consultation and medical report
        appointment = self.create_appointment(status=Appointment.Status.COMPLETED)
        consultation = Consultation.objects.create(
            appointment=appointment,
            doctor=self.doctor,
            patient=self.patient,
            symptoms_notes="Patient has fever",
            diagnosis="Flu",
            lab_results="Normal",
            test_results="Clear",
        )
        
        # Add report
        from django.core.files.uploadedfile import SimpleUploadedFile
        mock_file = SimpleUploadedFile("report.pdf", b"pdf content")
        report = consultation.reports.create(
            title="Blood Test",
            report_type="LAB",
            file=mock_file
        )

        # Login doctor
        self.client.force_login(self.doctor)
        url = reverse("emr:patient-medical-history", kwargs={"patient_id": self.patient.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "emr/patient_medical_history.html")
        self.assertContains(response, self.patient.username)
        self.assertContains(response, "Patient has fever")
        self.assertContains(response, "Blood Test")
        
        # Clean up
        if report.file:
            report.file.delete(save=False)

    def test_non_doctor_cannot_view_patient_medical_history(self):
        # Login patient
        self.client.force_login(self.patient)
        url = reverse("emr:patient-medical-history", kwargs={"patient_id": self.patient.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_consultation_list_view_and_search(self):
        from accounts.models import CustomUser
        patient_alice = CustomUser.objects.create_user(
            username="alice",
            email="alice@test.com",
            password="password",
            role=CustomUser.Role.PATIENT,
        )
        patient_bob = CustomUser.objects.create_user(
            username="bob",
            email="bob@test.com",
            password="password",
            role=CustomUser.Role.PATIENT,
        )

        appt1 = self.create_appointment(status=Appointment.Status.COMPLETED)
        appt1.patient = patient_alice
        appt1.save()
        c1 = Consultation.objects.create(
            appointment=appt1,
            doctor=self.doctor,
            patient=patient_alice,
            symptoms_notes="Alice symptoms",
            diagnosis="Flu",
        )
        
        appt2 = self.create_appointment(status=Appointment.Status.COMPLETED)
        appt2.patient = patient_bob
        appt2.save()
        c2 = Consultation.objects.create(
            appointment=appt2,
            doctor=self.doctor,
            patient=patient_bob,
            symptoms_notes="Bob symptoms",
            diagnosis="Cold",
        )

        self.client.force_login(self.doctor)
        url = reverse("emr:consultations-list")
        
        # Test no search query lists all
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, patient_alice.username)
        self.assertContains(response, patient_bob.username)
        
        # Test search filter matches the search term
        response = self.client.get(url, {"q": "bob"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, patient_bob.username)
        self.assertNotContains(response, patient_alice.username)
        
        # Test search filter with no matches
        response = self.client.get(url, {"q": "nonexistent"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, patient_alice.username)
        self.assertNotContains(response, patient_bob.username)
        self.assertContains(response, "No consultations yet")

    def test_patient_prescriptions_list_view_displays_prescriptions_and_enforces_rbac(self):
        # Create consultation and prescriptions for the patient
        appointment = self.create_appointment(status=Appointment.Status.COMPLETED)
        consultation = Consultation.objects.create(
            appointment=appointment,
            doctor=self.doctor,
            patient=self.patient,
            symptoms_notes="Patient notes",
            diagnosis="Diagnosis notes",
        )
        Prescription.objects.create(
            consultation=consultation,
            medication_name="Aspirin",
            dosage="100 mg",
            duration="5 days",
        )
        Prescription.objects.create(
            consultation=consultation,
            medication_name="Vitamin C",
            dosage="500 mg",
            duration="10 days",
        )

        url = reverse("emr:patient-prescriptions")

        # Test unauthenticated access redirects to login
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue("login" in response.url)

        # Test doctor access returns 403 (PermissionDenied)
        self.client.force_login(self.doctor)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        # Test patient access displays prescriptions
        self.client.force_login(self.patient)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "emr/patient_prescriptions.html")
        self.assertContains(response, "Aspirin")
        self.assertContains(response, "Vitamin C")
        self.assertContains(response, "Dr. doctor")

    def test_prescription_print_enforces_permissions_and_loads_correct_data(self):
        # Create a consultation with a prescription
        appointment = self.create_appointment(status=Appointment.Status.COMPLETED)
        consultation = Consultation.objects.create(
            appointment=appointment,
            doctor=self.doctor,
            patient=self.patient,
            symptoms_notes="Patient notes",
            diagnosis="Diagnosis notes",
        )
        Prescription.objects.create(
            consultation=consultation,
            medication_name="Penicillin",
            dosage="250 mg",
            duration="10 days",
        )

        url = reverse("emr:prescription-print", kwargs={"consultation_id": consultation.id})

        # Test unauthenticated access redirects to login
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Test consulting doctor access is allowed and contains data
        self.client.force_login(self.doctor)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "emr/prescription_print.html")
        self.assertContains(response, "Penicillin")
        self.assertContains(response, "Dr. doctor")

        # Test patient access is allowed
        self.client.force_login(self.patient)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Test other doctor access returns 403 PermissionDenied
        self.client.force_login(self.other_doctor)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        # Test other patient access returns 403 PermissionDenied
        self.client.force_login(self.other_patient)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)


