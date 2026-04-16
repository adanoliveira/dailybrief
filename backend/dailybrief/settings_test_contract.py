"""Minimal Django settings for processor contract tests.

These settings intentionally avoid the full production app/dependency graph so
contract tests can run fast and deterministically in CI.
"""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "contract-tests-only-secret-key"
DEBUG = False
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.contenttypes",
]

MIDDLEWARE = []
ROOT_URLCONF = "dailybrief.urls_test_contract"
TEMPLATES = []

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

