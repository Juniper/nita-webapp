# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Django management command: seed the evpn_vxlan_erb_dc project fixture.

Usage
-----
    manage.py seed_evpn_fixture <path/to/project.yaml>

What it does
------------
1. Ensures that the ActionCategory rows ``NOOB``, ``BUILD``, and ``TEST``
   exist (creates them if absent — these must be uppercase to match the
   project.yaml ``category`` field without case-folding).
2. Reads the supplied ``project.yaml`` and creates a ``CampusType`` row
   together with one ``Action`` + ``ActionProperty`` per action entry.
3. Is idempotent: if a ``CampusType`` with the same name already exists the
   command exits cleanly without error.

This command is used during CI to pre-seed the live database so that the
end-to-end integration tests can exercise the network/workbook API without
needing a running Jenkins instance.
"""

import pathlib

import yaml
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ngcn.models import Action, ActionCategory, ActionProperty, CampusType


class Command(BaseCommand):
    help = "Seed the database with an evpn_vxlan_erb_dc CampusType from project.yaml"

    def add_arguments(self, parser):
        parser.add_argument(
            "project_yaml",
            type=str,
            help="Absolute or relative path to the project.yaml file to import",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        yaml_path = pathlib.Path(options["project_yaml"])
        if not yaml_path.exists():
            raise CommandError(f"File not found: {yaml_path}")

        data = yaml.safe_load(yaml_path.read_text())

        campus_type_name = data["name"].strip()

        # ── Idempotency guard ─────────────────────────────────────────────────
        if CampusType.objects.filter(name=campus_type_name).exists():
            self.stdout.write(
                self.style.WARNING(
                    f"CampusType '{campus_type_name}' already exists — skipping."
                )
            )
            return

        # ── Ensure action categories exist (uppercase) ────────────────────────
        for cat_name in ("NOOB", "BUILD", "TEST"):
            ActionCategory.objects.get_or_create(category_name=cat_name)

        # ── Create CampusType ─────────────────────────────────────────────────
        campus_type = CampusType.objects.create(
            name=campus_type_name,
            description=data.get("description", "").strip(),
            app_zip_name=f"{campus_type_name}.zip",
        )

        # ── Create Actions ────────────────────────────────────────────────────
        action_count = 0
        for action_data in data["action"]:
            category_name = action_data["category"].strip().upper()
            try:
                action_category = ActionCategory.objects.get(
                    category_name=category_name
                )
            except ActionCategory.DoesNotExist:
                raise CommandError(
                    f"ActionCategory '{category_name}' not found after seeding — "
                    "this is a bug in seed_evpn_fixture."
                )

            output_path: str | None = None
            if category_name == "TEST":
                output_path = (
                    action_data["configuration"].get("output_path", "") or ""
                ).strip() or None

            custom_workspace = (
                action_data["configuration"].get("custom_workspace", "") or ""
            )

            prop = ActionProperty.objects.create(
                shell_command=action_data["configuration"]["shell_command"].strip(),
                output_path=output_path,
                custom_workspace=custom_workspace,
            )

            Action.objects.create(
                action_name=action_data["name"].strip(),
                jenkins_url=action_data["jenkins_url"].strip(),
                action_category=action_category,
                campus_type_id=campus_type,
                action_property=prop,
            )
            action_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded CampusType '{campus_type_name}' with {action_count} action(s)."
            )
        )
