from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from appointments.models import Appointment, AppointmentSlot, RescheduleHistory
from accounts.forms import BLOOD_TYPE_CHOICES
from accounts.models import PatientProfile
from payments.views import process_appointment_refund
from .models import WalkInPatient
from .forms import (
    PatientEditForm,
    PatientRegistrationForm,
    RescheduleForm,
    UpdateStatusForm,
    WalkInPatientForm,
)

User = get_user_model()


class ReceptionistRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'RECEPTIONIST':
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)


class PatientListView(LoginRequiredMixin, ReceptionistRequiredMixin, View):
    paginate_by = 25

    def get(self, request):
        patients = User.objects.filter(
            role=User.Role.PATIENT,
            patient_profile__isnull=False,
        ).select_related("patient_profile").order_by("id")
        search_query = (request.GET.get("q") or "").strip()
        blood_type = (request.GET.get("blood_type") or "").strip()
        gender = (request.GET.get("gender") or "").strip()

        if search_query:
            search_filter = (
                Q(first_name__icontains=search_query)
                | Q(last_name__icontains=search_query)
                | Q(username__icontains=search_query)
                | Q(email__icontains=search_query)
                | Q(phone_number__icontains=search_query)
            )
            if search_query.isdigit():
                search_filter |= Q(id=int(search_query))
            patients = patients.filter(search_filter)

        if blood_type:
            patients = patients.filter(patient_profile__blood_type=blood_type)

        if gender:
            patients = patients.filter(patient_profile__gender=gender)

        paginator = Paginator(patients, self.paginate_by)
        page_obj = paginator.get_page(request.GET.get("page"))

        return render(request, "reception/patient_list.html", {
            "patients": page_obj,
            "page_obj": page_obj,
            "search_query": search_query,
            "selected_blood_type": blood_type,
            "selected_gender": gender,
            "blood_type_choices": BLOOD_TYPE_CHOICES,
            "gender_choices": PatientProfile._meta.get_field("gender").choices,
            "current_section": "patients",
        })


class PatientCreateView(LoginRequiredMixin, ReceptionistRequiredMixin, View):
    def get(self, request):
        return render(request, "reception/patient_create.html", {
            "form": PatientRegistrationForm(),
            "current_section": "patients",
        })

    def post(self, request):
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                form.save()
            messages.success(request, _("Patient record created successfully."))
            return redirect("reception:patient-list")

        messages.error(request, _("Could not create the patient record. Please check the form and try again."))
        return render(request, "reception/patient_create.html", {
            "form": form,
            "current_section": "patients",
        })


class PatientEditView(LoginRequiredMixin, ReceptionistRequiredMixin, View):
    def get_patient(self, pk):
        return get_object_or_404(
            User.objects.select_related("patient_profile"),
            pk=pk,
            role=User.Role.PATIENT,
        )

    def get(self, request, pk):
        patient = self.get_patient(pk)
        return render(request, "reception/patient_edit.html", {
            "form": PatientEditForm(patient=patient),
            "patient": patient,
            "current_section": "patients",
        })

    def post(self, request, pk):
        patient = self.get_patient(pk)
        form = PatientEditForm(request.POST, patient=patient)
        if form.is_valid():
            with transaction.atomic():
                form.save()
            messages.success(request, _("Patient record updated successfully."))
            return redirect("reception:patient-detail", pk=patient.pk)

        messages.error(request, _("Could not update the patient record. Please check the form and try again."))
        return render(request, "reception/patient_edit.html", {
            "form": form,
            "patient": patient,
            "current_section": "patients",
        })


class PatientDetailView(LoginRequiredMixin, ReceptionistRequiredMixin, View):
    def get(self, request, pk):
        patient = get_object_or_404(
            User.objects.select_related("patient_profile"),
            pk=pk,
            role=User.Role.PATIENT,
        )
        appointments = Appointment.objects.filter(patient=patient).select_related(
            "doctor",
            "slot",
        ).order_by("-slot__date", "-slot__start_time")[:10]
        return render(request, "reception/patient_detail.html", {
            "patient": patient,
            "profile": patient.patient_profile,
            "appointments": appointments,
            "current_section": "patients",
        })


class UpdateAppointmentStatusView(LoginRequiredMixin, ReceptionistRequiredMixin, View):
    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        form = UpdateStatusForm(request.POST)

        if form.is_valid():
            new_status = form.cleaned_data['status']
            if new_status == Appointment.Status.COMPLETED:
                if appointment.status != Appointment.Status.CHECKED_IN:
                    messages.error(request, _("Only checked‑in appointments can be marked as completed."))
                    return redirect('dashboard')
            
            if new_status == Appointment.Status.CANCELLED:
                refund_info = process_appointment_refund(appointment, refund_percentage=Decimal("1.00"))
                
                slot = appointment.slot
                appointment.status = Appointment.Status.CANCELLED
                appointment.cancelled_by = request.user
                appointment.cancelled_at = timezone.now()
                appointment.save(update_fields=["status", "cancelled_by", "cancelled_at"])
                
                if not Appointment.objects.active().filter(slot_id=slot.id).exists():
                    slot.is_booked = False
                    slot.save(update_fields=["is_booked"])
                
                msg = f"Appointment for {appointment.patient} has been cancelled."
                if refund_info:
                    msg += f" A full refund of EGP {refund_info['refunded_amount']} has been processed."
                messages.success(request, msg)
            else:
                appointment.status = new_status
                appointment.save()
                name = appointment.patient.get_full_name() or appointment.patient.username
                messages.success(request, _("Status for {name} changed to {appointment.status}."))

        return redirect('dashboard')


class WalkInPatientCreateView(LoginRequiredMixin, ReceptionistRequiredMixin, View):
    def get(self, request):
        form = WalkInPatientForm()
        return render(request, 'reception/walk_in.html', {
            'form': form,
            'current_section': 'walkin'
        })

    def post(self, request):
        form = WalkInPatientForm(request.POST)

        if form.is_valid():
            walk_in = self.create_walk_in_patient(form)
            doctor = form.cleaned_data['doctor']
            patient_user = self.get_or_create_walk_in_user(walk_in)
            self.create_walk_in_appointment(patient_user, doctor)

            messages.success(request, _("Successfully registered {walk_in.name}!"))
            return redirect('dashboard')

        messages.error(request, _("Could not register the walk-in. Please check the data and try again."))
        return render(request, 'reception/walk_in.html', {
            'form': form,
            'current_section': 'walkin'
        })

    def create_walk_in_patient(self, form):
        return WalkInPatient.objects.create(
            name=form.cleaned_data['name'],
            phone_number=form.cleaned_data['phone_number'],
            notes=form.cleaned_data['notes'],
        )

    def get_or_create_walk_in_user(self, walk_in):
        username = f"walkin_{walk_in.id}"
        patient_user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@local',
                'role': 'PATIENT',
            },
        )
        if created:
            patient_user.set_unusable_password()
            patient_user.save()
        return patient_user

    def create_walk_in_appointment(self, patient_user, doctor):
        now = timezone.now()
        slot = AppointmentSlot.objects.create(
            doctor=doctor,
            date=now.date(),
            start_time=now.time(),
            end_time=(now + timedelta(minutes=30)).time(),
            is_booked=True,
        )
        return Appointment.objects.create(
            patient=patient_user,
            doctor=doctor,
            slot=slot,
            status=Appointment.Status.CHECKED_IN,
        )



class RescheduleAppointmentView(LoginRequiredMixin, ReceptionistRequiredMixin, View):
    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)

        if appointment.status in [Appointment.Status.CANCELLED, Appointment.Status.COMPLETED]:
            messages.error(request, _("Completed or cancelled appointments cannot be rescheduled."))
            return redirect('dashboard')

        form = RescheduleForm(request.POST)
        
        if form.is_valid():
            new_date = form.cleaned_data['new_date']
            new_start_time = form.cleaned_data['new_start_time']
            reason = form.cleaned_data['reason']

            old_slot = appointment.slot

            if old_slot.date == new_date and old_slot.start_time == new_start_time:
                messages.info(request, _("Please choose a different slot to reschedule."))
                return redirect('dashboard')
            
          
            new_slot, created = AppointmentSlot.objects.get_or_create(
                doctor=appointment.doctor,
                date=new_date,
                start_time=new_start_time,
                defaults={
                    'end_time': (timezone.datetime.combine(new_date, new_start_time) + timedelta(minutes=30)).time(),
                    'is_booked': False
                }
            )
            
            if not created and new_slot.is_booked:
                messages.error(request, _("The selected new slot is already booked."))
                return redirect('dashboard')

            try:
                with transaction.atomic():
                    appointment.slot = new_slot
                    appointment.save()

                    new_slot.is_booked = True
                    new_slot.save(update_fields=["is_booked"])

                    if not Appointment.objects.active().filter(slot_id=old_slot.id).exists():
                        old_slot.is_booked = False
                        old_slot.save(update_fields=["is_booked"])

                    RescheduleHistory.objects.create(
                        appointment=appointment,
                        old_slot=old_slot,
                        new_slot=new_slot,
                        changed_by=request.user,
                        reason=reason
                    )

                messages.success(request, _("Successfully rescheduled appointment for {appointment.patient}."))
            except ValidationError as exc:
                if hasattr(exc, "message_dict"):
                    errors = []
                    for field_errors in exc.message_dict.values():
                        errors.extend(field_errors)
                    message = errors[0] if errors else "Failed to reschedule due to validation rules."
                else:
                    message = exc.messages[0] if getattr(exc, "messages", None) else "Failed to reschedule due to validation rules."
                messages.error(request, message)
            except IntegrityError:
                messages.error(request, _("Could not reschedule due to a conflicting appointment. Please choose another slot."))
            
        else:
            messages.error(request, _("Failed to reschedule. Please check the form data."))
            
        return redirect('dashboard')
