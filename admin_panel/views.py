from django.utils.translation import gettext_lazy as _
import csv
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Q, Count
from django.db.models.functions import TruncMonth
from django.views.generic import ListView, CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponse

from .mixins import AdminRequiredMixin
from .forms import AdminUserCreateForm, AdminUserEditForm
from accounts.models import CustomUser, DoctorProfile, PatientProfile
from appointments.models import Appointment
from payments.models import PaymentTransaction
from reception.models import WalkInPatient

class UserListView(AdminRequiredMixin, ListView):
    model = CustomUser
    template_name = 'admin_panel/user_list.html'
    context_object_name = 'users'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        
        q = self.request.GET.get('q', '')
        role = self.request.GET.get('role', '')
        status = self.request.GET.get('status', '')

        if q:
            qs = qs.filter(
                Q(username__icontains=q) |
                Q(email__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q)
            )
        
        if role and role != 'ALL':
            qs = qs.filter(role=role)
            
        if status == 'Active':
            qs = qs.filter(is_active=True)
        elif status == 'Inactive':
            qs = qs.filter(is_active=False)
            
        return qs.order_by('-date_joined')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['role'] = self.request.GET.get('role', 'ALL')
        context['status'] = self.request.GET.get('status', 'ALL')
        context['current_section'] = 'admin-users'
        return context

class UserCreateView(AdminRequiredMixin, CreateView):
    model = CustomUser
    form_class = AdminUserCreateForm
    template_name = 'admin_panel/user_create.html'
    success_url = reverse_lazy('admin-users')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        
        if user.role == 'DOCTOR':
            DoctorProfile.objects.get_or_create(user=user)
        elif user.role == 'PATIENT':
            PatientProfile.objects.get_or_create(
                user=user,
                defaults={'date_of_birth': timezone.now().date()}
            )
            
        messages.success(self.request, f"User {user.username} created successfully.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_section'] = 'admin-users'
        return context

class UserEditView(AdminRequiredMixin, UpdateView):
    model = CustomUser
    form_class = AdminUserEditForm
    template_name = 'admin_panel/user_edit.html'
    success_url = reverse_lazy('admin-users')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        
        if user.role == 'DOCTOR':
            DoctorProfile.objects.get_or_create(user=user)
        elif user.role == 'PATIENT':
            PatientProfile.objects.get_or_create(
                user=user,
                defaults={'date_of_birth': timezone.now().date()}
            )
            
        messages.success(self.request, f"User {user.username} updated successfully.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_section'] = 'admin-users'
        return context

class UserToggleActiveView(AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        user = get_object_or_404(CustomUser, pk=pk)
        # Prevent deactivating oneself
        if user == request.user:
            messages.error(request, _("You cannot deactivate your own account."))
            return redirect('admin-users')
            
        user.is_active = not user.is_active
        user.save()
        status_text = "activated" if user.is_active else "deactivated"
        messages.success(request, _("User {user.username} {status_text}."))
        return redirect('admin-users')


def get_analytics_data(date_from, date_to):
    appointments = Appointment.objects.filter(created_at__gte=date_from, created_at__lte=date_to)
    transactions = PaymentTransaction.objects.filter(created_at__gte=date_from, created_at__lte=date_to)
    users = CustomUser.objects.filter(date_joined__gte=date_from, date_joined__lte=date_to)
    
    total_revenue = transactions.filter(status='PAID').aggregate(total=Sum('amount'))['total'] or 0
    total_appointments = appointments.count()
    total_users = users.count()
    
    confirmed_statuses = ['CONFIRMED', 'COMPLETED', 'CHECKED_IN']
    confirmed_count = appointments.filter(status__in=confirmed_statuses).count()
    confirmed_rate = round((confirmed_count / total_appointments * 100), 1) if total_appointments > 0 else 0
    
    paid_tx_count = transactions.filter(status='PAID').count()
    avg_revenue = round(float(total_revenue) / paid_tx_count, 2) if paid_tx_count > 0 else 0
    
    refund_qs = transactions.filter(status='REFUNDED')
    total_refunds = refund_qs.count()
    refund_amount = refund_qs.aggregate(total=Sum('amount'))['total'] or 0

    # Monthly Breakdown
    monthly_new_users = list(users.annotate(month=TruncMonth('date_joined')).values('month').annotate(count=Count('id')).order_by('month'))
    monthly_revenue = list(transactions.filter(status='PAID', paid_at__isnull=False).annotate(month=TruncMonth('paid_at')).values('month').annotate(total=Sum('amount')).order_by('month'))
    monthly_appointments = list(appointments.annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id')).order_by('month'))

    # Payment Status
    payment_status_dist = list(transactions.values('status').annotate(count=Count('id')))

    # Appointment Status
    appt_status_dist = list(appointments.values('status').annotate(count=Count('id')))

    # Role Distribution
    role_dist = list(users.values('role').annotate(count=Count('id')))

    # Doctor Performance
    doctor_performance = []
    doctors = CustomUser.objects.filter(role='DOCTOR')
    for doc in doctors:
        doc_appts = appointments.filter(slot__doctor=doc)
        doc_total = doc_appts.count()
        if doc_total > 0:
            doc_completed = doc_appts.filter(status='COMPLETED').count()
            doc_rate = round((doc_completed / doc_total * 100), 1)
            doc_revenue = transactions.filter(appointment__slot__doctor=doc, status='PAID').aggregate(total=Sum('amount'))['total'] or 0
            doctor_performance.append({
                'name': doc.get_full_name() or doc.username,
                'total_appointments': doc_total,
                'completed': doc_completed,
                'completion_rate': doc_rate,
                'revenue': doc_revenue
            })
    doctor_performance.sort(key=lambda x: x['revenue'], reverse=True)

    # 1. Most Common Diagnoses (top 10)
    from emr.models import Consultation
    most_common_diagnoses = list(
        Consultation.objects.filter(appointment__created_at__gte=date_from, appointment__created_at__lte=date_to)
        .exclude(diagnosis='')
        .values('diagnosis')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )

    # 2. Patient Return Rate
    completed_patients = (
        Appointment.objects.filter(status='COMPLETED', created_at__gte=date_from, created_at__lte=date_to)
        .values('patient')
        .annotate(completed_count=Count('id'))
    )
    total_completed_patients = completed_patients.count()
    returning_patients = completed_patients.filter(completed_count__gte=2).count()
    patient_return_rate = round((returning_patients / total_completed_patients * 100), 1) if total_completed_patients > 0 else 0.0

    # 3. Disease Statistics by Month
    disease_stats_by_month = list(
        Consultation.objects.filter(appointment__created_at__gte=date_from, appointment__created_at__lte=date_to)
        .exclude(diagnosis='')
        .annotate(month=TruncMonth('appointment__created_at'))
        .values('month', 'diagnosis')
        .annotate(count=Count('id'))
        .order_by('-month', '-count')
    )

    # 4. Monthly Patient Activity (new vs returning)
    from django.db.models import Min
    appts_in_range = Appointment.objects.filter(
        status='COMPLETED',
        created_at__gte=date_from,
        created_at__lte=date_to
    ).values('patient_id', 'created_at').order_by('created_at')

    patient_first_appt = {
        x['patient']: x['first_date']
        for x in Appointment.objects.filter(status='COMPLETED')
        .values('patient')
        .annotate(first_date=Min('created_at'))
    }

    activity_by_month = {}
    for appt in appts_in_range:
        appt_date = appt['created_at']
        month = appt_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month not in activity_by_month:
            activity_by_month[month] = {'new': set(), 'returning': set()}
        
        first_date = patient_first_appt.get(appt['patient_id'])
        if first_date and first_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0) == month:
            activity_by_month[month]['new'].add(appt['patient_id'])
        else:
            activity_by_month[month]['returning'].add(appt['patient_id'])

    monthly_patient_activity = [
        {
            'month': m,
            'new_count': len(data['new']),
            'returning_count': len(data['returning']),
            'total_count': len(data['new']) + len(data['returning'])
        }
        for m, data in sorted(activity_by_month.items())
    ]

    return {
        'total_revenue': total_revenue,
        'total_appointments': total_appointments,
        'total_users': total_users,
        'confirmed_rate': confirmed_rate,
        'avg_revenue': avg_revenue,
        'total_refunds': total_refunds,
        'refund_amount': refund_amount,
        'monthly_new_users': monthly_new_users,
        'monthly_revenue': monthly_revenue,
        'monthly_appointments': monthly_appointments,
        'payment_status_dist': payment_status_dist,
        'appt_status_dist': appt_status_dist,
        'role_dist': role_dist,
        'doctor_performance': doctor_performance,
        'most_common_diagnoses': most_common_diagnoses,
        'patient_return_rate': patient_return_rate,
        'returning_patients': returning_patients,
        'total_completed_patients': total_completed_patients,
        'disease_stats_by_month': disease_stats_by_month,
        'monthly_patient_activity': monthly_patient_activity,
    }




class AnalyticsExportView(AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        date_from_str = request.GET.get('date_from')
        date_to_str = request.GET.get('date_to')

        if date_to_str:
            try:
                date_to = timezone.datetime.strptime(date_to_str, '%Y-%m-%d').date()
                date_to = timezone.make_aware(timezone.datetime.combine(date_to, timezone.datetime.max.time()))
            except ValueError:
                date_to = timezone.now()
        else:
            date_to = timezone.now()
            
        if date_from_str:
            try:
                date_from = timezone.datetime.strptime(date_from_str, '%Y-%m-%d').date()
                date_from = timezone.make_aware(timezone.datetime.combine(date_from, timezone.datetime.min.time()))
            except ValueError:
                date_from = date_to - timedelta(days=365)
        else:
            date_from = date_to - timedelta(days=365)

        data = get_analytics_data(date_from, date_to)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="analytics_export_{date_from.strftime("%Y%m%d")}_{date_to.strftime("%Y%m%d")}.csv"'

        writer = csv.writer(response)
        
        # KPIs Section
        writer.writerow(['Overview KPIs'])
        writer.writerow(['Total Revenue (EGP)', data['total_revenue']])
        writer.writerow(['Total Appointments', data['total_appointments']])
        writer.writerow(['Total Users', data['total_users']])
        writer.writerow(['Confirmed Rate (%)', data['confirmed_rate']])
        writer.writerow(['Average Revenue/Appt (EGP)', data['avg_revenue']])
        writer.writerow(['Total Refunds', data['total_refunds']])
        writer.writerow(['Refund Amount (EGP)', data['refund_amount']])
        writer.writerow([])

        # Doctor Performance
        writer.writerow(['Doctor Performance'])
        writer.writerow(['Doctor Name', 'Total Appointments', 'Completed', 'Completion Rate (%)', 'Revenue Generated (EGP)'])
        for doc in data['doctor_performance']:
            writer.writerow([doc['name'], doc['total_appointments'], doc['completed'], doc['completion_rate'], doc['revenue']])
        writer.writerow([])

        # Appointment Status Distribution
        writer.writerow(['Appointment Status Distribution'])
        writer.writerow(['Status', 'Count'])
        for stat in data['appt_status_dist']:
            writer.writerow([stat['status'], stat['count']])
            
        return response


from clinic.models import ClinicSettings, ClinicService
from .forms import ClinicSettingsForm, ServiceForm

class ClinicSettingsView(AdminRequiredMixin, UpdateView):
    model = ClinicSettings
    form_class = ClinicSettingsForm
    template_name = 'admin_panel/clinic_settings.html'
    success_url = reverse_lazy('admin-clinic-settings')

    def get_object(self, queryset=None):
        return ClinicSettings.get_settings()

    def form_valid(self, form):
        messages.success(self.request, "Clinic settings updated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_section'] = 'clinic-settings'
        return context


class ServiceListView(AdminRequiredMixin, ListView):
    model = ClinicService
    template_name = 'admin_panel/service_list.html'
    context_object_name = 'services'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_section'] = 'clinic-services'
        return context


class ServiceCreateView(AdminRequiredMixin, CreateView):
    model = ClinicService
    form_class = ServiceForm
    template_name = 'admin_panel/service_form.html'
    success_url = reverse_lazy('admin-services')

    def form_valid(self, form):
        messages.success(self.request, f"Service '{form.cleaned_data['name']}' created successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_section'] = 'clinic-services'
        context['title'] = "Add New Service"
        return context


class ServiceEditView(AdminRequiredMixin, UpdateView):
    model = ClinicService
    form_class = ServiceForm
    template_name = 'admin_panel/service_form.html'
    success_url = reverse_lazy('admin-services')

    def form_valid(self, form):
        messages.success(self.request, f"Service '{form.cleaned_data['name']}' updated successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_section'] = 'clinic-services'
        context['title'] = "Edit Service"
        return context


class ServiceDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        service = get_object_or_404(ClinicService, pk=pk)
        service.delete()
        messages.success(request, _("Service '{service.name}' deleted successfully."))
        return redirect('admin-services')


def parse_report_dates(request):
    date_to_str = request.GET.get('date_to')
    date_from_str = request.GET.get('date_from')
    
    if date_to_str:
        try:
            date_to = timezone.datetime.strptime(date_to_str, '%Y-%m-%d').date()
            date_to = timezone.make_aware(timezone.datetime.combine(date_to, timezone.datetime.max.time()))
        except ValueError:
            date_to = timezone.now()
    else:
        date_to = timezone.now()
        
    if date_from_str:
        try:
            date_from = timezone.datetime.strptime(date_from_str, '%Y-%m-%d').date()
            date_from = timezone.make_aware(timezone.datetime.combine(date_from, timezone.datetime.min.time()))
        except ValueError:
            date_from = date_to - timedelta(days=30)
    else:
        date_from = date_to - timedelta(days=30)
        
    return date_from, date_to


class AppointmentReportView(AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        date_from, date_to = parse_report_dates(request)
        appointments = Appointment.objects.filter(
            slot__date__gte=date_from.date(),
            slot__date__lte=date_to.date()
        ).select_related('patient', 'slot', 'slot__doctor').order_by('slot__date', 'slot__start_time')

        if request.GET.get('export') == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="appointment_report_{date_from.strftime("%Y%m%d")}_{date_to.strftime("%Y%m%d")}.csv"'
            writer = csv.writer(response)
            writer.writerow(['Appointment ID', 'Patient Name', 'Doctor Name', 'Date', 'Start Time', 'Status', 'Created At'])
            for appt in appointments:
                writer.writerow([
                    appt.id,
                    appt.patient.get_full_name() or appt.patient.username,
                    appt.slot.doctor.get_full_name() or appt.slot.doctor.username,
                    appt.slot.date.strftime('%Y-%m-%d'),
                    appt.slot.start_time.strftime('%H:%M'),
                    appt.status,
                    appt.created_at.strftime('%Y-%m-%d %H:%M')
                ])
            return response

        context = {
            'appointments': appointments,
            'date_from': date_from.strftime('%Y-%m-%d'),
            'date_to': date_to.strftime('%Y-%m-%d'),
            'current_section': 'report-appointments',
        }
        from django.shortcuts import render
        return render(request, 'admin_panel/report_appointments.html', context)


class BillingReportView(AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        date_from, date_to = parse_report_dates(request)
        transactions = PaymentTransaction.objects.filter(
            created_at__gte=date_from,
            created_at__lte=date_to
        ).select_related('appointment', 'appointment__patient').order_by('-created_at')

        if request.GET.get('export') == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="billing_report_{date_from.strftime("%Y%m%d")}_{date_to.strftime("%Y%m%d")}.csv"'
            writer = csv.writer(response)
            writer.writerow(['Transaction ID', 'Appointment ID', 'Patient Name', 'Amount (EGP)', 'Payment Status', 'Stripe Checkout ID', 'Date'])
            for tx in transactions:
                writer.writerow([
                    tx.id,
                    tx.appointment.id if tx.appointment else '',
                    tx.appointment.patient.get_full_name() or tx.appointment.patient.username if (tx.appointment and tx.appointment.patient) else '',
                    tx.amount,
                    tx.status,
                    tx.stripe_checkout_id,
                    tx.created_at.strftime('%Y-%m-%d %H:%M')
                ])
            return response

        context = {
            'transactions': transactions,
            'date_from': date_from.strftime('%Y-%m-%d'),
            'date_to': date_to.strftime('%Y-%m-%d'),
            'current_section': 'report-billing',
        }
        from django.shortcuts import render
        return render(request, 'admin_panel/report_billing.html', context)


class PatientActivityReportView(AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        date_from, date_to = parse_report_dates(request)
        
        # Get all patients
        patients = CustomUser.objects.filter(role='PATIENT')
        patients_data = []
        for p in patients:
            appts = Appointment.objects.filter(patient=p, slot__date__gte=date_from.date(), slot__date__lte=date_to.date())
            total_cnt = appts.count()
            if total_cnt > 0 or (p.date_joined.date() >= date_from.date() and p.date_joined.date() <= date_to.date()):
                completed_cnt = appts.filter(status='COMPLETED').count()
                patients_data.append({
                    'name': p.get_full_name() or p.username,
                    'email': p.email,
                    'date_joined': p.date_joined,
                    'total_appointments': total_cnt,
                    'completed_appointments': completed_cnt
                })

        if request.GET.get('export') == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="patient_activity_{date_from.strftime("%Y%m%d")}_{date_to.strftime("%Y%m%d")}.csv"'
            writer = csv.writer(response)
            writer.writerow(['Patient Name', 'Email', 'Date Joined', 'Total Appointments in Period', 'Completed Appointments in Period'])
            for row in patients_data:
                writer.writerow([
                    row['name'],
                    row['email'],
                    row['date_joined'].strftime('%Y-%m-%d'),
                    row['total_appointments'],
                    row['completed_appointments']
                ])
            return response

        context = {
            'patients_data': patients_data,
            'date_from': date_from.strftime('%Y-%m-%d'),
            'date_to': date_to.strftime('%Y-%m-%d'),
            'current_section': 'report-patient-activity',
        }
        from django.shortcuts import render
        return render(request, 'admin_panel/report_patient_activity.html', context)


class DiseaseStatisticsReportView(AdminRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        date_from, date_to = parse_report_dates(request)
        from emr.models import Consultation
        disease_stats = list(
            Consultation.objects.filter(
                appointment__slot__date__gte=date_from.date(),
                appointment__slot__date__lte=date_to.date()
            )
            .exclude(diagnosis='')
            .values('diagnosis')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        if request.GET.get('export') == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="disease_stats_{date_from.strftime("%Y%m%d")}_{date_to.strftime("%Y%m%d")}.csv"'
            writer = csv.writer(response)
            writer.writerow(['Diagnosis', 'Cases Count'])
            for stat in disease_stats:
                writer.writerow([
                    stat['diagnosis'],
                    stat['count']
                ])
            return response

        context = {
            'disease_stats': disease_stats,
            'date_from': date_from.strftime('%Y-%m-%d'),
            'date_to': date_to.strftime('%Y-%m-%d'),
            'current_section': 'report-disease-statistics',
        }
        from django.shortcuts import render
        return render(request, 'admin_panel/report_disease_statistics.html', context)


