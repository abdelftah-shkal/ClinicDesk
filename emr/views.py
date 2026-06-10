from django.utils.translation import gettext_lazy as _
from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import ListView, View

from appointments.models import Appointment, DoctorSchedule
from .models import Consultation, Prescription
from .forms import ConsultationForm, PrescriptionFormSet, DoctorScheduleFormSet, MedicalReportFormSet


class DoctorRequiredMixin(LoginRequiredMixin):
    """Check that user is a doctor."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role != "DOCTOR":
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class PatientRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role != "PATIENT":
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class DoctorDailyQueueView(DoctorRequiredMixin, ListView):
    """Show weekly appointments for the doctor."""
    template_name = "emr/daily_queue.html"
    context_object_name = "weekly_appointments"
    paginate_by = None

    def get_queryset(self):
        today = timezone.now().date()
        
        # Calculate week start (Monday) and end (Sunday)
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        return Appointment.objects.filter(
            slot__doctor=self.request.user,
            slot__date__gte=week_start,
            slot__date__lte=week_end,
        ).select_related("patient", "slot").order_by("slot__date", "slot__start_time")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        # Calculate week start and end
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        context["today"] = today
        context["week_start"] = week_start
        context["week_end"] = week_end
        context["total_weekly"] = self.get_queryset().count()
        context["completed_this_week"] = Appointment.objects.filter(
            slot__doctor=self.request.user,
            slot__date__gte=week_start,
            slot__date__lte=week_end,
            status=Appointment.Status.COMPLETED,
        ).count()
        context["pending_this_week"] = Appointment.objects.filter(
            slot__doctor=self.request.user,
            slot__date__gte=week_start,
            slot__date__lte=week_end,
        ).exclude(status__in=[Appointment.Status.COMPLETED, Appointment.Status.CANCELLED]).count()
        context["current_section"] = "queue"
        return context


class ConsultationCreateView(DoctorRequiredMixin, View):
    """Create or update consultation and prescriptions, then mark appointment completed."""
    template_name = "emr/consultation_form.html"
    allowed_statuses = [
        Appointment.Status.CHECKED_IN,
        Appointment.Status.COMPLETED,
    ]

    def get_appointment(self):
        appointment_id = self.kwargs["appointment_id"]
        return get_object_or_404(
            Appointment,
            pk=appointment_id,
            slot__doctor=self.request.user,
            status__in=self.allowed_statuses,
        )

    def get_consultation(self, appointment):
        return Consultation.objects.filter(appointment=appointment).first()

    def get(self, request, *args, **kwargs):
        appointment = self.get_appointment()
        consultation = self.get_consultation(appointment)
        form = ConsultationForm(instance=consultation)
        formset = PrescriptionFormSet(instance=consultation)
        report_formset = MedicalReportFormSet(instance=consultation, prefix="reports")

        return render(request, self.template_name, {
            "appointment": appointment,
            "form": form,
            "formset": formset,
            "report_formset": report_formset,
            "current_section": "consultations",
        })

    def post(self, request, *args, **kwargs):
        appointment = self.get_appointment()
        consultation = self.get_consultation(appointment)
        form = ConsultationForm(request.POST, instance=consultation)
        formset = PrescriptionFormSet(request.POST, instance=consultation)
        report_formset = MedicalReportFormSet(request.POST, request.FILES, instance=consultation, prefix="reports")

        if form.is_valid() and formset.is_valid() and report_formset.is_valid():
            return self.save_consultation(appointment, form, formset, report_formset)

        return render(request, self.template_name, {
            "appointment": appointment,
            "form": form,
            "formset": formset,
            "report_formset": report_formset,
            "current_section": "consultations",
        })

    @transaction.atomic
    def save_consultation(self, appointment, form, formset, report_formset):
        consultation = form.save(commit=False)
        consultation.appointment = appointment
        consultation.doctor = self.request.user
        consultation.patient = appointment.patient
        consultation.save()

        formset.instance = consultation
        formset.save()

        report_formset.instance = consultation
        report_formset.save()

        appointment.status = Appointment.Status.COMPLETED
        appointment.save(update_fields=["status"])

        messages.success(self.request, f"Consultation saved for {appointment.patient}")
        return redirect("emr:daily-queue")


class ManageScheduleView(DoctorRequiredMixin, View):
    """Doctor manages their availability schedule."""
    template_name = "emr/manage_schedule.html"

    def get_queryset(self):
        return DoctorSchedule.objects.filter(doctor=self.request.user).order_by("day_of_week", "start_time")

    def get(self, request, *args, **kwargs):
        formset = DoctorScheduleFormSet(queryset=self.get_queryset())
        return render(request, self.template_name, {
            "formset": formset,
            "schedules": self.get_queryset(),
            "current_section": "schedule",
        })

    def post(self, request, *args, **kwargs):
        formset = DoctorScheduleFormSet(request.POST, queryset=self.get_queryset())

        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.doctor = request.user
                instance.save()

            for obj in formset.deleted_objects:
                obj.delete()

            messages.success(request, _("Schedule updated."))
            return redirect("emr:manage-schedule")

        return render(request, self.template_name, {
            "formset": formset,
            "schedules": self.get_queryset(),
            "current_section": "schedule",
        })


class ConsultationListView(DoctorRequiredMixin, ListView):
    """Show all consultations for this doctor."""
    template_name = "emr/consultations_list.html"
    context_object_name = "consultations"
    paginate_by = 20

    def get_queryset(self):
        queryset = Consultation.objects.filter(
            doctor=self.request.user
        ).select_related("patient", "appointment__slot").order_by("-id")
        
        q = self.request.GET.get("q", "").strip()
        if q:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(patient__username__icontains=q) |
                Q(patient__first_name__icontains=q) |
                Q(patient__last_name__icontains=q) |
                Q(patient__email__icontains=q)
            )
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_section"] = "consultations"
        context["q"] = self.request.GET.get("q", "").strip()
        return context


class PatientConsultationSummaryView(PatientRequiredMixin, View):
    template_name = "emr/patient_consultation_summary.html"

    def get(self, request, *args, **kwargs):
        consultation = get_object_or_404(
            Consultation.objects.select_related(
                "appointment__slot",
                "doctor",
                "patient",
            ).prefetch_related("prescriptions"),
            appointment_id=kwargs["appointment_id"],
            patient=request.user,
        )

        return render(request, self.template_name, {
            "consultation": consultation,
            "appointment": consultation.appointment,
            "current_section": "appointments",
            "dashboard_title": "Consultation Summary",
            "dashboard_subtitle": "Review the diagnosis and prescriptions from your completed visit.",
        })


class PatientMedicalHistoryView(DoctorRequiredMixin, View):
    template_name = "emr/patient_medical_history.html"

    def get(self, request, *args, **kwargs):
        from accounts.models import CustomUser
        patient = get_object_or_404(CustomUser, id=kwargs["patient_id"], role=CustomUser.Role.PATIENT)
        consultations = Consultation.objects.filter(patient=patient).select_related(
            "appointment__slot", "doctor"
        ).prefetch_related(
            "prescriptions", "reports"
        ).order_by("-appointment__slot__date", "-appointment__slot__start_time")

        patient_profile = getattr(patient, "patient_profile", None)

        return render(request, self.template_name, {
            "patient": patient,
            "patient_profile": patient_profile,
            "consultations": consultations,
            "current_section": "consultations",
        })


class PatientPrescriptionsListView(PatientRequiredMixin, ListView):
    template_name = "emr/patient_prescriptions.html"
    context_object_name = "prescriptions"
    paginate_by = 20

    def get_queryset(self):
        return Prescription.objects.filter(
            consultation__patient=self.request.user
        ).select_related(
            'consultation__appointment__slot',
            'consultation__doctor'
        ).order_by('-consultation__appointment__slot__date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_section"] = "prescriptions"
        return context


class PrescriptionPrintView(LoginRequiredMixin, View):
    def get(self, request, consultation_id, *args, **kwargs):
        consultation = get_object_or_404(
            Consultation.objects.select_related("appointment__slot", "doctor", "patient"),
            id=consultation_id
        )
        
        # Accessible by the doctor who created it, or the patient whose prescription it is
        if request.user != consultation.doctor and request.user != consultation.patient:
            raise PermissionDenied
            
        patient_profile = getattr(consultation.patient, "patient_profile", None)
        
        # Calculate age if date_of_birth exists
        age = None
        if patient_profile and patient_profile.date_of_birth:
            import datetime
            today = datetime.date.today()
            dob = patient_profile.date_of_birth
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
        from clinic.models import ClinicSettings
        clinic_settings = ClinicSettings.get_settings()
        
        return render(request, "emr/prescription_print.html", {
            "consultation": consultation,
            "prescriptions": consultation.prescriptions.all(),
            "patient_profile": patient_profile,
            "age": age,
            "clinic_settings": clinic_settings,
        })


