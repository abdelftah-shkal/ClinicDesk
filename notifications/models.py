from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        APPOINTMENT = "APPOINTMENT", _("Appointment")
        PAYMENT = "PAYMENT", _("Payment")
        REMINDER = "REMINDER", _("Reminder")
        SYSTEM = "SYSTEM", _("System")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=200, default="Notification")
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
    )
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return f"{self.title}: {self.message[:50]}"

    @classmethod
    def create_notification(cls, user, title, message, notification_type, link=""):
        return cls.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            link=link,
        )

