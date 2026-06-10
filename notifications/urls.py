from django.urls import path
from notifications.views import (
    NotificationListView,
    mark_notification_read,
    mark_all_read,
    unread_count,
)

app_name = "notifications"

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification-list"),
    path("<int:pk>/read/", mark_notification_read, name="notification-mark-read"),
    path("read-all/", mark_all_read, name="notification-mark-all-read"),
    path("unread-count/", unread_count, name="notification-unread-count"),
]
