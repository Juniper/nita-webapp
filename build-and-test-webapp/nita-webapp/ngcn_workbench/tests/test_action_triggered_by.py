# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Tests for action-history attribution (``triggered_by_username``).

The field is a durable string snapshot rather than a foreign key, so these
tests pin the two properties that motivated that choice: the recorded name
survives a rename of the user, and it survives deletion of the user without
blocking it.
"""

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from ngcn.api import views as api_views
from ngcn.models import ActionHistory, CampusNetwork, Workbook
from rest_framework.test import APIClient

User = get_user_model()


class _FakeJob:
    def invoke(self, **kwargs):
        pass


class _FakeJenkinsClient:
    def __init__(self, *args, **kwargs):
        self.job = _FakeJob()

    def get_job(self, job_name):
        return self.job


class _FakeServer:
    def get_job_info(self, job_name):
        return {"nextBuildNumber": 42}


@pytest.fixture
def alice(db):
    return User.objects.create_user(
        username="alice", password="secret", role=User.ROLE_ADMIN
    )


@pytest.fixture
def bob(db):
    return User.objects.create_user(
        username="bob", password="secret", role=User.ROLE_ADMIN
    )


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def owned_network(db, campus_type, alice):
    return CampusNetwork.objects.create(
        name="net-attrib",
        status="ok",
        description="d",
        host_file="h",
        campus_type=campus_type,
        owner=alice,
    )


def _mock_jenkins(monkeypatch):
    """Patch out every Jenkins touchpoint used by the trigger endpoint."""
    import jenkinsapi.jenkins as jenkinsapi_jenkins
    import jenkinsapi.utils.crumb_requester as jenkinsapi_crumb

    monkeypatch.setattr(api_views, "create_workbook_from_db", lambda pk: "test.xlsx")
    monkeypatch.setattr(
        api_views,
        "create_new_inv",
        lambda name: {"group_vars/all.yaml": {"build_dir": "/tmp/build"}},
    )
    monkeypatch.setattr(
        "ngcn.jenkins_config._make_jenkins_server", lambda: _FakeServer()
    )
    monkeypatch.setattr(jenkinsapi_jenkins, "Jenkins", _FakeJenkinsClient)
    monkeypatch.setattr(jenkinsapi_crumb, "CrumbRequester", lambda *a, **kw: object())


def _trigger(user, network, action, monkeypatch):
    _mock_jenkins(monkeypatch)
    Workbook.objects.get_or_create(name="wb", campus_network_id=network)
    resp = _client(user).post(f"/api/v1/networks/{network.id}/trigger/{action.id}/")
    assert resp.status_code == 202
    return ActionHistory.objects.get(id=resp.json()["action_history_id"])


# ── Capture ─────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_trigger_records_acting_user(alice, owned_network, action, monkeypatch):
    entry = _trigger(alice, owned_network, action, monkeypatch)
    assert entry.triggered_by_username == "alice"


@pytest.mark.django_db
def test_each_trigger_records_its_own_actor(
    alice, bob, owned_network, action, monkeypatch
):
    first = _trigger(alice, owned_network, action, monkeypatch)
    second = _trigger(bob, owned_network, action, monkeypatch)
    assert first.triggered_by_username == "alice"
    assert second.triggered_by_username == "bob"


# ── Exposure ────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_field_is_exposed_by_list_and_retrieve(
    alice, owned_network, action, monkeypatch
):
    entry = _trigger(alice, owned_network, action, monkeypatch)
    client = _client(alice)

    listed = client.get("/api/v1/action-history/").json()["results"]
    assert listed[0]["triggered_by_username"] == "alice"

    retrieved = client.get(f"/api/v1/action-history/{entry.id}/").json()
    assert retrieved["triggered_by_username"] == "alice"


@pytest.mark.django_db
def test_preexisting_entries_have_empty_actor(alice, owned_network, action):
    """Rows created before the field existed carry the empty-string default."""
    entry = ActionHistory.objects.create(
        action_id=action,
        timestamp=timezone.now(),
        status="Success",
        jenkins_job_build_no=1,
        category_id=action.action_category,
        campus_network_id=owned_network,
    )
    assert entry.triggered_by_username == ""

    body = _client(alice).get(f"/api/v1/action-history/{entry.id}/").json()
    assert body["triggered_by_username"] == ""


# ── Durability ──────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_attribution_survives_username_change(
    alice, owned_network, action, monkeypatch
):
    entry = _trigger(alice, owned_network, action, monkeypatch)
    alice.username = "alice.smith"
    alice.save()

    entry.refresh_from_db()
    assert entry.triggered_by_username == "alice"


@pytest.mark.django_db
def test_attribution_survives_user_deletion(
    alice, bob, owned_network, action, monkeypatch
):
    """Deleting the actor must not be blocked by, nor erase, the history row."""
    entry = _trigger(bob, owned_network, action, monkeypatch)
    assert entry.triggered_by_username == "bob"

    bob.delete()

    entry.refresh_from_db()
    assert entry.triggered_by_username == "bob"
    assert ActionHistory.objects.filter(id=entry.id).exists()
