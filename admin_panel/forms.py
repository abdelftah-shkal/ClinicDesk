from django.utils.translation import gettext_lazy as _
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from accounts.models import CustomUser, DoctorProfile, PatientProfile

class AdminUserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, validators=[validate_password])
    
    # Doctor Fields
    specialty = forms.CharField(max_length=100, required=False)
    bio = forms.CharField(widget=forms.Textarea, required=False)
    consultation_fee = forms.DecimalField(max_digits=8, decimal_places=2, required=False, initial=0)
    
    # Patient Fields
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False, initial=timezone.now().date)
    blood_type = forms.CharField(max_length=5, required=False)
    gender = forms.ChoiceField(choices=PatientProfile._meta.get_field('gender').choices, required=False)
    allergies = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    medical_history = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    emergency_contact_name = forms.CharField(max_length=100, required=False)
    emergency_contact_phone = forms.CharField(max_length=20, required=False)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'role', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.is_active = True
        if commit:
            user.save()
            self._save_profile(user)
        return user

    def _save_profile(self, user):
        if user.role == 'DOCTOR':
            DoctorProfile.objects.update_or_create(
                user=user,
                defaults={
                    'specialty': self.cleaned_data.get('specialty', ''),
                    'bio': self.cleaned_data.get('bio', ''),
                    'consultation_fee': self.cleaned_data.get('consultation_fee') or 0,
                }
            )
        elif user.role == 'PATIENT':
            PatientProfile.objects.update_or_create(
                user=user,
                defaults={
                    'date_of_birth': self.cleaned_data.get('date_of_birth') or timezone.now().date(),
                    'blood_type': self.cleaned_data.get('blood_type', ''),
                    'gender': self.cleaned_data.get('gender') or '',
                    'allergies': self.cleaned_data.get('allergies') or '',
                    'medical_history': self.cleaned_data.get('medical_history') or '',
                    'address': self.cleaned_data.get('address') or '',
                    'emergency_contact_name': self.cleaned_data.get('emergency_contact_name') or '',
                    'emergency_contact_phone': self.cleaned_data.get('emergency_contact_phone') or '',
                }
            )


class AdminUserEditForm(forms.ModelForm):
    # Doctor Fields
    specialty = forms.CharField(max_length=100, required=False)
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    consultation_fee = forms.DecimalField(max_digits=8, decimal_places=2, required=False)
    
    # Patient Fields
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    blood_type = forms.CharField(max_length=5, required=False)
    gender = forms.ChoiceField(choices=PatientProfile._meta.get_field('gender').choices, required=False)
    allergies = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    medical_history = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    emergency_contact_name = forms.CharField(max_length=100, required=False)
    emergency_contact_phone = forms.CharField(max_length=20, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'role', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if hasattr(self.instance, 'doctor_profile'):
                self.fields['specialty'].initial = self.instance.doctor_profile.specialty
                self.fields['bio'].initial = self.instance.doctor_profile.bio
                self.fields['consultation_fee'].initial = self.instance.doctor_profile.consultation_fee
            if hasattr(self.instance, 'patient_profile'):
                self.fields['date_of_birth'].initial = self.instance.patient_profile.date_of_birth
                self.fields['blood_type'].initial = self.instance.patient_profile.blood_type
                self.fields['gender'].initial = self.instance.patient_profile.gender
                self.fields['allergies'].initial = self.instance.patient_profile.allergies
                self.fields['medical_history'].initial = self.instance.patient_profile.medical_history
                self.fields['address'].initial = self.instance.patient_profile.address
                self.fields['emergency_contact_name'].initial = self.instance.patient_profile.emergency_contact_name
                self.fields['emergency_contact_phone'].initial = self.instance.patient_profile.emergency_contact_phone

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            self._save_profile(user)
        return user

    def _save_profile(self, user):
        if user.role == 'DOCTOR':
            DoctorProfile.objects.update_or_create(
                user=user,
                defaults={
                    'specialty': self.cleaned_data.get('specialty') or '',
                    'bio': self.cleaned_data.get('bio') or '',
                    'consultation_fee': self.cleaned_data.get('consultation_fee') or 0,
                }
            )
        elif user.role == 'PATIENT':
            PatientProfile.objects.update_or_create(
                user=user,
                defaults={
                    'date_of_birth': self.cleaned_data.get('date_of_birth') or timezone.now().date(),
                    'blood_type': self.cleaned_data.get('blood_type') or '',
                    'gender': self.cleaned_data.get('gender') or '',
                    'allergies': self.cleaned_data.get('allergies') or '',
                    'medical_history': self.cleaned_data.get('medical_history') or '',
                    'address': self.cleaned_data.get('address') or '',
                    'emergency_contact_name': self.cleaned_data.get('emergency_contact_name') or '',
                    'emergency_contact_phone': self.cleaned_data.get('emergency_contact_phone') or '',
                }
            )


DAYS_OF_WEEK = (
    ('0', 'Monday'),
    ('1', 'Tuesday'),
    ('2', 'Wednesday'),
    ('3', 'Thursday'),
    ('4', 'Friday'),
    ('5', 'Saturday'),
    ('6', 'Sunday'),
)

from clinic.models import ClinicSettings, ClinicService

class ClinicSettingsForm(forms.ModelForm):
    working_days = forms.MultipleChoiceField(
        choices=DAYS_OF_WEEK,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        help_text=_("Select the working days of the clinic.")
    )

    class Meta:
        model = ClinicSettings
        fields = [
            'clinic_name', 'clinic_address', 'clinic_phone', 'clinic_email',
            'logo', 'working_days', 'opening_time', 'closing_time',
            'default_slot_duration', 'currency'
        ]
        widgets = {
            'clinic_name': forms.TextInput(attrs={'class': 'form-control'}),
            'clinic_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'clinic_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'clinic_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'opening_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'closing_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'default_slot_duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            days = self.instance.working_days
            if isinstance(days, list):
                self.fields['working_days'].initial = [str(d) for d in days]

    def clean_working_days(self):
        days = self.cleaned_data.get('working_days', [])
        return [int(d) for d in days]


class ServiceForm(forms.ModelForm):
    class Meta:
        model = ClinicService
        fields = ['name', 'description', 'icon', 'price_range', 'is_active', 'display_order', 'doctors']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. bi-heart-pulse'}),
            'price_range': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 200 - 500 EGP'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'doctors': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }

