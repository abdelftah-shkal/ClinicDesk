from django.urls import path
from . import views

app_name = "emr"

urlpatterns = [
    path("queue/", views.DoctorDailyQueueView.as_view(), name="daily-queue"),
    path("consultations/", views.ConsultationListView.as_view(), name="consultations-list"),
    path("consultation/<int:appointment_id>/", views.ConsultationCreateView.as_view(), name="consultation-create"),
    path("consultation/<int:appointment_id>/summary/", views.PatientConsultationSummaryView.as_view(), name="patient-consultation-summary"),
    path("patient/<int:patient_id>/history/", views.PatientMedicalHistoryView.as_view(), name="patient-medical-history"),
    path("schedule/", views.ManageScheduleView.as_view(), name="manage-schedule"),
    path("my-prescriptions/", views.PatientPrescriptionsListView.as_view(), name="patient-prescriptions"),
    path("prescription/<int:consultation_id>/print/", views.PrescriptionPrintView.as_view(), name="prescription-print"),
]
