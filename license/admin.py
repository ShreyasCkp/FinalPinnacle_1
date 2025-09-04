from django.contrib import admin
from .models import License

@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ['license_key', 'start_date', 'end_date', 'activated']
    list_filter = ['activated']
    search_fields = ['license_key']
