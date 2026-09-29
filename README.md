# AI-Powered Profile Onboarder

A Django application that turns a PDF resume into a candidate profile, lets the
candidate verify extracted information, calculates a profile-completeness score,
and unlocks job applications when the profile is ready.

## Local setup

1. Create and activate a Python virtual environment.
2. Run `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and set `DJANGO_SECRET_KEY`.
4. Run `python manage.py migrate`.
5. Run `python manage.py createsuperuser`.
6. Run `python manage.py runserver` and open http://127.0.0.1:8000/.

Set `OPENAI_API_KEY` to process real resumes. The default email backend prints
onboarding mail to the terminal. To use SMTP, set `EMAIL_BACKEND` to
`django.core.mail.backends.smtp.EmailBackend` and fill in the email variables in
`.env`.

Staff members need the Resume add permission and Job Seeker Profile change
permission to upload a resume for a new candidate. The candidate receives a
temporary password, changes it after login, reviews the extracted profile, and
confirms it. A confirmed profile with all required fields becomes Open to Work.

## Validation

Run `python manage.py test --settings=config.test_settings` and
`python manage.py check` before deployment.
