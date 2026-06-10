from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.UserListView.as_view(), name='admin-users'),
    path('users/create/', views.UserCreateView.as_view(), name='admin-user-create'),
    path('users/<int:pk>/edit/', views.UserEditView.as_view(), name='admin-user-edit'),
    path('users/<int:pk>/toggle-active/', views.UserToggleActiveView.as_view(), name='admin-user-toggle'),
    path('analytics/export/', views.AnalyticsExportView.as_view(), name='admin-analytics-export'),
    path('settings/', views.ClinicSettingsView.as_view(), name='admin-clinic-settings'),
    path('services/', views.ServiceListView.as_view(), name='admin-services'),
    path('services/create/', views.ServiceCreateView.as_view(), name='admin-service-create'),
    path('services/<int:pk>/edit/', views.ServiceEditView.as_view(), name='admin-service-edit'),
    path('services/<int:pk>/delete/', views.ServiceDeleteView.as_view(), name='admin-service-delete'),
    path('reports/appointments/', views.AppointmentReportView.as_view(), name='admin-report-appointments'),
    path('reports/billing/', views.BillingReportView.as_view(), name='admin-report-billing'),
    path('reports/patient-activity/', views.PatientActivityReportView.as_view(), name='admin-report-patient-activity'),
    path('reports/disease-statistics/', views.DiseaseStatisticsReportView.as_view(), name='admin-report-disease-statistics'),
]
