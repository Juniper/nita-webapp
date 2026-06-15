# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Drop the CampusNetwork.dynamic_ansible_workspace column.

The dynamic Ansible workspace is now the permanent, only behaviour: the
build directory is always set to ``/var/tmp/build/<type>-<network>`` at
trigger time, so the per-network flag is no longer needed.

This migration is guarded so it is safe on a *fresh* database where the
``ngcn_campusnetwork`` table does not exist yet (the table is created later
by ``0004_create_base_tables``). It only issues the ``ALTER TABLE`` when the
table and the legacy column are actually present, which is the case on
existing installations created by the old syncdb code path.
"""

from django.db import migrations

TABLE = "ngcn_campusnetwork"
COLUMN = "dynamic_ansible_workspace"


def _table_exists(connection):
    return TABLE in connection.introspection.table_names()


def _column_exists(connection):
    with connection.cursor() as cursor:
        columns = connection.introspection.get_table_description(cursor, TABLE)
    return COLUMN in [column.name for column in columns]


def drop_column(apps, schema_editor):
    connection = schema_editor.connection
    if not _table_exists(connection):
        return
    if _column_exists(connection):
        with connection.cursor() as cursor:
            cursor.execute(
                "ALTER TABLE ngcn_campusnetwork DROP COLUMN dynamic_ansible_workspace;"
            )


def add_column(apps, schema_editor):
    connection = schema_editor.connection
    if not _table_exists(connection):
        return
    if not _column_exists(connection):
        with connection.cursor() as cursor:
            cursor.execute(
                "ALTER TABLE ngcn_campusnetwork "
                "ADD COLUMN dynamic_ansible_workspace bool NOT NULL DEFAULT 1;"
            )


class Migration(migrations.Migration):

    dependencies = [
        ("ngcn", "0001_remove_roles_resources"),
    ]

    operations = [
        migrations.RunPython(drop_column, reverse_code=add_column),
    ]
