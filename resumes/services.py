import secrets
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.mail import EmailMultiAlternatives
from django.db import IntegrityError, transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from profiles.models import Award, Certification, JobSeekerProfile, Project, Skill, StatusHistory, User
from profiles.services import refresh_profile
from .ai import OpenAIResumeParser, validate_result
from .extraction import extract_text, mask_aadhaar, validate_pdf
from .models import Resume


def may_manage_uploads(actor):
    return actor.is_staff and actor.has_perm('resumes.add_resume') and actor.has_perm('profiles.change_jobseekerprofile')


@sensitive_variables()
def send_onboarding(resume, temporary_password=None):
    context = {'user': resume.profile.user, 'temporary_password': temporary_password,
        'login_url': settings.SITE_URL + reverse('login'),
        'reset_url': settings.SITE_URL + reverse('password_reset'), 'hours': settings.TEMP_PASSWORD_HOURS}
    try:
        email = EmailMultiAlternatives('Your profile is ready for review',
            render_to_string('emails/onboarding.txt', context), settings.DEFAULT_FROM_EMAIL,
            [resume.profile.user.email])
        email.attach_alternative(render_to_string('emails/onboarding.html', context), 'text/html')
        if email.send(fail_silently=False) != 1:
            raise RuntimeError('No message sent')
    except Exception:
        # The committed profile survives email failure. Resending uses password reset,
        # never a stored plaintext password or a reset of an existing account's password.
        resume.email_status = 'FAILED'
        resume.email_error = 'Email delivery failed. Check email configuration and resend login information.'
    else:
        resume.email_status = 'SENT'
        resume.email_error = ''
    resume.save(update_fields=['email_status', 'email_error'])


@sensitive_variables()
@transaction.atomic
def save_candidate(resume, parsed, actor):
    user = User.objects.select_for_update().filter(email__iexact=parsed.email).first()
    owner_upload = not may_manage_uploads(actor)
    if owner_upload and parsed.email != actor.email.lower():
        raise ValidationError('The resume email must match your signed-in account. Contact staff for email corrections.')
    if user and (user.is_staff or user.is_superuser):
        raise ValidationError('This email belongs to a staff account. Use a candidate email.')
    password = None
    if not user:
        if owner_upload:
            raise PermissionDenied
        password = secrets.token_urlsafe(24)
        user = User.objects.create_user(username=parsed.email, email=parsed.email, password=password,
            must_change_password=True, temporary_password_expires_at=timezone.now() + timedelta(hours=settings.TEMP_PASSWORD_HOURS))
    profile, created = JobSeekerProfile.objects.select_for_update().get_or_create(user=user)
    if created:
        StatusHistory.objects.create(profile=profile, previous_status='', new_status=profile.profile_status,
                                     changed_by=actor, reason='Profile created from resume; review required.')
    # A repeat upload replaces parsed data only before the candidate has confirmed it.
    # Confirmed profiles remain editable by their owner and are never silently overwritten.
    if created or not profile.confirmed_at:
        fields = parsed.model_dump(exclude={'email', 'aadhaar_number', 'skills', 'projects', 'certifications', 'awards'})
        fields['experience_type'] = fields['experience_type'] or ''
        if fields['experience_years'] is not None:
            fields['experience_years'] = Decimal(str(fields['experience_years'])).quantize(Decimal('0.1'))
        for name, value in fields.items():
            setattr(profile, name, value)
        profile.aadhaar_last_four = parsed.aadhaar_number[-4:] if parsed.aadhaar_number else ''
        profile.full_clean()
        profile.save()
        profile.skills.set([Skill.objects.get_or_create(name=name)[0] for name in parsed.skills])
        for model, relation in [(Project, 'projects'), (Certification, 'certifications'), (Award, 'awards')]:
            getattr(profile, relation).all().delete()
            for item in getattr(parsed, relation):
                model.objects.create(profile=profile, **item.model_dump())
    resume.profile = profile
    resume.parsing_status = Resume.Status.PARSED
    resume.parsing_error = ''
    resume.parsed_at = timezone.now()
    resume.save(update_fields=['profile', 'parsing_status', 'parsing_error', 'parsed_at'])
    refresh_profile(profile, actor)
    transaction.on_commit(lambda: send_onboarding(resume, password))
    return profile


@sensitive_variables()
def process_resume(resume, actor, parser=None):
    if not may_manage_uploads(actor) and resume.uploaded_by_id != actor.pk:
        raise PermissionDenied
    claimed = Resume.objects.filter(pk=resume.pk, parsing_status__in=[Resume.Status.PENDING, Resume.Status.FAILED]).update(
        parsing_status=Resume.Status.PROCESSING, parsing_error='')
    if not claimed:
        raise ValidationError('This resume is already processing or has been parsed.')
    resume.refresh_from_db()
    try:
        with resume.uploaded_file.open('rb') as file:
            text = extract_text(file)
        resume.extracted_text = mask_aadhaar(text)
        resume.save(update_fields=['extracted_text'])
        parsed = validate_result((parser or OpenAIResumeParser()).parse(text), text)
        save_candidate(resume, parsed, actor)
    except ValidationError as error:
        resume.parsing_status = Resume.Status.FAILED
        # Only application-owned validation messages are exposed; model errors can hold values.
        resume.parsing_error = error.messages[0] if not hasattr(error, 'error_dict') else 'Extracted fields failed validation. Review the resume.'
        resume.save(update_fields=['parsing_status', 'parsing_error'])
    except IntegrityError:
        resume.parsing_status = Resume.Status.FAILED
        resume.parsing_error = 'Account data conflicts with an existing record. Ask staff to review and retry.'
        resume.save(update_fields=['parsing_status', 'parsing_error'])
    except Exception:
        resume.parsing_status = Resume.Status.FAILED
        resume.parsing_error = 'Resume processing failed unexpectedly. Ask staff to check the service and retry.'
        resume.save(update_fields=['parsing_status', 'parsing_error'])
    return resume


def upload_resume(upload, actor, parser=None):
    if not may_manage_uploads(actor) and not hasattr(actor, 'profile'):
        raise PermissionDenied
    validate_pdf(upload)
    resume = Resume.objects.create(uploaded_file=upload, original_filename=Path(upload.name).name[:255],
        uploaded_by=actor, profile=getattr(actor, 'profile', None) if not may_manage_uploads(actor) else None)
    return process_resume(resume, actor, parser)
