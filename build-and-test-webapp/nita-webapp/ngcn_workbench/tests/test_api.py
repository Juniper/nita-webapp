# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
API endpoint tests for ngcn/api/ (ViewSets and @action endpoints).

Coverage:
  - Token auth endpoint
  - ActionCategoryViewSet  (read-only)
  - CampusTypeViewSet      (list/retrieve/delete + zip upload)
  - CampusNetworkViewSet   (full CRUD + workbook and trigger actions)
  - ActionViewSet          (read-only, campus_type_id filter)
  - ActionHistoryViewSet   (read-only, campus_network_id filter + console action)
"""
import io
import json

import pytest
from django.utils import timezone
from ngcn.api import views as api_views
from ngcn.models import ActionHistory, CampusNetwork, CampusType, Workbook
from rest_framework.test import APIClient

# ── Shared helpers ─────────────────────────────────────────────────────────────

class _FakeJob:
    def __init__(self):
        self.calls = []

    def invoke(self, **kwargs):
        self.calls.append(kwargs)


class _FakeJenkinsClient:
    def __init__(self, *args, **kwargs):
        self.job = _FakeJob()

    def get_job(self, job_name):
        return self.job


class _FakeServer:
    def get_job_info(self, job_name):
        return {"nextBuildNumber": 42}

    def get_build_console_output(self, job_name, build_number):
        return "\x1b[32mbuild output\x1b[0m"


class _RaisingServer:
    def get_build_console_output(self, *args, **kwargs):
        raise Exception("build is queued")


class _FakeStorage:
    def exists(self, name):
        return False

    def save(self, name, f):
        return name

    def delete(self, name):
        pass


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def action_history(db, action, campus_network):
    return ActionHistory.objects.create(
        action_id=action,
        timestamp=timezone.now(),
        status="Running",
        jenkins_job_build_no=7,
        category_id=action.action_category,
        campus_network_id=campus_network,
    )


# ── Authentication ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_unauthenticated_request_is_rejected():
    # SessionAuthentication is the primary authenticator and does not emit
    # WWW-Authenticate, so DRF returns 403 rather than 401.
    response = APIClient().get("/api/v1/networks/")
    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_token_endpoint_returns_token_for_valid_credentials(user, client):
    # conftest creates user with password "secret"
    response = client.post(
        "/api/v1/auth/token/",
        {"username": "tester", "password": "secret"},
    )
    assert response.status_code == 200
    assert "token" in response.json()


@pytest.mark.django_db
def test_token_endpoint_rejects_bad_credentials(client):
    response = client.post(
        "/api/v1/auth/token/",
        {"username": "tester", "password": "wrong"},
    )
    assert response.status_code == 400


# ── ActionCategoryViewSet ──────────────────────────────────────────────────────

@pytest.mark.django_db
def test_action_category_list(api_client, action_category):
    response = api_client.get("/api/v1/action-categories/")
    assert response.status_code == 200
    names = [r["category_name"] for r in response.json()["results"]]
    assert action_category.category_name in names


@pytest.mark.django_db
def test_action_category_retrieve(api_client, action_category):
    response = api_client.get(f"/api/v1/action-categories/{action_category.id}/")
    assert response.status_code == 200
    assert response.json()["category_name"] == action_category.category_name


# ── CampusTypeViewSet ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_network_type_list(api_client, campus_type):
    response = api_client.get("/api/v1/network-types/")
    assert response.status_code == 200
    names = [r["name"] for r in response.json()["results"]]
    assert campus_type.name in names


@pytest.mark.django_db
def test_network_type_retrieve_includes_nested_roles_and_resources(api_client, campus_type):
    response = api_client.get(f"/api/v1/network-types/{campus_type.id}/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == campus_type.name
    assert "roles" in data
    assert "resources" in data


@pytest.mark.django_db
def test_network_type_post_is_disabled(api_client):
    response = api_client.post("/api/v1/network-types/", {"name": "x"})
    assert response.status_code == 405


@pytest.mark.django_db
def test_network_type_delete(api_client, campus_type):
    response = api_client.delete(f"/api/v1/network-types/{campus_type.id}/")
    assert response.status_code == 204
    assert not CampusType.objects.filter(id=campus_type.id).exists()


@pytest.mark.django_db
def test_network_type_upload_returns_parser_result(api_client, monkeypatch):
    import django.core.files.storage as django_storage
    from django.http import JsonResponse

    monkeypatch.setattr(django_storage, "default_storage", _FakeStorage())
    monkeypatch.setattr(
        api_views.NetworkTypeParser,
        "parseProjectFile",
        lambda self, name: JsonResponse({"result": "success", "name": "mytype"}),
    )

    response = api_client.post(
        "/api/v1/network-types/upload/",
        {"app_zip_file": io.BytesIO(b"zip-data")},
        format="multipart",
    )
    assert response.status_code == 200
    assert response.json()["result"] == "success"
    assert response.json()["name"] == "mytype"


@pytest.mark.django_db
def test_network_type_upload_without_file_returns_400(api_client):
    response = api_client.post("/api/v1/network-types/upload/", {}, format="multipart")
    assert response.status_code == 400


# ── CampusNetworkViewSet — CRUD ────────────────────────────────────────────────

@pytest.mark.django_db
def test_network_list(api_client, campus_network):
    response = api_client.get("/api/v1/networks/")
    assert response.status_code == 200
    names = [r["name"] for r in response.json()["results"]]
    assert campus_network.name in names


@pytest.mark.django_db
def test_network_retrieve_includes_campus_type_name(api_client, campus_network):
    response = api_client.get(f"/api/v1/networks/{campus_network.id}/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == campus_network.name
    assert data["campus_type_name"] == campus_network.campus_type.name


@pytest.mark.django_db
def test_network_create(api_client, campus_type):
    response = api_client.post(
        "/api/v1/networks/",
        {
            "name": "new-net",
            "status": "Initialized",
            "description": "Test network",
            "host_file": "hosts data",
            "campus_type": campus_type.id,
        },
    )
    assert response.status_code == 201
    assert CampusNetwork.objects.filter(name="new-net").exists()


@pytest.mark.django_db
def test_network_partial_update(api_client, campus_network):
    response = api_client.patch(
        f"/api/v1/networks/{campus_network.id}/",
        {"description": "Updated description"},
    )
    assert response.status_code == 200
    campus_network.refresh_from_db()
    assert campus_network.description == "Updated description"


@pytest.mark.django_db
def test_network_delete(api_client, campus_network):
    response = api_client.delete(f"/api/v1/networks/{campus_network.id}/")
    assert response.status_code == 204
    assert not CampusNetwork.objects.filter(id=campus_network.id).exists()


# ── CampusNetworkViewSet — workbook actions ────────────────────────────────────

@pytest.mark.django_db
def test_get_workbook_returns_sheet_data(api_client, campus_network, monkeypatch):
    sheets = [{"name": "hosts", "hosts": [{"host": "10.0.0.1"}]}]
    monkeypatch.setattr(
        api_views.GridDataManager,
        "get_sheets_by_campus_network",
        lambda self, pk: sheets,
    )
    response = api_client.get(f"/api/v1/networks/{campus_network.id}/workbook/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["workbook"] == sheets


@pytest.mark.django_db
def test_upload_workbook_success(api_client, campus_network, monkeypatch):
    sheets = [{"name": "hosts", "hosts": []}]
    monkeypatch.setattr(api_views, "parse_workbook", lambda f, pk: "ok")
    monkeypatch.setattr(
        api_views.GridDataManager,
        "get_sheets_by_campus_network",
        lambda self, pk: sheets,
    )
    response = api_client.post(
        f"/api/v1/networks/{campus_network.id}/workbook/upload/",
        {"up_file": io.BytesIO(b"xlsx-data")},
        format="multipart",
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.django_db
def test_upload_workbook_invalid_host_returns_400(api_client, campus_network, monkeypatch):
    monkeypatch.setattr(api_views, "parse_workbook", lambda f, pk: "invalid_host")
    response = api_client.post(
        f"/api/v1/networks/{campus_network.id}/workbook/upload/",
        {"up_file": io.BytesIO(b"xlsx-data")},
        format="multipart",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_upload_workbook_without_file_returns_400(api_client, campus_network):
    response = api_client.post(
        f"/api/v1/networks/{campus_network.id}/workbook/upload/",
        {},
        format="multipart",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_save_workbook_success(api_client, campus_network, monkeypatch):
    sheets = [{"name": "hosts", "hosts": [{"host": "10.0.0.1"}]}]
    saved = {}

    def fake_get_sheets(self, pk):
        return sheets

    def fake_save(self, pk, data):
        saved["pk"] = pk
        saved["data"] = data

    monkeypatch.setattr(api_views.GridDataManager, "get_sheets_by_campus_network", fake_get_sheets)
    monkeypatch.setattr(api_views.GridDataManager, "create_or_update_db", fake_save)

    payload = json.dumps({"data": [{"name": "hosts", "hosts": [{"host": "10.0.0.2"}]}]})
    response = api_client.post(
        f"/api/v1/networks/{campus_network.id}/workbook/save/",
        data=payload,
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert int(saved["pk"]) == campus_network.id


@pytest.mark.django_db
def test_clear_workbook_returns_204(api_client, campus_network, monkeypatch):
    monkeypatch.setattr(
        api_views.GridDataManager, "delete_workbook", lambda self, pk: None
    )
    response = api_client.delete(f"/api/v1/networks/{campus_network.id}/workbook/clear/")
    assert response.status_code == 204


@pytest.mark.django_db
def test_download_workbook_error_returns_500(api_client, campus_network, monkeypatch):
    def _raise(pk):
        raise Exception("no workbook data")

    monkeypatch.setattr(api_views, "create_workbook", _raise)
    response = api_client.get(f"/api/v1/networks/{campus_network.id}/workbook/download/")
    assert response.status_code == 500


# ── CampusNetworkViewSet — trigger action ─────────────────────────────────────

@pytest.mark.django_db
def test_trigger_action_returns_202_and_creates_history(
    api_client, campus_network, action, monkeypatch
):
    Workbook.objects.create(name="wb", campus_network_id=campus_network)
    monkeypatch.setattr("ngcn.views._make_jenkins_server", lambda: _FakeServer())
    monkeypatch.setattr(api_views, "create_workbook_from_db", lambda pk: "test.xlsx")
    monkeypatch.setattr(
        api_views,
        "create_new_inv",
        lambda name: {"group_vars/all.yaml": {"build_dir": "/tmp/build"}},
    )
    monkeypatch.setattr("jenkinsapi.jenkins.Jenkins", _FakeJenkinsClient)
    monkeypatch.setattr(
        "jenkinsapi.utils.crumb_requester.CrumbRequester", lambda **kw: None
    )

    response = api_client.post(
        f"/api/v1/networks/{campus_network.id}/trigger/{action.id}/"
    )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "accepted"
    assert "action_history_id" in body
    assert ActionHistory.objects.filter(id=body["action_history_id"]).exists()


@pytest.mark.django_db
def test_trigger_action_with_no_workbook_returns_409(api_client, campus_network, action):
    response = api_client.post(
        f"/api/v1/networks/{campus_network.id}/trigger/{action.id}/"
    )
    assert response.status_code == 409


@pytest.mark.django_db
def test_trigger_action_with_unknown_action_returns_404(api_client, campus_network):
    response = api_client.post(f"/api/v1/networks/{campus_network.id}/trigger/99999/")
    assert response.status_code == 404


# ── ActionViewSet ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_action_list(api_client, action):
    response = api_client.get("/api/v1/actions/")
    assert response.status_code == 200
    names = [r["action_name"] for r in response.json()["results"]]
    assert action.action_name in names


@pytest.mark.django_db
def test_action_list_filter_by_campus_type(api_client, campus_type, action):
    response = api_client.get(f"/api/v1/actions/?campus_type_id={campus_type.id}")
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["action_name"] == action.action_name


@pytest.mark.django_db
def test_action_list_filter_returns_empty_for_unknown_campus_type(api_client):
    response = api_client.get("/api/v1/actions/?campus_type_id=99999")
    assert response.status_code == 200
    assert response.json()["results"] == []


# ── ActionHistoryViewSet ───────────────────────────────────────────────────────

@pytest.mark.django_db
def test_action_history_list(api_client, action_history):
    response = api_client.get("/api/v1/action-history/")
    assert response.status_code == 200
    ids = [r["id"] for r in response.json()["results"]]
    assert action_history.id in ids


@pytest.mark.django_db
def test_action_history_retrieve_includes_derived_fields(api_client, action_history):
    response = api_client.get(f"/api/v1/action-history/{action_history.id}/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Running"
    assert data["action_name"] == action_history.action_id.action_name
    assert data["network_name"] == action_history.campus_network_id.name
    assert data["category_name"] == action_history.category_id.category_name


@pytest.mark.django_db
def test_action_history_filter_by_campus_network(api_client, action_history, campus_network):
    response = api_client.get(
        f"/api/v1/action-history/?campus_network_id={campus_network.id}"
    )
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1

    response = api_client.get("/api/v1/action-history/?campus_network_id=99999")
    assert response.status_code == 200
    assert response.json()["results"] == []


@pytest.mark.django_db
def test_action_history_console_returns_ansi_stripped_output(
    api_client, action_history, monkeypatch
):
    monkeypatch.setattr("ngcn.views._make_jenkins_server", lambda: _FakeServer())
    response = api_client.get(f"/api/v1/action-history/{action_history.id}/console/")
    assert response.status_code == 200
    data = response.json()
    assert "console" in data
    # ANSI escape codes must be stripped
    assert "\x1b[" not in data["console"]
    assert "build output" in data["console"]


@pytest.mark.django_db
def test_action_history_console_returns_fallback_when_jenkins_unavailable(
    api_client, action_history, monkeypatch
):
    monkeypatch.setattr("ngcn.views._make_jenkins_server", lambda: _RaisingServer())
    response = api_client.get(f"/api/v1/action-history/{action_history.id}/console/")
    assert response.status_code == 200
    assert "queued" in response.json()["console"].lower()
