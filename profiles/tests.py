from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from jobs.models import Application, Job
from jobs.services import apply_for_job
from resumes.models import Resume
from resumes.schema import ParsedResume
from resumes.services import save_candidate

from .models import JobSeekerProfile, Score, StatusHistory, User
from .services import calculate_score, refresh_profile


def parsed_resume():
    return ParsedResume.model_validate({
        'first_name': 'Asha', 'middle_name': '', 'last_name': 'Rao',
        'date_of_birth': None, 'mobile_number': '9876543210',
        'email': 'asha@example.com', 'aadhaar_number': None,
        'experience_type': 'Lateral', 'experience_years': 4.0,
        'current_company': 'Example Ltd', 'current_role': 'Python Developer',
        'preferred_role': 'Senior Python Developer', 'current_city': 'Bengaluru',
        'preferred_city': 'Bengaluru', 'skills': ['python', 'django', 'sql'],
        'projects': [{
            'title': 'Hiring Portal', 'description': 'Built candidate onboarding.',
            'from_month': 1, 'from_year': 2024, 'to_month': 6, 'to_year': 2024,
            'role': 'Developer', 'activities': 'Designed and implemented APIs.',
        }],
        'certifications': [{'name': 'Python', 'details': 'Professional certificate'}],
        'awards': [], 'experience_summary': 'Four years building web applications.',
    })


class CandidateWorkflowTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_superuser(
            username='admin@example.com', email='admin@example.com', password='Admin-password-123')
        self.resume = Resume.objects.create(
            uploaded_by=self.staff,
            uploaded_file=SimpleUploadedFile('resume.pdf', b'%PDF-1.4 test'),
            original_filename='resume.pdf',
        )

    def test_resume_to_application_workflow(self):
        with self.captureOnCommitCallbacks(execute=True):
            profile = save_candidate(self.resume, parsed_resume(), self.staff)

        profile.refresh_from_db()
        self.resume.refresh_from_db()
        self.assertEqual(profile.profile_status, JobSeekerProfile.Status.CREATED)
        self.assertTrue(profile.user.check_password(profile.user.password) is False)
        self.assertTrue(profile.user.must_change_password)
        self.assertEqual(self.resume.parsing_status, Resume.Status.PARSED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['asha@example.com'])

        profile.confirmed_at = timezone.now()
        profile.save(update_fields=['confirmed_at'])
        refresh_profile(profile, profile.user)
        profile.refresh_from_db()

        self.assertEqual(profile.profile_status, JobSeekerProfile.Status.OPEN_TO_WORK)
        self.assertGreaterEqual(profile.score.total_score, 80)
        self.assertTrue(StatusHistory.objects.filter(
            profile=profile, new_status=JobSeekerProfile.Status.OPEN_TO_WORK).exists())

        job = Job.objects.create(
            title='Senior Python Developer', description='Build web applications.',
            location='Bengaluru')
        application, created = apply_for_job(profile, job)
        self.assertTrue(created)
        self.assertEqual(application.status, Application.Status.APPLIED)

        same_application, created = apply_for_job(profile, job)
        self.assertFalse(created)
        self.assertEqual(same_application, application)

    def test_project_score_rewards_documented_project_details(self):
        user = User.objects.create_user('candidate@example.com', 'candidate@example.com', 'A-password-123')
        profile = JobSeekerProfile.objects.create(user=user)
        score = calculate_score(profile)
        self.assertEqual(score.components['projects'], 0)

        profile.projects.create(
            title='Project', description='Description', role='Developer', activities='Implementation')
        score = calculate_score(profile)
        self.assertEqual(score.components['projects'], 8)
        self.assertIsInstance(score, Score)
