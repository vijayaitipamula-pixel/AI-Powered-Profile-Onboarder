from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models.functions import Lower


class User(AbstractUser):
    username = models.CharField(max_length=254, unique=True)
    email = models.EmailField(unique=True)
    must_change_password = models.BooleanField(default=False)
    temporary_password_expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(Lower('email'), name='user_email_case_insensitive')]

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        self.username = self.username.strip().lower()
        super().save(*args, **kwargs)


class JobSeekerProfile(models.Model):
    class Status(models.TextChoices):
        CREATED = 'CREATED', 'Created'
        REVIEWED = 'REVIEWED', 'Reviewed'
        OPEN_TO_WORK = 'OPEN_TO_WORK', 'Open to work'
        NOT_INTERESTED = 'NOT_INTERESTED', 'Not interested'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=150, blank=True)
    middle_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    mobile_number = models.CharField(max_length=30, blank=True)
    aadhaar_last_four = models.CharField(max_length=4, blank=True, validators=[RegexValidator(r'^\d{4}$')])
    experience_type = models.CharField(max_length=7, blank=True, choices=[('Fresher', 'Fresher'), ('Lateral', 'Lateral')])
    experience_years = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(80)])
    current_company = models.CharField(max_length=200, blank=True)
    current_role = models.CharField(max_length=200, blank=True)
    preferred_role = models.CharField(max_length=200, blank=True)
    current_city = models.CharField(max_length=150, blank=True)
    preferred_city = models.CharField(max_length=150, blank=True)
    experience_summary = models.TextField(blank=True, max_length=10000)
    skills = models.ManyToManyField('Skill', blank=True, related_name='profiles')
    profile_status = models.CharField(max_length=16, choices=Status.choices, default=Status.CREATED, db_index=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def full_name(self):
        return ' '.join(filter(None, [self.first_name, self.middle_name, self.last_name])) or 'Candidate'

    @property
    def masked_aadhaar(self):
        return f'XXXX XXXX {self.aadhaar_last_four}' if self.aadhaar_last_four else 'Not provided'

    def __str__(self):
        return self.full_name


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Project(models.Model):
    profile = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, max_length=5000)
    from_month = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    from_year = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1900), MaxValueValidator(2100)])
    to_month = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(12)])
    to_year = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1900), MaxValueValidator(2100)])
    role = models.CharField(max_length=200, blank=True)
    activities = models.TextField(blank=True, max_length=5000)

    def clean(self):
        from django.core.exceptions import ValidationError
        if (self.from_month and not self.from_year) or (self.to_month and not self.to_year):
            raise ValidationError('A project month requires its year.')
        if self.from_year and self.to_year and (self.from_year, self.from_month or 1) > (self.to_year, self.to_month or 12):
            raise ValidationError('Project end must not precede its start.')

    def __str__(self):
        return self.title


class Certification(models.Model):
    profile = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=200)
    details = models.TextField(blank=True, max_length=5000)

    def __str__(self):
        return self.name


class Award(models.Model):
    profile = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name='awards')
    name = models.CharField(max_length=200)
    details = models.TextField(blank=True, max_length=5000)

    def __str__(self):
        return self.name


class Score(models.Model):
    profile = models.OneToOneField(JobSeekerProfile, on_delete=models.CASCADE, related_name='score')
    total_score = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(100)])
    components = models.JSONField(default=dict)
    suggestions = models.JSONField(default=list)
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(total_score__lte=100), name='score_max_100')]


class StatusHistory(models.Model):
    profile = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE, related_name='status_history')
    previous_status = models.CharField(max_length=16, blank=True)
    new_status = models.CharField(max_length=16, choices=JobSeekerProfile.Status.choices)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=250, blank=True)

    class Meta:
        ordering = ['-changed_at']
