from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from profiles.models import JobSeekerProfile
from .models import Application, Job
from .services import apply_for_job

@login_required
def listing(request):
    jobs = Job.objects.filter(active=True).prefetch_related('required_skills')
    query = request.GET.get('q', '').strip()[:100]
    if query:
        jobs = jobs.filter(title__icontains=query)
    return render(request, 'jobs/list.html', {'page_obj': Paginator(jobs, 12).get_page(request.GET.get('page')), 'query': query})

@login_required
def detail(request, pk):
    job = get_object_or_404(Job, pk=pk, active=True)
    applied = Application.objects.filter(job=job, profile__user=request.user).exists()
    return render(request, 'jobs/detail.html', {'job': job, 'applied': applied})

@login_required
@require_POST
def apply(request, pk):
    profile = get_object_or_404(JobSeekerProfile, user=request.user)
    job = get_object_or_404(Job, pk=pk)
    try:
        _, created = apply_for_job(profile, job)
        messages.success(request, 'Application submitted.' if created else 'You have already applied for this job.')
    except ValidationError as error:
        messages.error(request, error.messages[0])
    return redirect('my_applications')

@login_required
def my_applications(request):
    applications = Application.objects.filter(profile__user=request.user).select_related('job')
    return render(request, 'jobs/applications.html', {'applications': applications})
