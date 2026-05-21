# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "ys89t=b+62xu+9xzr3p#ha_i@*vvbo50_4cpgg1n6il8&6xh@$"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "https://localhost").split(",")
    if origin.strip()
]

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    #   ngcn
    "ngcn",
    #   Frameworks
    "djangoformsetjs",
    "django_tables2",
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "ngcn_workbench.csrf.LabCsrfMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "ngcn.servicestartupmiddleware.StatusStartupServiceMiddleware",
]

ROOT_URLCONF = "ngcn_workbench.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": False,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
            ],
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
                #                'django.template.loaders.eggs.Loader'
            ],
        },
    },
]

WSGI_APPLICATION = "ngcn_workbench.wsgi.application"

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "Sites",
        "USER": "root",
        "PASSWORD": "root",
        "HOST": "db",
        "PORT": 3306,
    }
}

# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# STATICFILES_DIRS = [
# ]


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"

STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "django.contrib.staticfiles.finders.FileSystemFinder",
]

# WhiteNoise serves the compiled React SPA assets (JS/CSS) at their root-relative
# paths (e.g. /assets/index-xxx.js) without going through collectstatic.
WHITENOISE_ROOT = os.environ.get(
    "FRONTEND_DIST",
    os.path.join(BASE_DIR, "../../../frontend/dist"),
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "NITA Webapp API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"


LOCALE_PATHS = [os.path.join(BASE_DIR, "ngcn/locale"), os.path.join(BASE_DIR, "locale")]


LOGGING = {
    "version": 1,
    # False so Django's own loggers (django.request, django.security) still emit
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[ %(asctime)s %(levelname)s %(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
        },
        "console": {
            "format": "%(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "default": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/nita-webapp/server.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "formatter": "standard",
        },
        # Console handler — respects DJANGO_LOG_LEVEL (default WARNING).
        # Set DJANGO_LOG_LEVEL=DEBUG in the k8s deployment for verbose output.
        "console": {
            "level": os.getenv("DJANGO_LOG_LEVEL", "WARNING"),
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "loggers": {
        # Application logger: file + console
        "ngcn": {"handlers": ["default", "console"], "level": "DEBUG", "propagate": False},
        # Django core: console only (errors + warnings surface in kubectl logs)
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        # HTTP 500/400 errors — always log at ERROR so they appear in kubectl logs
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "django.security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
