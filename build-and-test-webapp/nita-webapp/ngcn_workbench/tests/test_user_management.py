# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Tests for the user-management change.

Covers: self-registration, roles + me endpoint, teams, network ownership
scoping, network-type curation, permission classes, and the admin user API.
"""

import pytest
from django.contrib.auth import get_user_model
from ngcn.api.permissions import (
    IsAdminRole,
    IsOwnerOrAdmin,
    IsOwnerOrTeamMemberOrAdmin,
    IsPowerUserOrAdmin,
)
from ngcn.models import CampusNetwork, CampusType, Team
from rest_framework.test import APIClient, APIRequestFactory

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
def regular_user(db):
    return User.objects.create_user(
        username="regular", password="secret", role=User.ROLE_USER
    )


def _client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ── Self-registration ──────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_registration_success():
    resp = APIClient().post(
        "/api/v1/auth/register/",
        {"username": "newbie", "password": "sTr0ngPassw0rd!"},
        format="json",
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "newbie"
    assert data["role"] == "user"
    assert User.objects.get(username="newbie").role == User.ROLE_USER


@pytest.mark.django_db
def test_registration_duplicate_username(regular_user):
    resp = APIClient().post(
        "/api/v1/auth/register/",
        {"username": "regular", "password": "sTr0ngPassw0rd!"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_registration_weak_password():
    resp = APIClient().post(
        "/api/v1/auth/register/",
        {"username": "weak", "password": "123"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_registration_ignores_role_escalation():
    resp = APIClient().post(
        "/api/v1/auth/register/",
        {"username": "sneaky", "password": "sTr0ngPassw0rd!", "role": "admin"},
        format="json",
    )
    assert resp.status_code == 201
    assert User.objects.get(username="sneaky").role == User.ROLE_USER


# ── Roles + me endpoint ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_me_returns_role_and_teams(power_user):
    team = Team.objects.create(name="T1", created_by=power_user)
    team.members.add(power_user)
    resp = _client(power_user).get("/api/v1/auth/me/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "power_user"
    assert data["teams"] == [team.id]


# ── Teams ───────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_power_user_creates_team(power_user):
    resp = _client(power_user).post(
        "/api/v1/teams/", {"name": "Project-X"}, format="json"
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Project-X"
    assert Team.objects.get(name="Project-X").created_by == power_user


@pytest.mark.django_db
def test_regular_user_cannot_create_team(regular_user):
    resp = _client(regular_user).post("/api/v1/teams/", {"name": "Nope"}, format="json")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_duplicate_team_name_rejected(power_user):
    Team.objects.create(name="Project-X", created_by=power_user)
    resp = _client(power_user).post(
        "/api/v1/teams/", {"name": "Project-X"}, format="json"
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_regular_user_cannot_list_teams(regular_user):
    resp = _client(regular_user).get("/api/v1/teams/")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_power_user_lists_only_own_teams(power_user):
    other = User.objects.create_user(
        username="power2", password="secret", role=User.ROLE_POWER_USER
    )
    Team.objects.create(name="Mine", created_by=power_user)
    Team.objects.create(name="Theirs", created_by=other)
    resp = _client(power_user).get("/api/v1/teams/")
    assert resp.status_code == 200
    names = {t["name"] for t in resp.json()["results"]}
    assert names == {"Mine"}


@pytest.mark.django_db
def test_admin_lists_all_teams(admin_user, power_user):
    Team.objects.create(name="A", created_by=power_user)
    Team.objects.create(name="B", created_by=power_user)
    resp = _client(admin_user).get("/api/v1/teams/")
    assert resp.status_code == 200
    assert resp.json()["count"] == 2


@pytest.mark.django_db
def test_power_user_add_and_remove_member(power_user, regular_user):
    team = Team.objects.create(name="T", created_by=power_user)
    add = _client(power_user).post(
        f"/api/v1/teams/{team.id}/members/",
        {"user_id": regular_user.id},
        format="json",
    )
    assert add.status_code == 200
    assert team.members.filter(pk=regular_user.pk).exists()

    remove = _client(power_user).delete(
        f"/api/v1/teams/{team.id}/members/{regular_user.id}/"
    )
    assert remove.status_code == 204
    assert not team.members.filter(pk=regular_user.pk).exists()


@pytest.mark.django_db
def test_power_user_cannot_manage_others_team(power_user):
    other = User.objects.create_user(
        username="power2", password="secret", role=User.ROLE_POWER_USER
    )
    team = Team.objects.create(name="Theirs", created_by=other)
    resp = _client(power_user).post(
        f"/api/v1/teams/{team.id}/members/",
        {"user_id": power_user.id},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_delete_team_nulls_networks(power_user, campus_type):
    team = Team.objects.create(name="T", created_by=power_user)
    net = CampusNetwork.objects.create(
        name="net-team",
        status="ok",
        description="d",
        host_file="h",
        campus_type=campus_type,
        owner=power_user,
        team=team,
    )
    resp = _client(power_user).delete(f"/api/v1/teams/{team.id}/")
    assert resp.status_code == 204
    net.refresh_from_db()
    assert net.team is None


# ── Network ownership scoping ────────────────────────────────────────────────────


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


@pytest.mark.django_db
def test_user_sees_only_own_networks(regular_user, campus_type):
    bob = User.objects.create_user(username="bob", password="secret")
    _make_network("Net-A", regular_user, campus_type)
    _make_network("Net-B", regular_user, campus_type)
    _make_network("Net-C", bob, campus_type)
    resp = _client(regular_user).get("/api/v1/networks/")
    assert resp.status_code == 200
    names = {n["name"] for n in resp.json()["results"]}
    assert names == {"Net-A", "Net-B"}


@pytest.mark.django_db
def test_user_sees_team_networks(regular_user, campus_type):
    bob = User.objects.create_user(username="bob", password="secret")
    team = Team.objects.create(name="T", created_by=bob)
    team.members.add(regular_user)
    _make_network("Shared-Net", bob, campus_type, team=team)
    resp = _client(regular_user).get("/api/v1/networks/")
    names = {n["name"] for n in resp.json()["results"]}
    assert "Shared-Net" in names


@pytest.mark.django_db
def test_cross_user_retrieve_404(regular_user, campus_type):
    bob = User.objects.create_user(username="bob", password="secret")
    net = _make_network("Net-C", bob, campus_type)
    resp = _client(regular_user).get(f"/api/v1/networks/{net.id}/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_admin_sees_all_networks(admin_user, regular_user, campus_type):
    _make_network("Net-A", regular_user, campus_type)
    _make_network("Net-B", admin_user, campus_type)
    resp = _client(admin_user).get("/api/v1/networks/")
    assert resp.json()["count"] == 2


@pytest.mark.django_db
def test_team_member_cannot_modify_shared_network(regular_user, campus_type):
    bob = User.objects.create_user(username="bob", password="secret")
    team = Team.objects.create(name="T", created_by=bob)
    team.members.add(regular_user)
    net = _make_network("Shared-Net", bob, campus_type, team=team)
    resp = _client(regular_user).patch(
        f"/api/v1/networks/{net.id}/", {"description": "hacked"}, format="json"
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_owner_can_update_network(regular_user, campus_type):
    net = _make_network("Net-A", regular_user, campus_type)
    resp = _client(regular_user).patch(
        f"/api/v1/networks/{net.id}/", {"description": "updated"}, format="json"
    )
    assert resp.status_code == 200
    net.refresh_from_db()
    assert net.description == "updated"


# ── Network-type curation ────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_regular_user_cannot_delete_network_type(regular_user, power_user, campus_type):
    campus_type.created_by = power_user
    campus_type.save()
    resp = _client(regular_user).delete(f"/api/v1/network-types/{campus_type.id}/")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_non_creator_power_user_cannot_delete_type(power_user, campus_type):
    other = User.objects.create_user(
        username="power2", password="secret", role=User.ROLE_POWER_USER
    )
    campus_type.created_by = other
    campus_type.save()
    resp = _client(power_user).delete(f"/api/v1/network-types/{campus_type.id}/")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_creator_can_delete_type(power_user, campus_type):
    campus_type.created_by = power_user
    campus_type.save()
    resp = _client(power_user).delete(f"/api/v1/network-types/{campus_type.id}/")
    assert resp.status_code == 204


@pytest.mark.django_db
def test_admin_can_delete_any_type(admin_user, power_user, campus_type):
    campus_type.created_by = power_user
    campus_type.save()
    resp = _client(admin_user).delete(f"/api/v1/network-types/{campus_type.id}/")
    assert resp.status_code == 204


@pytest.mark.django_db
def test_any_user_can_list_types(regular_user, campus_type):
    resp = _client(regular_user).get("/api/v1/network-types/")
    assert resp.status_code == 200


# ── Admin user management ────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_admin_lists_users(admin_user, regular_user):
    resp = _client(admin_user).get("/api/v1/users/")
    assert resp.status_code == 200
    assert resp.json()["count"] >= 2


@pytest.mark.django_db
def test_non_admin_cannot_list_users(regular_user):
    resp = _client(regular_user).get("/api/v1/users/")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_admin_changes_role(admin_user, regular_user):
    resp = _client(admin_user).patch(
        f"/api/v1/users/{regular_user.id}/", {"role": "power_user"}, format="json"
    )
    assert resp.status_code == 200
    regular_user.refresh_from_db()
    assert regular_user.role == User.ROLE_POWER_USER


@pytest.mark.django_db
def test_admin_deactivates_user(admin_user, regular_user):
    resp = _client(admin_user).patch(
        f"/api/v1/users/{regular_user.id}/", {"is_active": False}, format="json"
    )
    assert resp.status_code == 200
    regular_user.refresh_from_db()
    assert regular_user.is_active is False


@pytest.mark.django_db
def test_delete_blocked_by_owned_network(admin_user, regular_user, campus_type):
    _make_network("Net-A", regular_user, campus_type)
    resp = _client(admin_user).delete(f"/api/v1/users/{regular_user.id}/")
    assert resp.status_code == 409
    assert "Net-A" in resp.json()["networks"]


@pytest.mark.django_db
def test_transfer_then_delete(admin_user, regular_user, campus_type):
    bob = User.objects.create_user(username="bob", password="secret")
    _make_network("Net-A", regular_user, campus_type)
    transfer = _client(admin_user).post(
        f"/api/v1/users/{regular_user.id}/transfer/",
        {"networks_to": bob.id},
        format="json",
    )
    assert transfer.status_code == 200
    assert CampusNetwork.objects.get(name="Net-A").owner == bob
    delete = _client(admin_user).delete(f"/api/v1/users/{regular_user.id}/")
    assert delete.status_code == 204


@pytest.mark.django_db
def test_transfer_invalid_recipient(admin_user, regular_user, campus_type):
    _make_network("Net-A", regular_user, campus_type)
    resp = _client(admin_user).post(
        f"/api/v1/users/{regular_user.id}/transfer/",
        {"networks_to": 999999},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_admin_cannot_delete_self(admin_user):
    resp = _client(admin_user).delete(f"/api/v1/users/{admin_user.id}/")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_delete_user_with_no_resources(admin_user, regular_user):
    resp = _client(admin_user).delete(f"/api/v1/users/{regular_user.id}/")
    assert resp.status_code == 204


# ── Permission classes (unit) ────────────────────────────────────────────────────


@pytest.mark.django_db
def test_permission_classes_unit(admin_user, power_user, regular_user, campus_type):
    factory = APIRequestFactory()

    def req(user, method="get"):
        r = getattr(factory, method)("/")
        r.user = user
        return r

    assert IsAdminRole().has_permission(req(admin_user), None) is True
    assert IsAdminRole().has_permission(req(power_user), None) is False

    assert IsPowerUserOrAdmin().has_permission(req(power_user), None) is True
    assert IsPowerUserOrAdmin().has_permission(req(regular_user), None) is False

    net = _make_network("N", regular_user, campus_type)
    assert IsOwnerOrAdmin().has_object_permission(req(regular_user), None, net) is True
    assert IsOwnerOrAdmin().has_object_permission(req(admin_user), None, net) is True
    bob = User.objects.create_user(username="bob", password="secret")
    assert IsOwnerOrAdmin().has_object_permission(req(bob), None, net) is False

    team = Team.objects.create(name="T", created_by=regular_user)
    team.members.add(bob)
    shared = _make_network("S", regular_user, campus_type, team=team)
    # Team member: read yes, write no.
    assert (
        IsOwnerOrTeamMemberOrAdmin().has_object_permission(
            req(bob, "get"), None, shared
        )
        is True
    )
    assert (
        IsOwnerOrTeamMemberOrAdmin().has_object_permission(
            req(bob, "patch"), None, shared
        )
        is False
    )


# ── Bootstrap / create_admin command ─────────────────────────────────────────────


@pytest.mark.django_db
def test_create_admin_command_creates_admin():
    from django.core.management import call_command

    call_command("create_admin", username="boss", password="sTr0ngPassw0rd!")
    boss = User.objects.get(username="boss")
    assert boss.role == User.ROLE_ADMIN
    assert boss.is_staff is True


@pytest.mark.django_db
def test_create_admin_command_is_idempotent():
    from django.core.management import call_command

    User.objects.create_user(username="boss", password="old", role=User.ROLE_USER)
    call_command("create_admin", username="boss", password="new")
    boss = User.objects.get(username="boss")
    assert boss.role == User.ROLE_ADMIN
    assert User.objects.filter(username="boss").count() == 1


@pytest.mark.django_db
def test_bootstrap_admin_from_env(monkeypatch):
    from ngcn.apps import bootstrap_admin_from_env

    monkeypatch.setenv("NITA_BOOTSTRAP_ADMIN_USERNAME", "envadmin")
    monkeypatch.setenv("NITA_BOOTSTRAP_ADMIN_PASSWORD", "sTr0ngPassw0rd!")
    monkeypatch.setenv("NITA_BOOTSTRAP_ADMIN_EMAIL", "env@example.com")
    created = bootstrap_admin_from_env()
    assert created is not None
    assert created.role == User.ROLE_ADMIN


@pytest.mark.django_db
def test_bootstrap_admin_noop_when_users_exist(monkeypatch, regular_user):
    from ngcn.apps import bootstrap_admin_from_env

    monkeypatch.setenv("NITA_BOOTSTRAP_ADMIN_USERNAME", "envadmin")
    monkeypatch.setenv("NITA_BOOTSTRAP_ADMIN_PASSWORD", "sTr0ngPassw0rd!")
    assert bootstrap_admin_from_env() is None
    assert not User.objects.filter(username="envadmin").exists()


# ── User directory (member picker) ────────────────────────────────────────────────


@pytest.mark.django_db
def test_directory_lists_id_and_username_for_power_user(
    power_user, regular_user, admin_user
):
    resp = _client(power_user).get("/api/v1/users/directory/")
    assert resp.status_code == 200
    rows = resp.json()
    assert {"power", "regular", "admin"} <= {r["username"] for r in rows}
    assert set(rows[0].keys()) == {"id", "username"}


@pytest.mark.django_db
def test_directory_forbidden_for_regular_user(regular_user):
    resp = _client(regular_user).get("/api/v1/users/directory/")
    assert resp.status_code == 403


# ── Network serializer owner/team display fields ─────────────────────────────────


@pytest.mark.django_db
def test_network_exposes_owner_username_and_team_name(regular_user, campus_type):
    team = Team.objects.create(name="Blue", created_by=regular_user)
    team.members.add(regular_user)
    net = _make_network("Net-A", regular_user, campus_type, team=team)
    resp = _client(regular_user).get(f"/api/v1/networks/{net.id}/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["owner_username"] == "regular"
    assert data["team_name"] == "Blue"


@pytest.mark.django_db
def test_network_owner_team_null_when_unset(admin_user, campus_type):
    net = CampusNetwork.objects.create(
        name="Orphan",
        status="ok",
        description="d",
        host_file="h",
        campus_type=campus_type,
    )
    resp = _client(admin_user).get(f"/api/v1/networks/{net.id}/")
    assert resp.status_code == 200
    assert resp.json()["owner_username"] is None
    assert resp.json()["team_name"] is None


# ── Admin user creation ──────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_admin_creates_user_with_role(admin_user):
    resp = _client(admin_user).post(
        "/api/v1/users/",
        {
            "username": "carol",
            "email": "carol@example.com",
            "role": "power_user",
            "password": "sTr0ngPassw0rd!",
        },
        format="json",
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "carol"
    assert data["role"] == "power_user"
    assert data["is_active"] is True
    assert "password" not in data
    carol = User.objects.get(username="carol")
    assert carol.role == User.ROLE_POWER_USER
    assert carol.check_password("sTr0ngPassw0rd!")


@pytest.mark.django_db
def test_admin_creates_admin_user(admin_user):
    resp = _client(admin_user).post(
        "/api/v1/users/",
        {"username": "carol", "role": "admin", "password": "sTr0ngPassw0rd!"},
        format="json",
    )
    assert resp.status_code == 201
    assert User.objects.get(username="carol").role == User.ROLE_ADMIN


@pytest.mark.django_db
def test_admin_create_duplicate_username_rejected(admin_user, regular_user):
    resp = _client(admin_user).post(
        "/api/v1/users/",
        {"username": "regular", "role": "user", "password": "sTr0ngPassw0rd!"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_admin_create_weak_password_rejected(admin_user):
    resp = _client(admin_user).post(
        "/api/v1/users/",
        {"username": "weakling", "role": "user", "password": "123"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_non_admin_cannot_create_user(power_user):
    resp = _client(power_user).post(
        "/api/v1/users/",
        {"username": "carol", "role": "user", "password": "sTr0ngPassw0rd!"},
        format="json",
    )
    assert resp.status_code == 403


# ── Admin password reset ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_admin_resets_another_users_password(admin_user, regular_user):
    resp = _client(admin_user).post(
        f"/api/v1/users/{regular_user.id}/set_password/",
        {"password": "N3wPassw0rd!x"},
        format="json",
    )
    assert resp.status_code == 200
    assert "password" not in resp.json()
    regular_user.refresh_from_db()
    assert regular_user.check_password("N3wPassw0rd!x")


@pytest.mark.django_db
def test_admin_resets_own_password(admin_user):
    resp = _client(admin_user).post(
        f"/api/v1/users/{admin_user.id}/set_password/",
        {"password": "N3wPassw0rd!x"},
        format="json",
    )
    assert resp.status_code == 200
    admin_user.refresh_from_db()
    assert admin_user.check_password("N3wPassw0rd!x")


@pytest.mark.django_db
def test_set_password_weak_rejected(admin_user, regular_user):
    resp = _client(admin_user).post(
        f"/api/v1/users/{regular_user.id}/set_password/",
        {"password": "123"},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_non_admin_cannot_set_password(power_user, regular_user):
    resp = _client(power_user).post(
        f"/api/v1/users/{regular_user.id}/set_password/",
        {"password": "N3wPassw0rd!x"},
        format="json",
    )
    assert resp.status_code == 403


# ── Self-registration flag ───────────────────────────────────────────────────────


@pytest.mark.django_db
def test_registration_enabled_by_default(settings):
    settings.SELF_REGISTRATION_ENABLED = True
    resp = APIClient().post(
        "/api/v1/auth/register/",
        {"username": "opener", "password": "sTr0ngPassw0rd!"},
        format="json",
    )
    assert resp.status_code == 201


@pytest.mark.django_db
def test_registration_disabled_returns_403(settings):
    settings.SELF_REGISTRATION_ENABLED = False
    resp = APIClient().post(
        "/api/v1/auth/register/",
        {"username": "blocked", "password": "sTr0ngPassw0rd!"},
        format="json",
    )
    assert resp.status_code == 403
    assert not User.objects.filter(username="blocked").exists()


# ── Last-administrator protection ────────────────────────────────────────────────


@pytest.mark.django_db
def test_cannot_demote_last_admin(admin_user):
    resp = _client(admin_user).patch(
        f"/api/v1/users/{admin_user.id}/", {"role": "power_user"}, format="json"
    )
    assert resp.status_code == 400
    admin_user.refresh_from_db()
    assert admin_user.role == User.ROLE_ADMIN


@pytest.mark.django_db
def test_cannot_deactivate_last_admin(admin_user):
    resp = _client(admin_user).patch(
        f"/api/v1/users/{admin_user.id}/", {"is_active": False}, format="json"
    )
    assert resp.status_code == 400
    admin_user.refresh_from_db()
    assert admin_user.is_active is True


@pytest.mark.django_db
def test_cannot_delete_last_admin(admin_user):
    # The delete guard is exercised at the helper level: deleting the sole active
    # admin would remove the last administrator. (Via the API the self-delete
    # guard also blocks this — see test_admin_cannot_delete_self.)
    from ngcn.api.views import UserViewSet

    assert (
        UserViewSet._would_remove_last_active_admin(admin_user, deleting=True) is True
    )
    other = User.objects.create_user(
        username="other-admin", password="secret", role=User.ROLE_ADMIN
    )
    assert (
        UserViewSet._would_remove_last_active_admin(admin_user, deleting=True) is False
    )
    assert UserViewSet._would_remove_last_active_admin(other, deleting=True) is False


@pytest.mark.django_db
def test_demote_admin_allowed_when_another_admin_exists(admin_user):
    other = User.objects.create_user(
        username="other-admin", password="secret", role=User.ROLE_ADMIN
    )
    resp = _client(admin_user).patch(
        f"/api/v1/users/{other.id}/", {"role": "power_user"}, format="json"
    )
    assert resp.status_code == 200
    other.refresh_from_db()
    assert other.role == User.ROLE_POWER_USER


# ── network-sharing-access: power_user reach + /teams/mine/ + assign constraint ─


def _mock_network_delete_jenkins(monkeypatch):
    """Patch the Jenkins helpers used by CampusNetworkViewSet.destroy."""
    import ngcn.jenkins_jobs as jenkins_jobs
    import ngcn.utils as ngcn_utils

    monkeypatch.setattr(jenkins_jobs, "invoke_job", lambda *a, **kw: 1)
    monkeypatch.setattr(
        ngcn_utils.ServerProperties, "getWorkspaceLocation", staticmethod(lambda: "")
    )


@pytest.mark.django_db
def test_power_user_sees_all_networks(power_user, regular_user, campus_type):
    bob = User.objects.create_user(username="bob", password="secret")
    _make_network("Net-A", regular_user, campus_type)
    _make_network("Net-C", bob, campus_type)
    resp = _client(power_user).get("/api/v1/networks/")
    assert resp.status_code == 200
    names = {n["name"] for n in resp.json()["results"]}
    assert {"Net-A", "Net-C"} <= names


@pytest.mark.django_db
def test_power_user_retrieves_any_network(power_user, campus_type):
    bob = User.objects.create_user(username="bob", password="secret")
    net = _make_network("Net-C", bob, campus_type)
    resp = _client(power_user).get(f"/api/v1/networks/{net.id}/")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_power_user_can_update_any_network(power_user, campus_type):
    bob = User.objects.create_user(username="bob", password="secret")
    net = _make_network("Net-C", bob, campus_type)
    resp = _client(power_user).patch(
        f"/api/v1/networks/{net.id}/", {"description": "by power"}, format="json"
    )
    assert resp.status_code == 200
    net.refresh_from_db()
    assert net.description == "by power"


@pytest.mark.django_db
def test_power_user_can_delete_any_network(power_user, campus_type, monkeypatch):
    bob = User.objects.create_user(username="bob", password="secret")
    net = _make_network("Net-C", bob, campus_type)
    _mock_network_delete_jenkins(monkeypatch)
    resp = _client(power_user).delete(f"/api/v1/networks/{net.id}/")
    assert resp.status_code == 202
    assert not CampusNetwork.objects.filter(pk=net.id).exists()


@pytest.mark.django_db
def test_teams_mine_returns_id_and_name(regular_user):
    creator = User.objects.create_user(
        username="creator", password="secret", role=User.ROLE_POWER_USER
    )
    t1 = Team.objects.create(name="Team-X", created_by=creator)
    t2 = Team.objects.create(name="Team-Y", created_by=creator)
    t1.members.add(regular_user)
    t2.members.add(regular_user)
    resp = _client(regular_user).get("/api/v1/teams/mine/")
    assert resp.status_code == 200
    assert resp.json() == [
        {"id": t1.id, "name": "Team-X"},
        {"id": t2.id, "name": "Team-Y"},
    ]


@pytest.mark.django_db
def test_teams_mine_empty_when_no_membership(regular_user):
    resp = _client(regular_user).get("/api/v1/teams/mine/")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.django_db
def test_teams_mine_excludes_non_member_teams(regular_user):
    creator = User.objects.create_user(
        username="creator", password="secret", role=User.ROLE_POWER_USER
    )
    mine = Team.objects.create(name="Team-X", created_by=creator)
    mine.members.add(regular_user)
    Team.objects.create(name="Team-Z", created_by=creator)
    resp = _client(regular_user).get("/api/v1/teams/mine/")
    names = {t["name"] for t in resp.json()}
    assert names == {"Team-X"}


@pytest.mark.django_db
def test_teams_mine_does_not_relax_full_list(regular_user):
    resp = _client(regular_user).get("/api/v1/teams/")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_owner_assigns_network_to_member_team(regular_user, campus_type):
    creator = User.objects.create_user(
        username="creator", password="secret", role=User.ROLE_POWER_USER
    )
    team = Team.objects.create(name="Team-X", created_by=creator)
    team.members.add(regular_user)
    net = _make_network("Net-A", regular_user, campus_type)
    resp = _client(regular_user).patch(
        f"/api/v1/networks/{net.id}/", {"team": team.id}, format="json"
    )
    assert resp.status_code == 200
    net.refresh_from_db()
    assert net.team_id == team.id


@pytest.mark.django_db
def test_owner_cannot_assign_to_nonmember_team(regular_user, campus_type):
    creator = User.objects.create_user(
        username="creator", password="secret", role=User.ROLE_POWER_USER
    )
    team = Team.objects.create(name="Team-Y", created_by=creator)
    net = _make_network("Net-A", regular_user, campus_type)
    resp = _client(regular_user).patch(
        f"/api/v1/networks/{net.id}/", {"team": team.id}, format="json"
    )
    assert resp.status_code == 400
    net.refresh_from_db()
    assert net.team_id is None


@pytest.mark.django_db
def test_power_user_assigns_any_network_to_any_team(power_user, campus_type):
    bob = User.objects.create_user(username="bob", password="secret")
    team = Team.objects.create(name="Team-Z", created_by=power_user)
    net = _make_network("Net-C", bob, campus_type)
    resp = _client(power_user).patch(
        f"/api/v1/networks/{net.id}/", {"team": team.id}, format="json"
    )
    assert resp.status_code == 200
    net.refresh_from_db()
    assert net.team_id == team.id


@pytest.mark.django_db
def test_owner_can_unassign_team(regular_user, campus_type):
    creator = User.objects.create_user(
        username="creator", password="secret", role=User.ROLE_POWER_USER
    )
    team = Team.objects.create(name="Team-X", created_by=creator)
    team.members.add(regular_user)
    net = _make_network("Net-A", regular_user, campus_type, team=team)
    resp = _client(regular_user).patch(
        f"/api/v1/networks/{net.id}/", {"team": None}, format="json"
    )
    assert resp.status_code == 200
    net.refresh_from_db()
    assert net.team_id is None
