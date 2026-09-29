import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

def env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in {'true', '1', 'yes'}

DEBUG = env_bool('DJANGO_DEBUG')
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    raise ImproperlyConfigured('Set DJANGO_SECRET_KEY in your environment or .env.')
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
CSRF_TRUSTED_ORIGINS = list(filter(None, os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',')))
INSTALLED_APPS = ['django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'profiles', 'resumes', 'jobs']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware',
    'profiles.middleware.TemporaryPasswordMiddleware', 'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True,
    'OPTIONS': {'context_processors': ['django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
if os.getenv('DB_ENGINE', 'sqlite') == 'mysql':
    DATABASES['default'] = {'ENGINE': 'django.db.backends.mysql', 'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'], 'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.getenv('DB_HOST', 'localhost'), 'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {'charset': 'utf8mb4', 'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"}}
AUTH_USER_MODEL = 'profiles.User'
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Serve resumes only through the authorized download view, never a public media URL.
MEDIA_ROOT = BASE_DIR / 'private_media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 7 * 1024 * 1024
RESUME_MAX_BYTES = 5 * 1024 * 1024
RESUME_MAX_PAGES = 30
RESUME_MAX_TEXT_CHARS = 60000
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')
OPENAI_TIMEOUT = float(os.getenv('OPENAI_TIMEOUT', '45'))
SITE_URL = os.getenv('SITE_URL', 'http://127.0.0.1:8000').rstrip('/')
TEMP_PASSWORD_HOURS = 24
PASSWORD_RESET_TIMEOUT = 86400
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', '') or 'onboarding@localhost'
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = env_bool('EMAIL_USE_TLS', True)
EMAIL_TIMEOUT = 15
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', not DEBUG)
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
# Do not send request tracebacks or SDK payloads to logs/email.
LOGGING = {'version': 1, 'disable_existing_loggers': False,
    'handlers': {'null': {'class': 'logging.NullHandler'}},
    'loggers': {name: {'handlers': ['null'], 'propagate': False} for name in
        ['django.request', 'openai', 'httpx', 'httpx2', 'httpcore', 'httpcore2']}}
