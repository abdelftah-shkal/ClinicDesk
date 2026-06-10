import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from clinic.models import ClinicSettings, ClinicService

class ClinicSettingsTests(TestCase):
    def test_singleton_behavior(self):
        # Retrieve or create setting
        settings1 = ClinicSettings.get_settings()
        self.assertEqual(settings1.pk, 1)
        self.assertEqual(settings1.clinic_name, 'CareFlow Clinic')

        # Try to save another settings instance
        settings2 = ClinicSettings(clinic_name="Another Clinic")
        settings2.save()

        # Both variables should point to or fetch the same instance with PK = 1
        self.assertEqual(ClinicSettings.objects.count(), 1)
        settings1.refresh_from_db()
        self.assertEqual(settings1.clinic_name, "Another Clinic")

    def test_default_values(self):
        settings = ClinicSettings.get_settings()
        self.assertEqual(settings.currency, 'EGP')
        self.assertEqual(settings.default_slot_duration, 30)
        self.assertEqual(settings.opening_time, datetime.time(9, 0))
        self.assertEqual(settings.closing_time, datetime.time(17, 0))


class ClinicServiceTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.doctor = User.objects.create_user(
            username="doctor",
            email="doctor@example.com",
            password="pass12345",
            role="DOCTOR",
        )
        self.patient = User.objects.create_user(
            username="patient",
            email="patient@example.com",
            password="pass12345",
            role="PATIENT",
        )

    def test_create_service_with_doctors(self):
        service = ClinicService.objects.create(
            name="Consultation",
            description="General checkup",
            icon="bi-heart",
            price_range="100 - 200 EGP",
        )
        service.doctors.add(self.doctor)
        self.assertIn(self.doctor, service.doctors.all())
        self.assertEqual(service.doctors.count(), 1)


from django.urls import reverse

class ClinicSettingsViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="pass12345",
            role="ADMIN",
        )
        self.doctor = User.objects.create_user(
            username="doctor",
            email="doctor@example.com",
            password="pass12345",
            role="DOCTOR",
        )

    def test_settings_view_requires_admin(self):
        url = reverse('admin-clinic-settings')
        
        # Unauthenticated redirects to login
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Doctor (non-admin) is forbidden
        self.client.force_login(self.doctor)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        # Admin can access
        self.client.force_login(self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_panel/clinic_settings.html')

    def test_settings_view_post_updates_settings(self):
        url = reverse('admin-clinic-settings')
        self.client.force_login(self.admin)
        
        data = {
            'clinic_name': 'Updated Clinic Name',
            'clinic_address': 'New Address',
            'clinic_phone': '555-0199',
            'clinic_email': 'updated@clinic.com',
            'opening_time': '08:00',
            'closing_time': '16:00',
            'default_slot_duration': 20,
            'currency': 'USD',
            'working_days': ['0', '1', '2', '3', '4'],
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, url)
        
        settings = ClinicSettings.get_settings()
        self.assertEqual(settings.clinic_name, 'Updated Clinic Name')
        self.assertEqual(settings.clinic_phone, '555-0199')
        self.assertEqual(settings.default_slot_duration, 20)
        self.assertEqual(settings.working_days, [0, 1, 2, 3, 4])


class ClinicServiceCRUDTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="pass12345",
            role="ADMIN",
        )
        self.doctor = User.objects.create_user(
            username="doctor",
            email="doctor@example.com",
            password="pass12345",
            role="DOCTOR",
        )
        self.service = ClinicService.objects.create(
            name="Cardiology",
            description="Heart care",
            icon="bi-heart",
            price_range="300-500",
            is_active=True,
            display_order=1,
        )

    def test_list_services(self):
        url = reverse('admin-services')
        self.client.force_login(self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cardiology")
        self.assertTemplateUsed(response, 'admin_panel/service_list.html')

    def test_create_service(self):
        url = reverse('admin-service-create')
        self.client.force_login(self.admin)
        
        data = {
            'name': 'Orthopedics',
            'description': 'Bone care',
            'icon': 'bi-activity',
            'price_range': '150 - 300 EGP',
            'is_active': True,
            'display_order': 2,
            'doctors': [self.doctor.id],
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('admin-services'))
        
        self.assertTrue(ClinicService.objects.filter(name='Orthopedics').exists())
        ortho = ClinicService.objects.get(name='Orthopedics')
        self.assertIn(self.doctor, ortho.doctors.all())

    def test_edit_service(self):
        url = reverse('admin-service-edit', args=[self.service.id])
        self.client.force_login(self.admin)
        
        data = {
            'name': 'Cardiology Updated',
            'description': 'Advanced Heart care',
            'icon': 'bi-heart-fill',
            'price_range': '400-600',
            'is_active': False,
            'display_order': 5,
            'doctors': [],
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('admin-services'))
        
        self.service.refresh_from_db()
        self.assertEqual(self.service.name, 'Cardiology Updated')
        self.assertFalse(self.service.is_active)

    def test_delete_service(self):
        url = reverse('admin-service-delete', args=[self.service.id])
        self.client.force_login(self.admin)
        
        # GET is not allowed
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)
        
        # POST deletes
        response = self.client.post(url)
        self.assertRedirects(response, reverse('admin-services'))
        self.assertFalse(ClinicService.objects.filter(id=self.service.id).exists())


from accounts.models import DoctorProfile


class PublicGuestPagesTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.doctor1 = User.objects.create_user(
            username="doc1",
            email="doc1@example.com",
            password="pass12345",
            role="DOCTOR",
            first_name="Alice",
            last_name="Smith",
        )
        self.doc_profile1 = DoctorProfile.objects.create(
            user=self.doctor1,
            specialty="Pediatrics",
            bio="Caring pediatrician",
            consultation_fee=250.00,
        )

        self.doctor2 = User.objects.create_user(
            username="doc2",
            email="doc2@example.com",
            password="pass12345",
            role="DOCTOR",
            first_name="Bob",
            last_name="Jones",
        )
        self.doc_profile2 = DoctorProfile.objects.create(
            user=self.doctor2,
            specialty="Cardiology",
            bio="Experienced cardiologist",
            consultation_fee=400.00,
        )

        # Inactive doctor should not appear
        self.doctor3 = User.objects.create_user(
            username="doc3",
            email="doc3@example.com",
            password="pass12345",
            role="DOCTOR",
            first_name="Inactive",
            last_name="Doc",
            is_active=False,
        )
        self.doc_profile3 = DoctorProfile.objects.create(
            user=self.doctor3,
            specialty="Dermatology",
            bio="Inactive doctor bio",
            consultation_fee=300.00,
        )

        # Services
        self.service_active = ClinicService.objects.create(
            name="Child Care",
            description="Pediatric service",
            icon="bi-baby",
            price_range="200-300",
            is_active=True,
            display_order=1,
        )
        self.service_active.doctors.add(self.doctor1)

        self.service_inactive = ClinicService.objects.create(
            name="Laser Therapy",
            description="Inactive service",
            icon="bi-lightning",
            price_range="500-1000",
            is_active=False,
            display_order=2,
        )

    def test_public_doctors_list_view_all(self):
        url = reverse('public-doctors')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'doctors/list.html')
        self.assertContains(response, "Dr. Alice Smith")
        self.assertContains(response, "Dr. Bob Jones")
        self.assertNotContains(response, "Inactive Doc")

    def test_public_doctors_list_view_search_text(self):
        url = reverse('public-doctors')
        # Search by name
        response = self.client.get(url, {'q': 'Alice'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dr. Alice Smith")
        self.assertNotContains(response, "Dr. Bob Jones")

        # Search by specialty text
        response = self.client.get(url, {'q': 'Cardiology'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dr. Bob Jones")
        self.assertNotContains(response, "Dr. Alice Smith")

    def test_public_doctors_list_view_filter_specialty(self):
        url = reverse('public-doctors')
        # Filter by specialty dropdown
        response = self.client.get(url, {'specialty': 'Pediatrics'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dr. Alice Smith")
        self.assertNotContains(response, "Dr. Bob Jones")

    def test_public_services_list_view(self):
        url = reverse('public-services')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'services/list.html')
        self.assertContains(response, "Child Care")
        self.assertNotContains(response, "Laser Therapy")

    def test_dynamic_home_view(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        
        # Verify stats counters
        self.assertEqual(response.context['doctors_count'], 2)
        self.assertEqual(response.context['services_count'], 1)
        self.assertEqual(response.context['today_appointments_count'], 0)
        self.assertEqual(response.context['today_checked_in_count'], 0)
        
        # Check featured lists in context
        self.assertIn(self.doc_profile1, response.context['featured_doctors'])
        self.assertIn(self.service_active, response.context['featured_services'])


