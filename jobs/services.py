from django.core.exceptions import ValidationError
from django.db import transaction
from profiles.models import JobSeekerProfile
from profiles.services import ready_for_work
from .models import Application, Job

@transaction.atomic
def apply_for_job(profile, job):
    profile = JobSeekerProfile.objects.select_for_update().get(pk=profile.pk)
    job = Job.objects.select_for_update().get(pk=job.pk)
    if not job.active:
        raise ValidationError('This job is no longer accepting applications.')
    if profile.profile_status != JobSeekerProfile.Status.OPEN_TO_WORK or not ready_for_work(profile):
        raise ValidationError('Review and complete your profile before applying. Your status must be Open to work.')
    return Application.objects.get_or_create(profile=profile, job=job)
