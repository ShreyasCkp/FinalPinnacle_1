from django.contrib import admin
from .models import License
from django.utils import timezone

@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ['license_key', 'client_name', 'start_date', 'end_date', 'activated', 'is_valid_display', 'days_remaining']
    list_filter = ['activated', 'start_date', 'end_date']
    search_fields = ['license_key', 'client_name']
    date_hierarchy = 'start_date'
    readonly_fields = ['is_valid_display', 'days_remaining']
    
    fieldsets = (
        ('License Information', {
            'fields': ('license_key', 'client_name', 'activated')
        }),
        ('Validity Period', {
            'fields': ('start_date', 'end_date', 'is_valid_display', 'days_remaining')
        }),
    )
    
    def is_valid_display(self, obj):
        """Display license validity status"""
        if not obj.start_date or not obj.end_date:
            return "N/A"
        if obj.is_valid():
            return "✅ Valid"
        elif obj.end_date < timezone.localdate():
            return "❌ Expired"
        elif obj.start_date > timezone.localdate():
            return "⏳ Not Started"
        else:
            return "❌ Inactive"
    is_valid_display.short_description = 'Status'
    
    def days_remaining(self, obj):
        """Display days remaining until expiration"""
        if obj.end_date:
            days = (obj.end_date - timezone.localdate()).days
            if days < 0:
                return f"Expired {abs(days)} days ago"
            elif days == 0:
                return "Expires today"
            elif days <= 7:
                return f"⚠️ {days} days remaining"
            else:
                return f"{days} days remaining"
        return "N/A"
    days_remaining.short_description = 'Days Remaining'
    
    def save_model(self, request, obj, form, change):
        """Override save to ensure license key is unique"""
        super().save_model(request, obj, form, change)
