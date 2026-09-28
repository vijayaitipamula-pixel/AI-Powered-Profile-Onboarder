from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Resume

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('id', 'profile', 'parsing_status', 'email_status', 'uploaded_at', 'processing_details')
    list_filter = ('parsing_status', 'email_status', 'uploaded_at')
    search_fields = ('profile__user__email', 'profile__first_name', 'profile__last_name')
    # No FileField widget: storage URLs must never expose private resumes.
    fields = ('profile', 'uploaded_by', 'original_filename', 'parsing_status', 'parsing_error',
              'email_status', 'email_error', 'uploaded_at', 'parsed_at', 'processing_details')
    readonly_fields = fields

    @admin.display(description='Resume and processing details')
    def processing_details(self, obj):
        return format_html('<a href="{}">View / download / retry</a>', reverse('resume_detail', args=[obj.pk]))

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
