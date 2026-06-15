# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Drop the Role, Resource, and their CampusType M2M join tables.

These tables were never populated — the code that would parse roles and
resources from project.yaml was commented out before the feature shipped.
The Role and Resource models are removed in this migration.

Use ``python manage.py migrate ngcn --fake-initial`` on an existing
installation where these tables were already created via syncdb, then
apply this migration to drop the orphaned tables.
"""

from django.db import migrations


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.RunSQL(
            sql=[
                "DROP TABLE IF EXISTS ngcn_campustype_roles;",
                "DROP TABLE IF EXISTS ngcn_campustype_resources;",
                "DROP TABLE IF EXISTS ngcn_role;",
                "DROP TABLE IF EXISTS ngcn_resource;",
            ],
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
