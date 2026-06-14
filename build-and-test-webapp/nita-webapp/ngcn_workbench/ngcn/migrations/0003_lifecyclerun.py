# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Add the LifecycleRun table for network lifecycle job history."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ngcn", "0002_remove_dynamic_ansible_workspace"),
    ]

    operations = [
        migrations.CreateModel(
            name="LifecycleRun",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("network_create", "Network create"),
                            ("network_delete", "Network delete"),
                            ("network_type_load", "Network type load"),
                        ],
                        max_length=32,
                    ),
                ),
                ("subject", models.CharField(max_length=255)),
                ("job_name", models.CharField(max_length=255)),
                ("build_no", models.IntegerField()),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("status", models.CharField(max_length=64)),
            ],
        ),
    ]
