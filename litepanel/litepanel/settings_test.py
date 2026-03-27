"""
Test settings for Lite Hosting Panel.

Uses in-memory SQLite and fast MD5 password hasher so the test suite
runs quickly without touching the production database or requiring
Argon2 key-stretching overhead.
"""
import os

# Provide dummy secrets so settings.py env-loading does not raise KeyError
os.environ.setdefault('SECRET_KEY', 'test-secret-key-not-for-production')
os.environ.setdefault('FERNET_KEY', 'dGVzdC1mZXJuZXQta2V5LW5vdC1mb3ItcHJvZHVjdGlvbg==')

# Import everything from the base settings, then override below
from litepanel.settings import *  # noqa: F401, F403

# ---------------------------------------------------------------------------
# Fast in-memory database
# ---------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# ---------------------------------------------------------------------------
# Fast password hasher — MD5 (never use in production)
# ---------------------------------------------------------------------------
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# ---------------------------------------------------------------------------
# Disable session cookie security for test client (no HTTPS in tests)
# ---------------------------------------------------------------------------
SESSION_COOKIE_SECURE = False

# ---------------------------------------------------------------------------
# Silence logging during tests
# ---------------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {'class': 'logging.NullHandler'},
    },
    'root': {
        'handlers': ['null'],
    },
}

DEBUG = True
