# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Tests for action-history visibility scoping.

Action history has no ownership of its own: it is visible exactly when the
network it belongs to is visible. These tests pin that rule and the 404
behaviour of the detail routes, including the console/stream routes that would
otherwise disclose Jenkins output for other users' networks.
"""

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from ngcn.models import ActionHistory, CampusNetwork, Team
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin", password="secret", role=User.ROLE_ADMIN
    )


@pytest.fixture
def power_user(db):
    return User.objects.create_user(
        username="power", password="secret", role=User.ROLE_POWER_USER
    )


@pytest.fixture
def alice(db):
    return User.objects.create_user(
        username="alice", password="secret", role=User.ROLE_USER
    )


@pytest.fixture
def bob(db):
    return User.objects.create_user(
        username="bob", password="secret", role=User.ROLE_USER
    )


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _make_network(name, owner, campus_type, team=None):
    return CampusNetwork.objects.create(
        name=name,
        status="ok",
        description="d",
        host_file="h",
        campus_type=campus_type,
        owner=owner,
        team=team,
    )


def _make_history(action, network, category, status="Success"):
    return ActionHistory.objects.create(
        action_id=action,
        timestamp=timezone.now(),
        status=status,
        jenkins_job_build_no=1,
        category_id=category,
        campus_network_id=network,
    )


# ── List scoping ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_user_sees_history_only_for_own_networks(
    alice, bob, campus_type, action, action_category
):
    mine = _make_network("Net-A", alice, campus_type)
    theirs = _make_network("Net-C", bob, campus_type)
    _make_history(action, mine, action_category)
    _make_history(action, theirs, action_category)

    resp = _client(alice).get("/api/v1/action-history/")
    assert resp.status_code == 200
    names = {h["network_name"] for h in resp.json()["results"]}
    assert names == {"Net-A"}


@pytest.mark.django_db
def test_user_sees_history_for_team_shared_network(
    alice, bob, campus_type, action, action_category
):
    team = Team.objects.create(name="Team-X", created_by=bob)
    team.members.add(alice)
    shared = _make_network("Shared-Net", bob, campus_type, team=team)
    _make_history(action, shared, action_category)

    resp = _client(alice).get("/api/v1/action-history/")
    assert resp.status_code == 200
    names = {h["network_name"] for h in resp.json()["results"]}
    assert "Shared-Net" in names


@pytest.mark.django_db
def test_network_filter_cannot_widen_scope(
    alice, bob, campus_type, action, action_category
):
    theirs = _make_network("Net-C", bob, campus_type)
    _make_history(action, theirs, action_category)

    resp = _client(alice).get(f"/api/v1/action-history/?campus_network_id={theirs.id}")
    assert resp.status_code == 200
    assert resp.json()["results"] == []


@pytest.mark.django_db
def test_category_filter_still_applies_within_scope(
    alice, campus_type, action, action_category, build_action_category
):
    mine = _make_network("Net-A", alice, campus_type)
    _make_history(action, mine, action_category)
    _make_history(action, mine, build_action_category)

    resp = _client(alice).get(
        f"/api/v1/action-history/?action_category_id={action_category.id}"
    )
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) == 1
    assert results[0]["category_name"] == "TEST"


@pytest.mark.django_db
def test_power_user_sees_all_history(
    power_user, bob, campus_type, action, action_category
):
    theirs = _make_network("Net-C", bob, campus_type)
    _make_history(action, theirs, action_category)

    resp = _client(power_user).get("/api/v1/action-history/")
    assert resp.status_code == 200
    assert resp.json()["count"] == 1


@pytest.mark.django_db
def test_admin_sees_all_history(admin_user, bob, campus_type, action, action_category):
    theirs = _make_network("Net-C", bob, campus_type)
    _make_history(action, theirs, action_category)

    resp = _client(admin_user).get("/api/v1/action-history/")
    assert resp.status_code == 200
    assert resp.json()["count"] == 1


@pytest.mark.django_db
def test_team_membership_does_not_duplicate_rows(
    alice, bob, campus_type, action, action_category
):
    team = Team.objects.create(name="Team-X", created_by=bob)
    team.members.add(alice)
    for name in ("carol", "dave", "erin"):
        team.members.add(User.objects.create_user(username=name, password="secret"))
    shared = _make_network("Shared-Net", bob, campus_type, team=team)
    _make_history(action, shared, action_category)

    resp = _client(alice).get("/api/v1/action-history/")
    assert resp.status_code == 200
    assert resp.json()["count"] == 1


@pytest.mark.django_db
def test_history_networks_are_subset_of_visible_networks(
    alice, bob, campus_type, action, action_category
):
    """The two viewsets must agree on what the user can see."""
    team = Team.objects.create(name="Team-X", created_by=bob)
    team.members.add(alice)
    mine = _make_network("Net-A", alice, campus_type)
    shared = _make_network("Shared-Net", bob, campus_type, team=team)
    theirs = _make_network("Net-C", bob, campus_type)
    for net in (mine, shared, theirs):
        _make_history(action, net, action_category)

    client = _client(alice)
    history_names = {
        h["network_name"]
        for h in client.get("/api/v1/action-history/").json()["results"]
    }
    network_names = {
        n["name"] for n in client.get("/api/v1/networks/").json()["results"]
    }
    assert history_names <= network_names
    assert "Net-C" not in history_names


# ── Detail-route scoping ────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_out_of_scope_retrieve_returns_404(
    alice, bob, campus_type, action, action_category
):
    theirs = _make_network("Net-C", bob, campus_type)
    entry = _make_history(action, theirs, action_category)

    resp = _client(alice).get(f"/api/v1/action-history/{entry.id}/")
    assert resp.status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize("route", ["console", "stream", "robot-summary"])
def test_out_of_scope_subroutes_return_404(
    alice, bob, campus_type, action, action_category, route
):
    """No Jenkins output may leak for a network the caller cannot see."""
    theirs = _make_network("Net-C", bob, campus_type)
    entry = _make_history(action, theirs, action_category)

    resp = _client(alice).get(f"/api/v1/action-history/{entry.id}/{route}/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_owner_can_retrieve_own_history_entry(
    alice, campus_type, action, action_category
):
    mine = _make_network("Net-A", alice, campus_type)
    entry = _make_history(action, mine, action_category)

    resp = _client(alice).get(f"/api/v1/action-history/{entry.id}/")
    assert resp.status_code == 200
    assert resp.json()["network_name"] == "Net-A"
