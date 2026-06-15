# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Create the ngcn base tables on a fresh database.

Earlier installations created these tables through the legacy syncdb code
path, so the original migration history only ever contained *transition*
migrations (drop orphaned tables, drop a column, add LifecycleRun) and never
the ``CreateModel`` operations for the core models. On a brand new database
that meant ``migrate`` produced no ngcn tables at all and every API call
returned HTTP 500.

This migration fixes that using ``SeparateDatabaseAndState``:

* ``state_operations`` register the eight core models in Django's migration
  state, so ``makemigrations`` stays a no-op afterwards. This keeps pod
  restarts safe: the startup ``makemigrations ngcn`` no longer generates a
  fresh, timestamp-named migration that would try to re-create existing
  tables.
* ``database_operations`` create the tables only when they are absent. On an
  existing installation (tables already created by syncdb) nothing is touched
  and the migration simply records state.
"""

from django.apps import apps as global_apps
from django.db import migrations, models
import django.db.models.deletion


# Core models in foreign-key dependency order (referenced tables first).
MODEL_ORDER = [
    "ActionCategory",
    "CampusType",
    "ActionProperty",
    "Action",
    "CampusNetwork",
    "ActionHistory",
    "Workbook",
    "Worksheets",
]

# Any one of the core tables existing means this is an established install
# (created by syncdb or a previous run), so the schema must not be recreated.
SENTINEL_TABLE = "ngcn_campustype"


def create_base_tables(apps, schema_editor):
    # ``apps`` here is the historical state *before* this migration's
    # ``state_operations`` are applied, so the base models are not yet present
    # in it. Use the real, current models from the global registry instead;
    # the ``state_operations`` are written to match them exactly.
    connection = schema_editor.connection
    if SENTINEL_TABLE in connection.introspection.table_names():
        return
    for model_name in MODEL_ORDER:
        schema_editor.create_model(global_apps.get_model("ngcn", model_name))


def drop_base_tables(apps, schema_editor):
    connection = schema_editor.connection
    if SENTINEL_TABLE not in connection.introspection.table_names():
        return
    for model_name in reversed(MODEL_ORDER):
        schema_editor.delete_model(global_apps.get_model("ngcn", model_name))


class Migration(migrations.Migration):

    dependencies = [
        ("ngcn", "0003_lifecyclerun"),
    ]

    state_operations = [
        migrations.CreateModel(
            name="Action",
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
                    "action_name",
                    models.CharField(max_length=255, verbose_name="Action Name"),
                ),
                (
                    "jenkins_url",
                    models.CharField(max_length=255, verbose_name="Jenkins Action Url"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ActionCategory",
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
                    "category_name",
                    models.CharField(
                        max_length=255, unique=True, verbose_name="Category Name"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ActionProperty",
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
                    "shell_command",
                    models.TextField(max_length=255, verbose_name="Shell Command"),
                ),
                (
                    "output_path",
                    models.CharField(
                        max_length=255, null=True, verbose_name="Output Path"
                    ),
                ),
                (
                    "custom_workspace",
                    models.CharField(
                        max_length=255, null=True, verbose_name="Output Path"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CampusNetwork",
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
                    "name",
                    models.CharField(
                        max_length=255, unique=True, verbose_name="network_heading Name"
                    ),
                ),
                ("status", models.CharField(max_length=255, verbose_name="Status")),
                (
                    "description",
                    models.CharField(max_length=255, verbose_name="Description"),
                ),
                ("host_file", models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name="CampusType",
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
                    "name",
                    models.CharField(
                        max_length=255,
                        unique=True,
                        verbose_name="network_type_heading Name",
                    ),
                ),
                (
                    "description",
                    models.CharField(max_length=255, verbose_name="Description"),
                ),
                ("app_zip_name", models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="Workbook",
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
                ("name", models.CharField(max_length=255)),
                (
                    "campus_network_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="ngcn.campusnetwork",
                        verbose_name="network_heading",
                    ),
                ),
            ],
            options={
                "unique_together": {("campus_network_id", "name")},
            },
        ),
        migrations.AddField(
            model_name="campusnetwork",
            name="campus_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="ngcn.campustype",
                verbose_name="network_type_heading",
            ),
        ),
        migrations.CreateModel(
            name="ActionHistory",
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
                ("timestamp", models.DateTimeField(verbose_name="Timestamp")),
                ("status", models.CharField(max_length=255, verbose_name="Status")),
                (
                    "jenkins_job_build_no",
                    models.IntegerField(verbose_name="Jenkins Job Id"),
                ),
                (
                    "action_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="ngcn.action",
                        verbose_name="Action Id",
                    ),
                ),
                (
                    "campus_network_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="ngcn.campusnetwork",
                        verbose_name="Campus Network Id",
                    ),
                ),
                (
                    "category_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="ngcn.actioncategory",
                        verbose_name="Category Id",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="action",
            name="action_category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="ngcn.actioncategory",
                verbose_name="Action Category",
            ),
        ),
        migrations.AddField(
            model_name="action",
            name="action_property",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                to="ngcn.actionproperty",
                verbose_name="Action Property",
            ),
        ),
        migrations.AddField(
            model_name="action",
            name="campus_type_id",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="ngcn.campustype",
                verbose_name="Campus Type Id",
            ),
        ),
        migrations.CreateModel(
            name="Worksheets",
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
                ("name", models.CharField(max_length=255)),
                ("data", models.TextField()),
                (
                    "workbook_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="ngcn.workbook"
                    ),
                ),
            ],
            options={
                "unique_together": {("workbook_id", "name")},
            },
        ),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=state_operations,
            database_operations=[
                migrations.RunPython(create_base_tables, drop_base_tables),
            ],
        ),
    ]
