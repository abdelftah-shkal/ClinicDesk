from django.utils.translation import gettext_lazy as _
import datetime
from django.db import models
from django.conf import settings

class ClinicSettings(models.Model):
    clinic_name = models.CharField(max_length=200, default='CareFlow Clinic')
    clinic_address = models.TextField(blank=True, default='Clinic Address')
    clinic_phone = models.CharField(max_length=20, blank=True, default='+123456789')
    clinic_email = models.EmailField(blank=True, default='info@clinic.com')
    logo = models.ImageField(upload_to='clinic/', blank=True, null=True)
    working_days = models.JSONField(default=list, blank=True)
    opening_time = models.TimeField(default=datetime.time(9, 0))
    closing_time = models.TimeField(default=datetime.time(17, 0))
    default_slot_duration = models.PositiveIntegerField(default=30)
    currency = models.CharField(max_length=10, default='EGP')

    class Meta:
        verbose_name=_("Clinic Settings")
        verbose_name_plural = "Clinic Settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return self.clinic_name


class ClinicService(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='bi-heart-pulse')
    price_range = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    doctors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        limit_choices_to={'role': 'DOCTOR'},
        blank=True,
        related_name='services'
    )

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name=_("Clinic Service")
        verbose_name_plural = "Clinic Services"

    def __str__(self):
        return self.name
