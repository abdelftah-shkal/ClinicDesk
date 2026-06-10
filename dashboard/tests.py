from django.test import TestCase
from django.urls import reverse
from accounts.models import CustomUser

class DashboardViewTestCase(TestCase):
    def test_admin_dashboard_view(self):
        admin_user = CustomUser.objects.create_user(
            username='admin_test',
            email='admin@example.com',
            password='password123',
            role='ADMIN'
        )
        self.client.login(username='admin_test', password='password123')
        url = reverse('dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
