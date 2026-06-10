from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import CustomUser
from appointments.models import Appointment, AppointmentSlot
from payments.models import PaymentTransaction
from emr.models import Consultation

class AdminReportsTestCase(TestCase):
    def setUp(self):
        # Create an admin user
        self.admin_user = CustomUser.objects.create_user(
            username='admin_test',
            email='admin@example.com',
            password='password123',
            role='ADMIN'
        )
        # Create a patient user
        self.patient_user = CustomUser.objects.create_user(
            username='patient_test',
            email='patient@example.com',
            password='password123',
            role='PATIENT'
        )
        # Create a doctor user
        self.doctor_user = CustomUser.objects.create_user(
            username='doctor_test',
            email='doctor@example.com',
            password='password123',
            role='DOCTOR'
        )

        # Create slot and appointment
        self.slot = AppointmentSlot.objects.create(
            doctor=self.doctor_user,
            date=timezone.now().date(),
            start_time=timezone.now().time(),
            end_time=(timezone.now() + timedelta(minutes=30)).time(),
            is_booked=True
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient_user,
            doctor=self.doctor_user,
            slot=self.slot,
            status='COMPLETED'
        )

        # Create payment transaction
        self.payment = PaymentTransaction.objects.create(
            appointment=self.appointment,
            amount=500,
            status='PAID',
            stripe_checkout_id='cs_test_123'
        )

        # Create consultation
        self.consultation = Consultation.objects.create(
            appointment=self.appointment,
            doctor=self.doctor_user,
            patient=self.patient_user,
            symptoms_notes='Fever',
            diagnosis='Influenza'
        )

    def test_unauthenticated_access(self):
        # Unauthenticated users should be redirected or forbidden
        views = [
            'admin-report-appointments',
            'admin-report-billing',
            'admin-report-patient-activity',
            'admin-report-disease-statistics'
        ]
        for view_name in views:
            url = reverse(view_name)
            response = self.client.get(url)
            # AdminRequiredMixin redirects unauthorized users to login page
            self.assertEqual(response.status_code, 302)

    def test_non_admin_access(self):
        self.client.login(username='patient_test', password='password123')
        views = [
            'admin-report-appointments',
            'admin-report-billing',
            'admin-report-patient-activity',
            'admin-report-disease-statistics'
        ]
        for view_name in views:
            url = reverse(view_name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403)

    def test_admin_access_appointments_report(self):
        self.client.login(username='admin_test', password='password123')
        url = reverse('admin-report-appointments')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_panel/report_appointments.html')
        self.assertIn('appointments', response.context)
        self.assertEqual(len(response.context['appointments']), 1)

    def test_admin_export_appointments_csv(self):
        self.client.login(username='admin_test', password='password123')
        url = reverse('admin-report-appointments') + '?export=csv'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        content = response.content.decode('utf-8')
        self.assertIn('Appointment ID', content)
        self.assertIn('patient_test', content)
        self.assertIn('doctor_test', content)

    def test_admin_access_billing_report(self):
        self.client.login(username='admin_test', password='password123')
        url = reverse('admin-report-billing')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_panel/report_billing.html')
        self.assertIn('transactions', response.context)
        self.assertEqual(len(response.context['transactions']), 1)

    def test_admin_export_billing_csv(self):
        self.client.login(username='admin_test', password='password123')
        url = reverse('admin-report-billing') + '?export=csv'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        content = response.content.decode('utf-8')
        self.assertIn('Transaction ID', content)
        self.assertIn('500', content)
        self.assertIn('cs_test_123', content)

    def test_admin_access_patient_activity_report(self):
        self.client.login(username='admin_test', password='password123')
        url = reverse('admin-report-patient-activity')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_panel/report_patient_activity.html')
        self.assertIn('patients_data', response.context)
        self.assertEqual(len(response.context['patients_data']), 1)

    def test_admin_export_patient_activity_csv(self):
        self.client.login(username='admin_test', password='password123')
        url = reverse('admin-report-patient-activity') + '?export=csv'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        content = response.content.decode('utf-8')
        self.assertIn('Patient Name', content)
        self.assertIn('patient_test', content)

    def test_admin_access_disease_statistics_report(self):
        self.client.login(username='admin_test', password='password123')
        url = reverse('admin-report-disease-statistics')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_panel/report_disease_statistics.html')
        self.assertIn('disease_stats', response.context)
        self.assertEqual(len(response.context['disease_stats']), 1)

    def test_admin_export_disease_statistics_csv(self):
        self.client.login(username='admin_test', password='password123')
        url = reverse('admin-report-disease-statistics') + '?export=csv'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        content = response.content.decode('utf-8')
        self.assertIn('Diagnosis', content)
        self.assertIn('Influenza', content)
