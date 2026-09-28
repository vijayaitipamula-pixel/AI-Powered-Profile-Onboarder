from django.contrib import admin
from django.contrib.auth import views as auth
from django.urls import path
from profiles import views as profiles
from profiles.forms import LoginForm
from resumes import views as resumes
from jobs import views as jobs

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', profiles.dashboard, name='dashboard'),
    path('accounts/login/', auth.LoginView.as_view(template_name='registration/login.html', authentication_form=LoginForm), name='login'),
    path('accounts/logout/', auth.LogoutView.as_view(), name='logout'),
    path('accounts/password/change/', profiles.ChangePasswordView.as_view(), name='password_change'),
    path('accounts/password/reset/', auth.PasswordResetView.as_view(template_name='registration/form.html',
        extra_context={'heading': 'Reset your password'}, email_template_name='registration/password_reset_email.txt',
        subject_template_name='registration/password_reset_subject.txt'), name='password_reset'),
    path('accounts/password/reset/sent/', auth.PasswordResetDoneView.as_view(template_name='registration/message.html',
        extra_context={'heading': 'Check your email', 'message': 'If an active account matches that email, a password reset link has been sent.'}), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', profiles.ResetPasswordConfirmView.as_view(), name='password_reset_confirm'),
    path('accounts/password/reset/complete/', auth.PasswordResetCompleteView.as_view(template_name='registration/message.html',
        extra_context={'heading': 'Password updated', 'message': 'You can now sign in with your new password.'}), name='password_reset_complete'),
    path('profile/edit/', profiles.edit_profile, name='edit_profile'),
    path('profile/not-interested/', profiles.not_interested, name='not_interested'),
    path('resumes/upload/', resumes.upload, name='resume_upload'),
    path('resumes/<int:pk>/', resumes.detail, name='resume_detail'),
    path('resumes/<int:pk>/download/', resumes.download, name='resume_download'),
    path('resumes/<int:pk>/retry/', resumes.retry, name='resume_retry'),
    path('resumes/<int:pk>/email/', resumes.resend_email, name='resume_email'),
    path('jobs/', jobs.listing, name='job_list'),
    path('jobs/<int:pk>/', jobs.detail, name='job_detail'),
    path('jobs/<int:pk>/apply/', jobs.apply, name='job_apply'),
    path('applications/', jobs.my_applications, name='my_applications'),
]
