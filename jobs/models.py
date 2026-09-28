from django.db import models

class Job(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    required_skills = models.ManyToManyField('profiles.Skill', blank=True)
    location = models.CharField(max_length=150)
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = 'APPLIED', 'Applied'
        SHORTLISTED = 'SHORTLISTED', 'Shortlisted'
        REJECTED = 'REJECTED', 'Rejected'
        HIRED = 'HIRED', 'Hired'

    job = models.ForeignKey(Job, on_delete=models.PROTECT, related_name='applications')
    profile = models.ForeignKey('profiles.JobSeekerProfile', on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.APPLIED, db_index=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_at']
        constraints = [models.UniqueConstraint(fields=['job', 'profile'], name='one_application_per_candidate_job')]
