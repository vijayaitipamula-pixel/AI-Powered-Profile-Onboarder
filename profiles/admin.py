from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from .forms import ProfileForm
from .models import Award, Certification, JobSeekerProfile, Project, Score, Skill, StatusHistory, User
from .services import change_status, refresh_profile


class ScoreRangeFilter(admin.SimpleListFilter):
    title = 'profile score'
    parameter_name = 'score_range'

    def lookups(self, request, model_admin):
        return [('high', '80–100'), ('medium', '50–79'), ('low', '0–49')]

    def queryset(self, request, queryset):
        if self.value() == 'high':
            return queryset.filter(score__total_score__gte=80)
        if self.value() == 'medium':
            return queryset.filter(score__total_score__gte=50, score__total_score__lt=80)
        if self.value() == 'low':
            return queryset.filter(models.Q(score__total_score__lt=50) | models.Q(score__isnull=True))
        return queryset


@admin.register(User)
class AccountAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('Onboarding', {'fields': ('must_change_password', 'temporary_password_expires_at')}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('Contact', {'fields': ('email',)}),)
    readonly_fields = ('must_change_password', 'temporary_password_expires_at')


class ProjectInline(admin.StackedInline):
    model = Project
    extra = 0

class CertificationInline(admin.TabularInline):
    model = Certification
    extra = 0

class AwardInline(admin.TabularInline):
    model = Award
    extra = 0

class HistoryInline(admin.TabularInline):
    model = StatusHistory
    fields = ('previous_status', 'new_status', 'changed_by', 'changed_at', 'reason')
    readonly_fields = fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(JobSeekerProfile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'candidate_email', 'profile_status', 'experience_type', 'experience_years', 'score_value')
    list_filter = ('profile_status', 'experience_type', ScoreRangeFilter, 'skills')
    search_fields = ('first_name', 'last_name', 'user__email', 'skills__name', 'current_role')
    readonly_fields = ('user', 'profile_status', 'masked_aadhaar', 'confirmed_at', 'created_at', 'updated_at')
    exclude = ('aadhaar_last_four',)
    filter_horizontal = ('skills',)
    inlines = [ProjectInline, CertificationInline, AwardInline, HistoryInline]
    actions = ['mark_reviewed', 'mark_not_interested']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'score')

    @admin.display(description='Email')
    def candidate_email(self, obj):
        return obj.user.email

    @admin.display(description='Score')
    def score_value(self, obj):
        return obj.score.total_score if hasattr(obj, 'score') else 0

    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        # Staff edits need candidate confirmation again.
        obj.confirmed_at = None
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        refresh_profile(form.instance, request.user)

    @admin.action(description='Mark reviewed (automatically opens complete, confirmed profiles)', permissions=['change'])
    def mark_reviewed(self, request, queryset):
        for profile in queryset:
            change_status(profile, JobSeekerProfile.Status.REVIEWED, request.user)
        self.message_user(request, 'Profiles reviewed and completeness checked.', messages.SUCCESS)

    @admin.action(description='Mark not interested', permissions=['change'])
    def mark_not_interested(self, request, queryset):
        for profile in queryset:
            change_status(profile, JobSeekerProfile.Status.NOT_INTERESTED, request.user)


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ('profile', 'total_score', 'calculated_at')
    readonly_fields = ('profile', 'total_score', 'components', 'suggestions', 'calculated_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('profile', 'previous_status', 'new_status', 'changed_by', 'changed_at')
    readonly_fields = ('profile', 'previous_status', 'new_status', 'changed_by', 'changed_at', 'reason')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(Skill)
admin.site.site_header = 'Profile Onboarder administration'
