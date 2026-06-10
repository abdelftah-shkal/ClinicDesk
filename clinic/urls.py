
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from accounts.views import OnboardingView
from clinic.views import favicon, DynamicHomeView, PublicDoctorsListView, PublicServicesView

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('favicon.ico', favicon),
    path('favicon.svg', favicon),
]

urlpatterns += i18n_patterns(
    path('', DynamicHomeView.as_view(), name='home'),
    path('doctors/', PublicDoctorsListView.as_view(), name='public-doctors'),
    path('services/', PublicServicesView.as_view(), name='public-services'),
    path('onboarding/', OnboardingView.as_view(), name='onboarding'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('appointments/', include('appointments.urls')),
    path('reception/', include('reception.urls')),
    path('emr/', include('emr.urls')),
    path('payments/', include('payments.urls')),
    path('admin-panel/', include('admin_panel.urls')),
    path('notifications/', include('notifications.urls')),
)


if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static
    urlpatterns = [
        path('debug/', include(debug_toolbar.urls)),
    ] + urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)