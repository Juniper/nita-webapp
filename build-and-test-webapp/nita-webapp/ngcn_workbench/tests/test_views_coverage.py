import json

import jenkins
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from openpyxl import Workbook as OpenPyxlWorkbook

from ngcn.models import ActionHistory
from ngcn.models import CampusNetwork
from ngcn.models import Workbook
from ngcn import views


class FakeJob:
    def __init__(self):
        self.calls = []

    def invoke(self, **kwargs):
        self.calls.append(kwargs)


class FakeJenkinsClient:
    def __init__(self):
        self.job = FakeJob()
        self.job_names = []

    def get_job(self, job_name):
        self.job_names.append(job_name)
        return self.job


class FakeServer:
    def __init__(self, build_number=7, console_output=""):
        self.build_number = build_number
        self.console_output = console_output
        self.build_calls = []
        self.console_calls = []

    def get_job_info(self, job_name):
        return {"nextBuildNumber": self.build_number}

    def build_job(self, job_name, params):
        self.build_calls.append((job_name, params))

    def get_build_console_output(self, job_name, build_number):
        self.console_calls.append((job_name, build_number))
        return self.console_output


class RaisingServer(FakeServer):
    def get_build_console_output(self, job_name, build_number):
        raise Exception("queued")


@pytest.mark.django_db
def test_upload_file_view_returns_workbook_payload(
    auth_client, campus_network, monkeypatch
):
    sheets = [{"name": "sheet1", "sheet1": [{"host": "1.1.1.1"}]}]
    monkeypatch.setattr(views, "parse_workbook", lambda *_args: "success")
    monkeypatch.setattr(
        views.GridDataManager,
        "get_sheets_by_campus_network",
        lambda self, _campus_network_id: sheets,
    )

    response = auth_client.post(
        f"/campus_network/{campus_network.id}/upload_file/",
        data={"up_file": SimpleUploadedFile("config.xlsx", b"xlsx-data")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert json.loads(payload["workbook"]) == sheets


@pytest.mark.django_db
def test_save_grid_data_view_updates_workbook(auth_client, campus_network, monkeypatch):
    sheets = [{"name": "sheet1", "sheet1": [{"host": "old"}]}]
    updated_calls = {}

    def fake_get_sheets_by_campus_network(self, _campus_network_id):
        return sheets

    def fake_create_or_update_db(self, campus_network_id, new_sheets, filename=None):
        updated_calls["campus_network_id"] = campus_network_id
        updated_calls["sheets"] = new_sheets
        updated_calls["filename"] = filename

    monkeypatch.setattr(
        views.GridDataManager,
        "get_sheets_by_campus_network",
        fake_get_sheets_by_campus_network,
    )
    monkeypatch.setattr(
        views.GridDataManager,
        "create_or_update_db",
        fake_create_or_update_db,
    )

    payload = {"data": [{"name": "sheet1", "sheet1": [{"host": "new"}]}]}
    response = auth_client.generic(
        "POST",
        reverse("save_data", kwargs={"campus_network_id": campus_network.id}),
        json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.content.decode("utf-8") == "Success"
    assert updated_calls["campus_network_id"] == campus_network.id
    assert updated_calls["sheets"] == [{"name": "sheet1", "sheet1": [{"host": "new"}]}]


@pytest.mark.django_db
def test_jenkins_console_log_view_strips_ansi(
    auth_client, action, campus_network, monkeypatch
):
    action_history = ActionHistory.objects.create(
        action_id=action,
        timestamp=views.timezone.now(),
        status="Running",
        jenkins_job_build_no=41,
        category_id=action.action_category,
        campus_network_id=campus_network,
    )
    monkeypatch.setattr(
        views,
        "server",
        FakeServer(console_output="\x1b[31mhello\x1b[0m from jenkins"),
    )

    response = auth_client.get(
        reverse("jenkinsconsoleLog", kwargs={"action_history_id": action_history.id})
    )

    assert response.status_code == 200
    assert response.content.decode("utf-8") == "hello from jenkins"


@pytest.mark.django_db
def test_jenkins_console_log_view_uses_fallback_message(
    auth_client, action, campus_network, monkeypatch
):
    action_history = ActionHistory.objects.create(
        action_id=action,
        timestamp=views.timezone.now(),
        status="Running",
        jenkins_job_build_no=41,
        category_id=action.action_category,
        campus_network_id=campus_network,
    )
    monkeypatch.setattr(views, "server", RaisingServer())

    response = auth_client.get(
        reverse("jenkinsconsoleLog", kwargs={"action_history_id": action_history.id})
    )

    assert response.status_code == 200
    assert "queued in the Jenkins Server" in response.content.decode("utf-8")


@pytest.mark.django_db
def test_add_campus_network_view_creates_network(auth_client, campus_type, monkeypatch):
    monkeypatch.setattr(views, "server", FakeServer(build_number=11))
    monkeypatch.setattr(views, "wait_and_get_build_status", lambda *_args: True)
    monkeypatch.setattr(
        views.ServerProperties,
        "getWorkspaceLocation",
        staticmethod(lambda: "/workspace"),
    )

    response = auth_client.post(
        reverse("campusnetworkadd"),
        data={
            "name": "campus-one",
            "description": "Campus one",
            "host_file": SimpleUploadedFile("hosts.txt", b"host data"),
            "campus_type": campus_type.id,
            "dynamic_ansible_workspace": "on",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"result": "success", "name": "campus-one"}
    campus_network = CampusNetwork.objects.get(name="campus-one")
    assert campus_network.status == "Initialized"
    assert campus_network.host_file == "host data"


@pytest.mark.django_db
def test_add_campus_network_view_cleans_up_on_failure(
    auth_client, campus_type, monkeypatch
):
    fake_server = FakeServer(build_number=11)
    monkeypatch.setattr(views, "server", fake_server)
    monkeypatch.setattr(views, "wait_and_get_build_status", lambda *_args: False)
    monkeypatch.setattr(
        views.ServerProperties,
        "getWorkspaceLocation",
        staticmethod(lambda: "/workspace"),
    )

    response = auth_client.post(
        reverse("campusnetworkadd"),
        data={
            "name": "campus-two",
            "description": "Campus two",
            "host_file": SimpleUploadedFile("hosts.txt", b"host data"),
            "campus_type": campus_type.id,
            "dynamic_ansible_workspace": "on",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"result": "failure", "name": "campus-two"}
    assert not CampusNetwork.objects.filter(name="campus-two").exists()
    assert fake_server.build_calls[0][1]["operation"] == "create"
    assert fake_server.build_calls[1][1]["operation"] == "delete"


@pytest.mark.django_db
def test_add_campus_network_view_retries_on_forbidden(
    auth_client, campus_type, monkeypatch
):
    class ForbiddenServer(FakeServer):
        def build_job(self, job_name, params):
            raise jenkins.JenkinsException("Forbidden: crumbs required")

    initial_server = ForbiddenServer(build_number=11)
    reauth_server = FakeServer(build_number=11)
    monkeypatch.setattr(views, "server", initial_server)
    monkeypatch.setattr(views, "wait_and_get_build_status", lambda *_args: True)
    monkeypatch.setattr(
        views.ServerProperties,
        "getWorkspaceLocation",
        staticmethod(lambda: "/workspace"),
    )
    monkeypatch.setattr(views.jenkins, "Jenkins", lambda *args, **kwargs: reauth_server)

    response = auth_client.post(
        reverse("campusnetworkadd"),
        data={
            "name": "campus-three",
            "description": "Campus three",
            "host_file": SimpleUploadedFile("hosts.txt", b"host data"),
            "campus_type": campus_type.id,
            "dynamic_ansible_workspace": "on",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"result": "success", "name": "campus-three"}
    assert len(reauth_server.build_calls) == 1
    assert reauth_server.build_calls[0][1]["operation"] == "create"


@pytest.mark.django_db
def test_edit_campus_network_view_updates_hosts(
    auth_client, campus_network, monkeypatch
):
    fake_server = FakeServer(build_number=12)
    monkeypatch.setattr(views, "server", fake_server)
    monkeypatch.setattr(views, "wait_and_get_build_status", lambda *_args: True)
    monkeypatch.setattr(
        views.ServerProperties,
        "getWorkspaceLocation",
        staticmethod(lambda: "/workspace"),
    )

    response = auth_client.post(
        reverse("campusnetworkedit", kwargs={"campus_network_id": campus_network.id}),
        data={
            "name": "campus-one",
            "description": "Updated campus",
            "host_file": "group_vars/all.yaml\nbuild_dir: /tmp/build",
            "dynamic_ansible_workspace": "",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"result": "success", "name": "campus-one"}
    campus_network.refresh_from_db()
    assert campus_network.status == "Hosts file modified"
    assert campus_network.host_file == "group_vars/all.yaml\nbuild_dir: /tmp/build"


@pytest.mark.django_db
def test_edit_campus_network_view_reports_failure(
    auth_client, campus_network, monkeypatch
):
    fake_server = FakeServer(build_number=12)
    monkeypatch.setattr(views, "server", fake_server)
    monkeypatch.setattr(views, "wait_and_get_build_status", lambda *_args: False)
    monkeypatch.setattr(
        views.ServerProperties,
        "getWorkspaceLocation",
        staticmethod(lambda: "/workspace"),
    )

    response = auth_client.post(
        reverse("campusnetworkedit", kwargs={"campus_network_id": campus_network.id}),
        data={
            "name": "campus-one",
            "description": "Updated campus",
            "host_file": "group_vars/all.yaml\nbuild_dir: /tmp/build",
            "dynamic_ansible_workspace": "",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"result": "failure", "name": "campus-one"}
    campus_network.refresh_from_db()
    assert campus_network.status == "Hosts file modification failed"


@pytest.mark.django_db
def test_delete_campus_network_view_deletes_network(
    auth_client, campus_network, monkeypatch
):
    fake_server = FakeServer(build_number=13)
    monkeypatch.setattr(views, "server", fake_server)
    monkeypatch.setattr(views, "wait_and_get_build_status", lambda *_args: True)
    monkeypatch.setattr(
        views.ServerProperties,
        "getWorkspaceLocation",
        staticmethod(lambda: "/workspace"),
    )

    response = auth_client.post(
        reverse("campusnetworkdelete"),
        data={"campus_network_ids": campus_network.id},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "success", "name": campus_network.name}
    assert not CampusNetwork.objects.filter(id=campus_network.id).exists()


@pytest.mark.django_db
def test_delete_campus_network_view_reports_failure(
    auth_client, campus_network, monkeypatch
):
    fake_server = FakeServer(build_number=13)
    monkeypatch.setattr(views, "server", fake_server)
    monkeypatch.setattr(views, "wait_and_get_build_status", lambda *_args: False)
    monkeypatch.setattr(
        views.ServerProperties,
        "getWorkspaceLocation",
        staticmethod(lambda: "/workspace"),
    )

    response = auth_client.post(
        reverse("campusnetworkdelete"),
        data={"campus_network_ids": campus_network.id},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "failure", "name": campus_network.name}
    assert CampusNetwork.objects.filter(id=campus_network.id).exists()


@pytest.mark.django_db
def test_trigger_action_returns_failure_without_workbook(
    auth_client, action, campus_network
):
    response = auth_client.get(
        reverse(
            "trigger_action_view",
            kwargs={"campus_network_id": campus_network.id, "action_id": action.id},
        )
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "failure",
        "name": action.action_name,
        "reason": "No data configured",
    }
    assert ActionHistory.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("dynamic_workspace", "expected_build_dir"),
    [
        (True, "/var/tmp/build/sample_type-campus_one"),
        (False, "/from/yaml"),
    ],
)
def test_trigger_action_uses_expected_build_dir(
    auth_client,
    action,
    campus_network,
    monkeypatch,
    dynamic_workspace,
    expected_build_dir,
):
    campus_network.dynamic_ansible_workspace = dynamic_workspace
    campus_network.save()
    Workbook.objects.create(name="campus_one.xlsx", campus_network_id=campus_network)

    fake_server = FakeServer(build_number=21)
    fake_job_runner = FakeJenkinsClient()
    configuration_data = {"group_vars/all.yaml": {"build_dir": "/from/yaml"}}
    recorded_updates = {}

    monkeypatch.setattr(views, "server", fake_server)
    monkeypatch.setattr(views, "CrumbRequester", lambda *args, **kwargs: object())
    monkeypatch.setattr(views, "Jenkins", lambda *args, **kwargs: fake_job_runner)
    monkeypatch.setattr(
        views, "create_workbook_from_db", lambda _campus_network_id: "/tmp/temp.xlsx"
    )
    monkeypatch.setattr(
        views, "create_new_inv", lambda _workbook_name: configuration_data
    )
    monkeypatch.setattr(
        views,
        "updateCampusNetworkStatusOnDB",
        lambda campus_network_id, status: recorded_updates.update(
            {"campus_network_id": campus_network_id, "status": status}
        ),
    )

    response = auth_client.get(
        reverse(
            "trigger_action_view",
            kwargs={"campus_network_id": campus_network.id, "action_id": action.id},
        )
    )

    assert response.status_code == 200
    assert response.json() == {"status": "success", "name": action.action_name}
    assert (
        fake_job_runner.job.calls[0]["build_params"]["build_dir"] == expected_build_dir
    )
    assert fake_job_runner.job.calls[0]["files"]["data.json"] == json.dumps(
        configuration_data
    )
    history = ActionHistory.objects.get()
    assert history.status == "Running"
    assert history.jenkins_job_build_no == 21
    assert recorded_updates == {
        "campus_network_id": campus_network.id,
        "status": f"Triggered {action.jenkins_url}-{campus_network.name}",
    }


@pytest.mark.django_db
def test_parse_workbook_rejects_invalid_host(tmp_path, campus_network):
    workbook = OpenPyxlWorkbook()
    sheet = workbook.active
    sheet.title = "base"
    sheet.append(["host", "name"])
    sheet.append(["etc/hosts", "value"])
    workbook_path = tmp_path / "invalid_hosts.xlsx"
    workbook.save(workbook_path)

    result = views.parse_workbook(workbook_path, campus_network.id)

    assert result == "invalid_host"
