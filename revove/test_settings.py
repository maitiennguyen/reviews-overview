"""
Lightweight test settings that reuse the main settings but force an
in-memory SQLite database so unit tests can run without needing the
Postgres test database to be created.

Use by running:

  DJANGO_SETTINGS_MODULE=revove.test_settings python manage.py test menus.tests.test_models menus.tests.test_api

"""
from .settings import *  # noqa: F401,F403

# Use in-memory SQLite for tests to avoid creating a Postgres test DB.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
