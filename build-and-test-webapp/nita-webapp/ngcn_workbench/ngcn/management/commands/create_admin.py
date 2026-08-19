# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Django management command: create (or update) the initial admin user.

Usage
-----
    manage.py create_admin --username admin --email admin@example.com --password secret

Behaviour
---------
* Creates a user with ``role=admin``, ``is_staff=True`` and ``is_superuser=True``.
* Idempotent: if a user with the given username already exists it is promoted to
  admin and (optionally) has its password reset, rather than raising an error.

This supersedes ``createsuperuser`` for NITA deployments so that the initial
account carries the application ``role=admin`` used for API access control.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Create or promote the initial admin user (role=admin, is_staff=True)."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True, help="Admin username")
        parser.add_argument("--email", default="", help="Admin email address")
        parser.add_argument("--password", required=True, help="Admin password")

    @transaction.atomic
    def handle(self, *args, **options):
        username = options["username"].strip()
        email = options["email"].strip()
        password = options["password"]

        if not username or not password:
            raise CommandError("Both --username and --password are required.")

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )
        user.role = User.ROLE_ADMIN
        user.is_staff = True
        user.is_superuser = True
        if email:
            user.email = email
        user.set_password(password)
        user.save()

        verb = "Created" if created else "Updated"
        self.stdout.write(
            self.style.SUCCESS(f"{verb} admin user '{username}' (role=admin).")
        )
