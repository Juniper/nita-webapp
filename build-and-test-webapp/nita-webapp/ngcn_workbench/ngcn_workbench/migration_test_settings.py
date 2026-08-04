# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Settings overlay for migration-integrity tests.

Unlike :mod:`ngcn_workbench.test_settings` — which disables the ``ngcn`` app's
migrations (``MIGRATION_MODULES = {"ngcn": None}``) so the schema is built
directly from the models — this overlay keeps the *real* migration graph enabled
and runs it against SQLite. That lets tests exercise the actual migration
ordering (e.g. the custom user-model swappable-dependency ordering), which the
model-based table creation used by the main suite cannot catch.
"""

from .settings import *  # noqa: F401,F403

# Quiet file-based logging that requires /var/log/nita-webapp to exist.
LOGGING = {"version": 1, "disable_existing_loggers": False}

# SQLite so the migration graph can be applied without a MySQL server.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
