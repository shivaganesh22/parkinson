from django.contrib import admin
from .models import UserProfile, Hospital, DetectionHistory, SuggestedHospital, EmailReport

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'city', 'created_at')
    search_fields = ('user__username', 'city')
    list_filter = ('gender', 'created_at')

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'specialization', 'rating', 'phone')
    search_fields = ('name', 'city', 'specialization')
    list_filter = ('city', 'rating')
    fieldsets = (
        ('Basic Info', {'fields': ('name', 'phone', 'email', 'specialization')}),
        ('Location', {'fields': ('address', 'city', 'state', 'lat', 'lon')}),
        ('Rating', {'fields': ('rating',)}),
    )

@admin.register(DetectionHistory)
class DetectionHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'detection_result', 'confidence', 'test_type', 'test_date')
    search_fields = ('user__username',)
    list_filter = ('detection_result', 'test_type', 'test_date')
    readonly_fields = ('test_date',)

@admin.register(SuggestedHospital)
class SuggestedHospitalAdmin(admin.ModelAdmin):
    list_display = ('detection', 'hospital', 'rank', 'added_at')
    search_fields = ('hospital__name', 'detection__user__username')
    list_filter = ('rank', 'added_at')

@admin.register(EmailReport)
class EmailReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipient_email', 'status', 'sent_at')
    search_fields = ('user__username', 'recipient_email')
    list_filter = ('status', 'sent_at')
