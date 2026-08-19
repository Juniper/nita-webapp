# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Add ownership/curation fields.

* ``CampusNetwork.owner`` (PROTECT) and ``CampusNetwork.team`` (SET_NULL)
* ``CampusType.created_by`` (SET_NULL)

A data migration assigns any pre-existing (orphaned) networks to the first
admin user so they remain visible rather than becoming invisible orphans.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def assign_orphan_networks_to_admin(apps, schema_editor):
    """Assign networks with no owner to the first admin user, if one exists."""
    User = apps.get_model(settings.AUTH_USER_MODEL)
    CampusNetwork = apps.get_model("ngcn", "CampusNetwork")

    admin = User.objects.filter(role="admin").order_by("id").first()
    if admin is None:
        admin = User.objects.order_by("id").first()
    if admin is None:
        return
    CampusNetwork.objects.filter(owner__isnull=True).update(owner=admin)


def noop_reverse(apps, schema_editor):
    """No-op reverse; ownership assignment is not undone."""
    return


class Migration(migrations.Migration):

    dependencies = [
        ("ngcn", "0005_user_team"),
    ]

    operations = [
        migrations.AddField(
            model_name="campustype",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_types",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Created By",
            ),
        ),
        migrations.AddField(
            model_name="campusnetwork",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="owned_networks",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Owner",
            ),
        ),
        migrations.AddField(
            model_name="campusnetwork",
            name="team",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="networks",
                to="ngcn.team",
                verbose_name="Team",
            ),
        ),
        migrations.RunPython(assign_orphan_networks_to_admin, noop_reverse),
    ]
