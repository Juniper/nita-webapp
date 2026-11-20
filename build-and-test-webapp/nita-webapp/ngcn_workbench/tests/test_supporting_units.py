# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for supporting modules: middleware, status updater, and models.

Covers servicestartupmiddleware, statusupdater, model validation logic, and
workbook helpers that sit outside the API layer.
"""

import json
from io import BytesIO
from types import SimpleNamespace

import pytest
from django.utils import timezone
from openpyxl import Workbook as OpenpyxlWorkbook
from ngcn import servicestartupmiddleware, statusupdater, workbook as workbook_module
from ngcn.models import ActionHistory, ActionProperty, CampusType, Workbook, Worksheets
from ngcn.templatetags.json_filters import jsonify
from ngcn.workbook import GridDataManager, escape_ansi


def _xlsx_with_rows(sheet_rows, empty_sheet=False):
    workbook = OpenpyxlWorkbook()
    sheet = workbook.active
    sheet.title = "base"
    for row in sheet_rows:
        sheet.append(row)
    if empty_sheet:
        workbook.create_sheet("env").append(["host"])
    content = BytesIO()
    workbook.save(content)
    content.seek(0)
    content.name = "test.xlsx"
    return content


def test_parse_workbook_accepts_nested_group_vars_path(monkeypatch):
    saved = {}

    class FakeQuerySet:
        def delete(self):
            pass

    class FakeGridDataManager:
        def create_or_update_db(self, _network_id, tables, _filename):
            saved["tables"] = tables

    monkeypatch.setattr(
        workbook_module,
        "Workbook",
        SimpleNamespace(objects=SimpleNamespace(filter=lambda **_kwargs: FakeQuerySet())),
    )
    monkeypatch.setattr(workbook_module, "GridDataManager", FakeGridDataManager)

    result = workbook_module.parse_workbook(
        _xlsx_with_rows(
            [
                ["host", "key", "value"],
                ["group_vars/vqfx_role_candidate1/all.yaml", "asn", 64512],
            ]
        ),
        1,
    )

    assert result == "success"
    assert saved["tables"][0]["base"][0]["host"] == (
        "group_vars/vqfx_role_candidate1/all.yaml"
    )


def test_parse_workbook_rejects_host_path_traversal():
    result = workbook_module.parse_workbook(
        _xlsx_with_rows(
            [
                ["host", "key", "value"],
                ["group_vars/../host_vars/device.yaml", "asn", 64512],
            ]
        ),
        1,
    )

    assert result == "invalid_host"


def test_parse_workbook_skips_header_only_sheet(monkeypatch):
    class FakeQuerySet:
        def delete(self):
            pass

    class FakeGridDataManager:
        def create_or_update_db(self, _network_id, tables, _filename):
            saved["tables"] = tables

    saved = {}
    monkeypatch.setattr(
        workbook_module,
        "Workbook",
        SimpleNamespace(objects=SimpleNamespace(filter=lambda **_kwargs: FakeQuerySet())),
    )
    monkeypatch.setattr(workbook_module, "GridDataManager", FakeGridDataManager)

    result = workbook_module.parse_workbook(
        _xlsx_with_rows(
            [
                ["host", "key", "value"],
                ["group_vars/all.yaml", "asn", 64512],
            ],
            empty_sheet=True,
        ),
        1,
    )

    assert result == "success"
    assert [table["name"] for table in saved["tables"]] == ["base"]


def test_parse_workbook_rejects_workbook_with_no_data_rows():
    result = workbook_module.parse_workbook(
        _xlsx_with_rows([["host", "key", "value"]]), 1
    )

    assert result == "empty_workbook"


@pytest.mark.django_db
def test_jsonify_serializes_queryset_and_plain_object(campus_type):
    queryset_payload = json.loads(jsonify(CampusType.objects.filter(id=campus_type.id)))
    assert queryset_payload[0]["fields"]["name"] == campus_type.name
    assert json.loads(jsonify({"answer": 42})) == {"answer": 42}


def test_status_startup_service_middleware_calls_updater(monkeypatch):
    fake_updater = SimpleNamespace(started=False)

    def fake_start_status_updater_service():
        fake_updater.started = True

    fake_updater.startStatusUpdaterService = fake_start_status_updater_service
    monkeypatch.setattr(
        statusupdater.StatusUpdater, "getInstance", staticmethod(lambda: fake_updater)
    )

    middleware = servicestartupmiddleware.StatusStartupServiceMiddleware(
        get_response=lambda request: None
    )
    middleware.process_request(SimpleNamespace())

    assert fake_updater.started is True


def test_status_updater_get_build_status_uses_server_result(monkeypatch):
    updater = statusupdater.StatusUpdater()

    class FakeJenkins:
        def get_build_info(self, _name, _number):
            return {"result": "SUCCESS"}

    monkeypatch.setattr(statusupdater.StatusUpdater, "SERVER", None)
    monkeypatch.setattr(
        statusupdater, "_make_jenkins_server", lambda acting_user=None: FakeJenkins()
    )

    assert updater.getBuildStatus("job-name", 1) == "SUCCESS"


def test_jenkins_client_asserts_identity_via_header(monkeypatch):
    from ngcn import jenkins_config

    monkeypatch.setattr(jenkins_config, "JENKINS_SERVER_USER", "svc")

    assert jenkins_config.jenkins_identity_headers() == {"X-Forwarded-User": "svc"}
    assert jenkins_config.jenkins_identity_headers("alice", ["admin", "team-3"]) == {
        "X-Forwarded-User": "alice",
        "X-Forwarded-Groups": "admin|team-3",
    }
    service = jenkins_config._make_jenkins_server()
    assert service._session.headers["X-Forwarded-User"] == "svc"
    assert service._session.auth is None
    acting = jenkins_config._make_jenkins_server("alice")
    assert acting._session.headers["X-Forwarded-User"] == "alice"


@pytest.mark.django_db
def test_jenkins_groups_mirror_role_and_teams():
    from django.contrib.auth import get_user_model
    from ngcn import jenkins_config
    from ngcn.models import Team

    user = get_user_model().objects.create_user(
        username="bob", password="x", role="user"
    )
    assert jenkins_config.jenkins_groups_for(user) == ["user"]
    team = Team.objects.create(name="t", created_by=user)
    team.members.add(user)
    assert jenkins_config.jenkins_groups_for(user) == ["user", f"team-{team.id}"]
    assert jenkins_config.jenkins_team_group(team.id) == f"team-{team.id}"


@pytest.mark.django_db
def test_status_updater_updates_running_jobs(action, campus_network, monkeypatch):
    history = ActionHistory.objects.create(
        action_id=action,
        timestamp=timezone.now(),
        status="Running",
        jenkins_job_build_no=9,
        category_id=action.action_category,
        campus_network_id=campus_network,
    )
    updater = statusupdater.StatusUpdater()
    monkeypatch.setattr(updater, "getBuildStatus", lambda *_args: "SUCCESS")

    updater.updateAllRunningJobs()

    history.refresh_from_db()
    assert history.status == "Success"


@pytest.mark.django_db
def test_grid_data_manager_creates_updates_and_reads_sheets(campus_network):
    manager = GridDataManager()
    sheets = [
        {
            "name": "base",
            "columns": [
                {"field": "host", "id": "host", "name": "host"},
            ],
            "base": [{"host": "1.1.1.1"}],
        }
    ]

    manager.create_or_update_db(campus_network.id, sheets, "sample.xlsx")

    workbook = Workbook.objects.get(campus_network_id=campus_network)
    assert workbook.name == "sample.xlsx"
    assert manager.get_workbook_name(campus_network.id) == "sample_type_campus_one.xlsx"
    assert manager.get_sheets_by_campus_network(campus_network.id) == sheets

    updated_sheets = [
        {
            "name": "base",
            "columns": [
                {"field": "host", "id": "host", "name": "host"},
            ],
            "base": [{"host": "2.2.2.2"}],
        }
    ]
    manager.create_or_update_db(campus_network.id, updated_sheets, "sample.xlsx")

    assert (
        Worksheets.objects.filter(workbook_id__campus_network_id=campus_network).count()
        == 1
    )
    assert manager.get_sheets_by_campus_network(campus_network.id) == updated_sheets


@pytest.mark.django_db
def test_model_string_representations(
    action_category, campus_type, campus_network, action
):
    action_property = ActionProperty.objects.create(
        shell_command="echo hello",
        output_path="/tmp/out",
        custom_workspace="/workspace",
    )
    history = ActionHistory.objects.create(
        action_id=action,
        timestamp=timezone.now(),
        status="Running",
        jenkins_job_build_no=1,
        category_id=action_category,
        campus_network_id=campus_network,
    )
    workbook = Workbook.objects.create(
        name="sample.xlsx", campus_network_id=campus_network
    )
    worksheet = Worksheets.objects.create(
        name="sheet1", data="{}", workbook_id=workbook
    )

    assert str(action_category) == action_category.category_name
    assert str(campus_type) == campus_type.name
    assert str(campus_network) == campus_network.name
    assert str(action_property) == "echo hello"
    assert str(action) == action.action_name
    assert str(history) == action.action_name
    assert str(worksheet) == "sheet1"


def test_escape_ansi_strips_escape_sequences():
    assert escape_ansi("\x1b[31mhello\x1b[0m") == "hello"
