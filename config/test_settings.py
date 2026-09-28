import os
import secrets
os.environ['DJANGO_SECRET_KEY'] = secrets.token_urlsafe(50)
os.environ['DJANGO_DEBUG'] = 'true'
os.environ['DB_ENGINE'] = 'sqlite'
from .settings import *  # noqa: F403, E402
SECURE_SSL_REDIRECT = False
MAILERS = {'default': {'BACKEND': 'django.core.mail.backends.locmem.EmailBackend'}}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
