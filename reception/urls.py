from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'reception'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='dashboard', permanent=False), name='traffic_board'),
    path('patients/', views.PatientListView.as_view(), name='patient-list'),
    path('patients/create/', views.PatientCreateView.as_view(), name='patient-create'),
    path('patients/<int:pk>/', views.PatientDetailView.as_view(), name='patient-detail'),
    path('patients/<int:pk>/edit/', views.PatientEditView.as_view(), name='patient-edit'),
    path('update-status/<int:pk>/', views.UpdateAppointmentStatusView.as_view(), name='update_status'),
    path('walk-in/', views.WalkInPatientCreateView.as_view(), name='walk_in'),
    path('reschedule/<int:pk>/', views.RescheduleAppointmentView.as_view(), name='reschedule'),
]
