"""Settings for tests."""

SECRET_KEY = 'Qapla\'!'

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'djmoney',
    'django_pain.apps.DjangoPainConfig',
]

DATABASES = {
        'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}
}
