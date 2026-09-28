from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .models import JobSeekerProfile, Score, StatusHistory

# Explicit, deterministic weights. Sensitive identity fields never affect employability.
WEIGHTS = {'personal': 20, 'experience': 20, 'skills': 20, 'projects': 15,
           'credentials': 5, 'preferred_role': 10, 'preferred_city': 10}


def calculate_score(profile):
    personal = sum(bool(v) for v in [profile.first_name, profile.user.email, profile.mobile_number, profile.current_city]) / 4
    experience = (1 if profile.experience_type == 'Fresher' else
                  sum(bool(v) for v in [profile.experience_type, profile.experience_years is not None,
                                       profile.current_role, profile.experience_summary]) / 4)
    fractions = {'personal': personal, 'experience': experience,
        'skills': min(profile.skills.count() / 3, 1), 'projects': min(profile.projects.count() / 2, 1),
        'credentials': int(profile.certifications.exists() or profile.awards.exists()),
        'preferred_role': int(bool(profile.preferred_role)), 'preferred_city': int(bool(profile.preferred_city))}
    components = {key: round(WEIGHTS[key] * value) for key, value in fractions.items()}
    hints = {'personal': 'Add your name, phone and current city.',
        'experience': 'Specify fresher status or complete your experience details.',
        'skills': 'Add up to three relevant skills.', 'projects': 'Describe up to two projects, if applicable.',
        'credentials': 'Add certifications or awards, if applicable.',
        'preferred_role': 'Add your preferred role.', 'preferred_city': 'Add your preferred location.'}
    suggestions = [hints[key] for key, value in fractions.items() if value < 1]
    if not profile.confirmed_at:
        suggestions.insert(0, 'Review and confirm the extracted information.')
    score, _ = Score.objects.update_or_create(profile=profile, defaults={
        'total_score': sum(components.values()), 'components': components, 'suggestions': suggestions})
    return score


def ready_for_work(profile):
    return bool(profile.confirmed_at and profile.first_name and profile.mobile_number
        and profile.current_city and profile.preferred_city and profile.preferred_role
        and profile.experience_type and profile.skills.exists()
        and (profile.experience_type == 'Fresher' or
             (profile.experience_years is not None and profile.current_role and profile.experience_summary)))


def _record_transition(profile, status, actor, reason):
    if profile.profile_status == status:
        return
    previous = profile.profile_status
    profile.profile_status = status
    profile.save(update_fields=['profile_status', 'updated_at'])
    StatusHistory.objects.create(profile=profile, previous_status=previous, new_status=status,
                                 changed_by=actor, reason=reason)


@transaction.atomic
def refresh_profile(profile, actor=None):
    profile = JobSeekerProfile.objects.select_for_update().get(pk=profile.pk)
    score = calculate_score(profile)
    if profile.profile_status != JobSeekerProfile.Status.NOT_INTERESTED:
        if ready_for_work(profile):
            _record_transition(profile, JobSeekerProfile.Status.OPEN_TO_WORK, actor, 'Required information confirmed and complete.')
        elif profile.profile_status == JobSeekerProfile.Status.OPEN_TO_WORK:
            _record_transition(profile, JobSeekerProfile.Status.REVIEWED, actor, 'Required information is incomplete or needs confirmation.')
    return score


@transaction.atomic
def change_status(profile, status, actor):
    profile = JobSeekerProfile.objects.select_for_update().get(pk=profile.pk)
    staff = actor.is_staff and actor.has_perm('profiles.change_jobseekerprofile')
    if status == JobSeekerProfile.Status.NOT_INTERESTED:
        if actor.pk != profile.user_id and not staff:
            raise PermissionDenied
    elif status == JobSeekerProfile.Status.REVIEWED:
        if not staff:
            raise PermissionDenied
    else:
        raise ValidationError('Open to work is calculated automatically; choose Reviewed or Not interested.')
    _record_transition(profile, status, actor, 'Status selected by candidate or reviewer.')
    refresh_profile(profile, actor)
