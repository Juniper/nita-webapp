# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import os

from django.apps import AppConfig

logger = logging.getLogger(__name__)


def bootstrap_admin_from_env():
    """Create an admin user from ``NITA_BOOTSTRAP_ADMIN_*`` env vars.

    Fires only when the database currently has **zero** users, so it is a no-op
    on any established deployment. Returns the created user, or ``None`` when the
    env vars are unset, users already exist, or the database is not yet ready.
    """
    username = os.environ.get("NITA_BOOTSTRAP_ADMIN_USERNAME")
    password = os.environ.get("NITA_BOOTSTRAP_ADMIN_PASSWORD")
    email = os.environ.get("NITA_BOOTSTRAP_ADMIN_EMAIL", "")

    if not username or not password:
        return None

    # Import lazily so this module stays importable before the app registry and
    # database are ready.
    from django.contrib.auth import get_user_model
    from django.db.utils import DatabaseError

    User = get_user_model()
    try:
        if User.objects.exists():
            return None
        user = User(
            username=username,
            email=email,
            role=User.ROLE_ADMIN,
            is_staff=True,
            is_superuser=True,
        )
        user.set_password(password)
        user.save()
    except DatabaseError:
        # Tables not created yet (e.g. running during `migrate`); skip silently.
        return None

    logger.info("Bootstrapped admin user '%s' from environment variables.", username)
    return user


class TreeTutorialConfig(AppConfig):
    name = "ngcn"
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        """Attempt env-driven admin bootstrap on application startup."""
        try:
            bootstrap_admin_from_env()
        except Exception:  # pragma: no cover - never block startup on bootstrap
            logger.exception("Admin bootstrap from environment failed.")
