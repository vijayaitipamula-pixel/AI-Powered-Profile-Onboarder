from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from django.utils import timezone

from .models import Award, Certification, JobSeekerProfile, Project


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Email (or staff username)', max_length=254)

    def clean_username(self):
        return self.cleaned_data['username'].strip().lower()

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if user.must_change_password and (not user.temporary_password_expires_at or user.temporary_password_expires_at <= timezone.now()):
            raise ValidationError('Your temporary password has expired. Use Forgot password to set a new one.', code='expired')


class ProfileForm(forms.ModelForm):
    skill_names = forms.CharField(label='Skills (comma separated)', required=False, max_length=10000)
    confirm_details = forms.BooleanField(label='I have reviewed these details and confirm they are accurate.')

    class Meta:
        model = JobSeekerProfile
        fields = ['first_name', 'middle_name', 'last_name', 'date_of_birth', 'mobile_number',
            'aadhaar_last_four', 'experience_type', 'experience_years', 'current_company',
            'current_role', 'preferred_role', 'current_city', 'preferred_city', 'experience_summary']
        widgets = {'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
                   'experience_summary': forms.Textarea(attrs={'rows': 4})}
        labels = {'aadhaar_last_four': 'Aadhaar last four digits (optional)'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['skill_names'].initial = ', '.join(self.instance.skills.values_list('name', flat=True))

    def clean_date_of_birth(self):
        value = self.cleaned_data.get('date_of_birth')
        if value and (value > timezone.localdate() or value.year < 1900):
            raise ValidationError('Enter a valid birth date.')
        return value

    def clean_skill_names(self):
        names = list(dict.fromkeys(x.strip().casefold() for x in self.cleaned_data['skill_names'].split(',') if x.strip()))
        if len(names) > 100 or any(len(x) > 100 for x in names):
            raise ValidationError('Use up to 100 skills, each no longer than 100 characters.')
        return names

    def clean(self):
        data = super().clean()
        if data.get('experience_type') == 'Fresher' and data.get('experience_years') not in (None, 0):
            self.add_error('experience_years', 'A fresher cannot have non-zero professional experience.')
        return data


ProjectFormSet = inlineformset_factory(JobSeekerProfile, Project,
    fields=['title', 'description', 'from_month', 'from_year', 'to_month', 'to_year', 'role', 'activities'],
    extra=1, can_delete=True, max_num=30, validate_max=True, absolute_max=60)
CertificationFormSet = inlineformset_factory(JobSeekerProfile, Certification,
    fields=['name', 'details'], extra=1, can_delete=True, max_num=50, validate_max=True, absolute_max=100)
AwardFormSet = inlineformset_factory(JobSeekerProfile, Award,
    fields=['name', 'details'], extra=1, can_delete=True, max_num=50, validate_max=True, absolute_max=100)
