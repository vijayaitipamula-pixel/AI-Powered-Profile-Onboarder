from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import UploadForm
from .models import Resume
from .services import may_manage_uploads, process_resume, send_onboarding, upload_resume


def visible_resumes(user):
    if user.is_staff and user.has_perm('resumes.view_resume'):
        return Resume.objects.all()
    return Resume.objects.filter(Q(profile__user=user) | Q(uploaded_by=user))


@login_required
def upload(request):
    if not may_manage_uploads(request.user) and not hasattr(request.user, 'profile'):
        raise PermissionDenied
    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        resume = upload_resume(form.cleaned_data['resume'], request.user)
        return redirect('resume_detail', pk=resume.pk)
    return render(request, 'resumes/upload.html', {'form': form})


@login_required
def detail(request, pk):
    resume = get_object_or_404(visible_resumes(request.user), pk=pk)
    return render(request, 'resumes/detail.html', {'resume': resume, 'can_manage': may_manage_uploads(request.user)})


@login_required
def download(request, pk):
    resume = get_object_or_404(visible_resumes(request.user), pk=pk)
    try:
        response = FileResponse(resume.uploaded_file.open('rb'), as_attachment=True,
            filename='resume.pdf', content_type='application/pdf')
    except FileNotFoundError:
        raise Http404('Resume file is unavailable.') from None
    response['Cache-Control'] = 'private, no-store'
    return response


@login_required
@require_POST
def retry(request, pk):
    resume = get_object_or_404(visible_resumes(request.user), pk=pk)
    try:
        process_resume(resume, request.user)
    except ValidationError as error:
        messages.error(request, error.messages[0])
    return redirect('resume_detail', pk=pk)


@login_required
@require_POST
def resend_email(request, pk):
    if not may_manage_uploads(request.user):
        raise PermissionDenied
    resume = get_object_or_404(Resume, pk=pk, parsing_status=Resume.Status.PARSED)
    send_onboarding(resume)
    messages.info(request, 'Email delivery status has been updated.')
    return redirect('resume_detail', pk=pk)
