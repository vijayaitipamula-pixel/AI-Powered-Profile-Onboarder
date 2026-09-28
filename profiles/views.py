from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView, PasswordResetConfirmView
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import AwardFormSet, CertificationFormSet, ProfileForm, ProjectFormSet
from .models import JobSeekerProfile, Skill
from .services import change_status, refresh_profile


@login_required
def dashboard(request):
    profile = JobSeekerProfile.objects.filter(user=request.user).select_related('user', 'score').first()
    return render(request, 'profiles/dashboard.html', {'profile': profile})


@login_required
def edit_profile(request):
    profile = get_object_or_404(JobSeekerProfile, user=request.user)
    data = request.POST if request.method == 'POST' else None
    form = ProfileForm(data, instance=profile)
    formsets = [ProjectFormSet(data, instance=profile, prefix='projects'),
        CertificationFormSet(data, instance=profile, prefix='certifications'),
        AwardFormSet(data, instance=profile, prefix='awards')]
    valid = [form.is_valid(), *[item.is_valid() for item in formsets]] if data is not None else []
    if data is not None and all(valid):
        with transaction.atomic():
            JobSeekerProfile.objects.select_for_update().get(pk=profile.pk)
            profile = form.save(commit=False)
            profile.confirmed_at = timezone.now()
            profile.save()
            profile.skills.set([Skill.objects.get_or_create(name=name)[0] for name in form.cleaned_data['skill_names']])
            for formset in formsets:
                formset.save()
            refresh_profile(profile, request.user)
        messages.success(request, 'Profile updated and score recalculated.')
        return redirect('dashboard')
    return render(request, 'profiles/edit.html', {'form': form, 'formsets': formsets})


@login_required
@require_POST
def not_interested(request):
    profile = get_object_or_404(JobSeekerProfile, user=request.user)
    change_status(profile, JobSeekerProfile.Status.NOT_INTERESTED, request.user)
    messages.success(request, 'Your preference has been saved. Contact a reviewer when you want to reopen your profile.')
    return redirect('dashboard')


class ChangePasswordView(PasswordChangeView):
    template_name = 'registration/form.html'
    success_url = reverse_lazy('dashboard')
    extra_context = {'heading': 'Change your password'}

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            type(self.request.user).objects.filter(pk=self.request.user.pk).update(
                must_change_password=False, temporary_password_expires_at=None)
        return response


class ResetPasswordConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            type(self.user).objects.filter(pk=self.user.pk).update(
                must_change_password=False, temporary_password_expires_at=None)
        return response
