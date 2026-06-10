from django.contrib import admin
from .models import ClinicSettings, ClinicService

@admin.register(ClinicSettings)
class ClinicSettingsAdmin(admin.ModelAdmin):
    list_display = ('clinic_name', 'clinic_phone', 'clinic_email', 'opening_time', 'closing_time')
    
    def has_add_permission(self, request):
        # Prevent adding more than one instance
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        # Prevent deleting the settings
        return False


@admin.register(ClinicService)
class ClinicServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_range', 'is_active', 'display_order')
    list_editable = ('is_active', 'display_order')
    search_fields = ('name', 'description')
    filter_horizontal = ('doctors',)
