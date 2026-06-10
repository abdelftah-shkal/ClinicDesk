import datetime
from pathlib import Path
from django.conf import settings
from django.http import FileResponse, Http404
from django.db.models import Q
from django.views.generic import ListView, TemplateView

from accounts.models import DoctorProfile
from clinic.models import ClinicService
from appointments.models import Appointment


def favicon(request):
    favicon_path = Path(settings.BASE_DIR) / 'static' / 'favicon.svg'
    if not favicon_path.exists():
        raise Http404('Favicon not found')
    return FileResponse(favicon_path.open('rb'), content_type='image/svg+xml')


class PublicDoctorsListView(ListView):
    model = DoctorProfile
    template_name = 'doctors/list.html'
    context_object_name = 'doctors'

    def get_queryset(self):
        queryset = DoctorProfile.objects.select_related('user').filter(user__is_active=True)
        
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(user__first_name__icontains=q) |
                Q(user__last_name__icontains=q) |
                Q(user__username__icontains=q) |
                Q(specialty__icontains=q)
            )
            
        specialty = self.request.GET.get('specialty', '').strip()
        if specialty and specialty != 'All specialties':
            queryset = queryset.filter(specialty__iexact=specialty)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['specialties'] = DoctorProfile.objects.filter(user__is_active=True).values_list('specialty', flat=True).distinct()
        context['q'] = self.request.GET.get('q', '')
        context['selected_specialty'] = self.request.GET.get('specialty', '')
        return context


class PublicServicesView(ListView):
    model = ClinicService
    template_name = 'services/list.html'
    context_object_name = 'services'

    def get_queryset(self):
        return ClinicService.objects.filter(is_active=True).order_by('display_order')


class DynamicHomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = datetime.date.today()
        
        context['doctors_count'] = DoctorProfile.objects.filter(user__is_active=True).count()
        context['services_count'] = ClinicService.objects.filter(is_active=True).count()
        context['today_appointments_count'] = Appointment.objects.filter(slot__date=today).count()
        context['today_checked_in_count'] = Appointment.objects.filter(slot__date=today, status="CHECKED_IN").count()
        
        context['featured_doctors'] = DoctorProfile.objects.select_related('user').filter(user__is_active=True)[:3]
        context['featured_services'] = ClinicService.objects.filter(is_active=True).order_by('display_order')[:3]
        return context
