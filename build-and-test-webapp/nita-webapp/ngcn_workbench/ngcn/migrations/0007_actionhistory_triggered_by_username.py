# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Record who triggered an action.

Adds ``ActionHistory.triggered_by_username``, a durable string snapshot of the
triggering user's username rather than a foreign key, so that attribution
survives renaming or deletion of that user.

Existing rows predate the field and have no recoverable actor, so they take the
empty-string default; the SPA renders that as an em dash.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ngcn", "0006_network_ownership"),
    ]

    operations = [
        migrations.AddField(
            model_name="actionhistory",
            name="triggered_by_username",
            field=models.CharField(
                blank=True,
                default="",
                max_length=150,
                verbose_name="Triggered By",
            ),
        ),
    ]
