# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Drop the CampusNetwork.dynamic_ansible_workspace column.

The dynamic Ansible workspace is now the permanent, only behaviour: the
build directory is always set to ``/var/tmp/build/<type>-<network>`` at
trigger time, so the per-network flag is no longer needed.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ngcn", "0001_remove_roles_resources"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE ngcn_campusnetwork "
            "DROP COLUMN dynamic_ansible_workspace;",
            reverse_sql="ALTER TABLE ngcn_campusnetwork "
            "ADD COLUMN dynamic_ansible_workspace bool NOT NULL DEFAULT 1;",
        ),
    ]
