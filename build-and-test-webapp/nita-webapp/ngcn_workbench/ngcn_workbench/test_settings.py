from .settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Keep tests isolated from host filesystem logging paths.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
}

# Disable service startup middleware to avoid background thread side effects.
MIDDLEWARE = [
    item
    for item in MIDDLEWARE
    if item != "ngcn.servicestartupmiddleware.StatusStartupServiceMiddleware"
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

MIGRATION_MODULES = {
    "ngcn": None,
}
