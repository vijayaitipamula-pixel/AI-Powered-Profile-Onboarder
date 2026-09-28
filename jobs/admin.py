from django.contrib import admin
from .models import Application, Job

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'active', 'created_at')
    list_filter = ('active', 'location')
    search_fields = ('title', 'description')
    filter_horizontal = ('required_skills',)

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('profile', 'job', 'status', 'applied_at')
    list_filter = ('status', 'job')
    search_fields = ('profile__user__email', 'profile__first_name', 'job__title')
    readonly_fields = ('profile', 'job', 'applied_at', 'updated_at')

    def has_add_permission(self, request):
        return False
