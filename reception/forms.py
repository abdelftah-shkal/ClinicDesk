from django.utils.translation import gettext_lazy as _
from django import forms
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.crypto import get_random_string

from appointments.models import Appointment
from accounts.models import PatientProfile
from accounts.forms import BLOOD_TYPE_CHOICES
from accounts.utils.verification_service import VerificationService

User = get_user_model()


class WalkInPatientForm(forms.Form):
    name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "walkin-input",
            "placeholder": "Patient full name",
        }),
    )
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            "class": "walkin-input",
            "placeholder": "Phone number",
        }),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": "walkin-input walkin-textarea",
            "placeholder": "Optional notes",
            "rows": 3,
        }),
    )
    doctor = forms.ModelChoiceField(
        queryset=User.objects.filter(role='DOCTOR'),
        widget=forms.Select(attrs={"class": "walkin-input"}),
    )


class UpdateStatusForm(forms.Form):
    STATUS_CHOICES = [
        (Appointment.Status.CONFIRMED, 'Confirmed'),
        (Appointment.Status.CHECKED_IN, 'Checked In'),
        (Appointment.Status.CANCELLED, 'Cancelled'),
        (Appointment.Status.COMPLETED, 'Completed'),
    ]
    status = forms.ChoiceField(choices=STATUS_CHOICES)



class RescheduleForm(forms.Form):
    new_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "walkin-input", "type": "date"}),
    )
    new_start_time = forms.TimeField(
        widget=forms.Select(attrs={"class": "walkin-input time-select"}),
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            "class": "walkin-input walkin-textarea",
            "placeholder": "Reason for rescheduling",
            "rows": 2,
        }),
    )


class PatientRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "walkin-input"}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "walkin-input"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "walkin-input"}))
    phone_number = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={"class": "walkin-input"}))
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={"class": "walkin-input", "type": "date"}))
    blood_type = forms.ChoiceField(choices=[("", "Not set")] + BLOOD_TYPE_CHOICES, required=False, widget=forms.Select(attrs={"class": "walkin-input"}))
    gender = forms.ChoiceField(choices=[("", "Not set")] + list(PatientProfile._meta.get_field("gender").choices), required=False, widget=forms.Select(attrs={"class": "walkin-input"}))
    allergies = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "walkin-input walkin-textarea", "rows": 3}))
    medical_history = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "walkin-input walkin-textarea", "rows": 4}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "walkin-input walkin-textarea", "rows": 3}))
    emergency_contact_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={"class": "walkin-input"}))
    emergency_contact_phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={"class": "walkin-input"}))

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("A user with this email already exists."))
        return email

    def _generate_username(self, email):
        base_username = email.split("@", 1)[0] or "patient"
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            counter += 1
            username = f"{base_username}{counter}"
        return username

    def save(self):
        email = self.cleaned_data["email"]
        user = User(
            username=self._generate_username(email),
            email=email,
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            phone_number=self.cleaned_data["phone_number"],
            role=User.Role.PATIENT,
            is_active=False,
        )
        user.set_password(get_random_string(32))
        user.save()
        PatientProfile.objects.create(
            user=user,
            date_of_birth=self.cleaned_data["date_of_birth"],
            blood_type=self.cleaned_data["blood_type"],
            gender=self.cleaned_data["gender"],
            allergies=self.cleaned_data["allergies"],
            medical_history=self.cleaned_data["medical_history"],
            address=self.cleaned_data["address"],
            emergency_contact_name=self.cleaned_data["emergency_contact_name"],
            emergency_contact_phone=self.cleaned_data["emergency_contact_phone"],
        )
        self._send_activation_email(user)
        return user

    def _send_activation_email(self, user):
        verification_link = VerificationService.generate_link(user)
        html_content = render_to_string(
            "emails/activate_account.html",
            {
                "user": user,
                "verification_link": verification_link,
            },
        )
        email = EmailMultiAlternatives(
            subject="Activate Your Account",
            body="Please activate your account.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()


class PatientEditForm(forms.Form):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "walkin-input"}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"class": "walkin-input"}))
    phone_number = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={"class": "walkin-input"}))
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={"class": "walkin-input", "type": "date"}))
    blood_type = forms.ChoiceField(choices=[("", "Not set")] + BLOOD_TYPE_CHOICES, required=False, widget=forms.Select(attrs={"class": "walkin-input"}))
    gender = forms.ChoiceField(choices=[("", "Not set")] + list(PatientProfile._meta.get_field("gender").choices), required=False, widget=forms.Select(attrs={"class": "walkin-input"}))
    allergies = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "walkin-input walkin-textarea", "rows": 3}))
    medical_history = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "walkin-input walkin-textarea", "rows": 4}))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "walkin-input walkin-textarea", "rows": 3}))
    emergency_contact_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={"class": "walkin-input"}))
    emergency_contact_phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={"class": "walkin-input"}))

    def __init__(self, *args, patient=None, **kwargs):
        self.patient = patient
        if patient is not None and "initial" not in kwargs:
            profile = patient.patient_profile
            kwargs["initial"] = {
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "phone_number": patient.phone_number,
                "date_of_birth": profile.date_of_birth,
                "blood_type": profile.blood_type,
                "gender": profile.gender,
                "allergies": profile.allergies,
                "medical_history": profile.medical_history,
                "address": profile.address,
                "emergency_contact_name": profile.emergency_contact_name,
                "emergency_contact_phone": profile.emergency_contact_phone,
            }
        super().__init__(*args, **kwargs)

    def save(self):
        profile = self.patient.patient_profile
        self.patient.first_name = self.cleaned_data["first_name"]
        self.patient.last_name = self.cleaned_data["last_name"]
        self.patient.phone_number = self.cleaned_data["phone_number"]
        self.patient.save(update_fields=["first_name", "last_name", "phone_number"])

        profile.date_of_birth = self.cleaned_data["date_of_birth"]
        profile.blood_type = self.cleaned_data["blood_type"]
        profile.gender = self.cleaned_data["gender"]
        profile.allergies = self.cleaned_data["allergies"]
        profile.medical_history = self.cleaned_data["medical_history"]
        profile.address = self.cleaned_data["address"]
        profile.emergency_contact_name = self.cleaned_data["emergency_contact_name"]
        profile.emergency_contact_phone = self.cleaned_data["emergency_contact_phone"]
        profile.save()
        return self.patient
