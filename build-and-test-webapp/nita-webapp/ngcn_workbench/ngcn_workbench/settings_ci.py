"""CI settings for running automated checks and tests in GitHub Actions."""

from .settings import *  # noqa: F401,F403


# Use SQLite in CI to keep tests self-contained and avoid external DB setup.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Write logs to the workflow filesystem instead of /var/log.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        }
    },
    "loggers": {
        "ngcn": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        }
    },
}
