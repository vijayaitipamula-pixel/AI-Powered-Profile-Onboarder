import uuid
from django.conf import settings
from django.db import models

def resume_path(instance, filename):
    return f'resumes/{uuid.uuid4().hex}.pdf'

class Resume(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        PARSED = 'PARSED', 'Parsed'
        FAILED = 'FAILED', 'Failed'

    profile = models.ForeignKey('profiles.JobSeekerProfile', on_delete=models.CASCADE, null=True, blank=True, related_name='resumes')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_file = models.FileField(upload_to=resume_path)
    original_filename = models.CharField(max_length=255)
    extracted_text = models.TextField(blank=True)
    parsing_status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)
    parsing_error = models.CharField(max_length=300, blank=True)
    email_status = models.CharField(max_length=12, default='NOT_SENT', choices=[('NOT_SENT', 'Not sent'), ('SENT', 'Sent'), ('FAILED', 'Failed')])
    email_error = models.CharField(max_length=300, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    parsed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']
