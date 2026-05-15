"""Unit tests for supporting modules: middleware, status updater, models, and tables.

Covers servicestartupmiddleware, statusupdater, model validation logic, and
django-tables2 table classes that sit outside the main views and API layers.
"""
import json
from types import SimpleNamespace

import pytest
from django.utils import timezone
from ngcn import servicestartupmiddleware, statusupdater
from ngcn.models import ActionHistory, ActionProperty, CampusType, Workbook, Worksheets
from ngcn.tables import CampusNetworkActionListTable
from ngcn.templatetags.json_filters import jsonify
from ngcn.views import GridDataManager, escape_ansi


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
    updater.SERVER = SimpleNamespace(
        get_build_info=lambda _name, _number: {"result": "SUCCESS"}
    )

    assert updater.getBuildStatus("job-name", 1) == "SUCCESS"


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


@pytest.mark.django_db
def test_campus_network_action_list_table_renders_suffixed_url(action):
    table = CampusNetworkActionListTable.__new__(CampusNetworkActionListTable)
    table.network_name = "campus_one"

    assert table.render_jenkins_url(action.jenkins_url, action) == "job-test-campus_one"


def test_escape_ansi_strips_escape_sequences():
    assert escape_ansi("\x1b[31mhello\x1b[0m") == "hello"
