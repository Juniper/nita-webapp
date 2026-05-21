# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Tests for ?action_category_id= filter on ActionViewSet and ActionHistoryViewSet."""

import pytest
from django.utils import timezone
from ngcn.models import Action, ActionHistory, ActionProperty
from rest_framework.test import APIClient

# ── Shared fixture ─────────────────────────────────────────────────────────────


@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def build_action(db, campus_type, build_action_category):
    """An Action belonging to the BUILD category."""
    prop = ActionProperty.objects.create(
        shell_command="echo build",
        output_path="/tmp/build",
        custom_workspace="",
    )
    return Action.objects.create(
        action_name="run_build",
        jenkins_url="job-build",
        action_category=build_action_category,
        campus_type_id=campus_type,
        action_property=prop,
    )


@pytest.fixture
def test_action_history(db, action, campus_network):
    """An ActionHistory entry belonging to the TEST category."""
    return ActionHistory.objects.create(
        action_id=action,
        timestamp=timezone.now(),
        status="Done",
        jenkins_job_build_no=1,
        category_id=action.action_category,
        campus_network_id=campus_network,
    )


@pytest.fixture
def build_action_history(db, build_action, campus_network):
    """An ActionHistory entry belonging to the BUILD category."""
    return ActionHistory.objects.create(
        action_id=build_action,
        timestamp=timezone.now(),
        status="Done",
        jenkins_job_build_no=2,
        category_id=build_action.action_category,
        campus_network_id=campus_network,
    )


# ── ActionCategoryFilterTests ──────────────────────────────────────────────────


@pytest.mark.django_db
def test_filter_actions_by_category(api_client, action, build_action, action_category):
    """?action_category_id= returns only actions in that category."""
    response = api_client.get(
        f"/api/v1/actions/?action_category_id={action_category.id}"
    )
    assert response.status_code == 200
    ids = [r["id"] for r in response.json()["results"]]
    assert action.id in ids
    assert build_action.id not in ids


@pytest.mark.django_db
def test_filter_actions_combined(
    api_client, action, build_action, campus_type, action_category
):
    """?campus_type_id= combined with ?action_category_id= returns intersection."""
    response = api_client.get(
        f"/api/v1/actions/?campus_type_id={campus_type.id}"
        f"&action_category_id={action_category.id}"
    )
    assert response.status_code == 200
    ids = [r["id"] for r in response.json()["results"]]
    assert action.id in ids
    assert build_action.id not in ids


@pytest.mark.django_db
def test_filter_actions_no_params_returns_all(api_client, action, build_action):
    """No filter parameters returns all actions."""
    response = api_client.get("/api/v1/actions/")
    assert response.status_code == 200
    ids = [r["id"] for r in response.json()["results"]]
    assert action.id in ids
    assert build_action.id in ids


# ── ActionHistoryCategoryFilterTests ──────────────────────────────────────────


@pytest.mark.django_db
def test_filter_history_by_category(
    api_client,
    test_action_history,
    build_action_history,
    action_category,
):
    """?action_category_id= returns only history entries in that category."""
    response = api_client.get(
        f"/api/v1/action-history/?action_category_id={action_category.id}"
    )
    assert response.status_code == 200
    ids = [r["id"] for r in response.json()["results"]]
    assert test_action_history.id in ids
    assert build_action_history.id not in ids


@pytest.mark.django_db
def test_filter_history_combined(
    api_client,
    test_action_history,
    build_action_history,
    campus_network,
    action_category,
):
    """?campus_network_id= combined with ?action_category_id= returns intersection."""
    response = api_client.get(
        f"/api/v1/action-history/?campus_network_id={campus_network.id}"
        f"&action_category_id={action_category.id}"
    )
    assert response.status_code == 200
    ids = [r["id"] for r in response.json()["results"]]
    assert test_action_history.id in ids
    assert build_action_history.id not in ids


@pytest.mark.django_db
def test_filter_history_no_params_returns_all(
    api_client, test_action_history, build_action_history
):
    """No filter parameters returns all history entries."""
    response = api_client.get("/api/v1/action-history/")
    assert response.status_code == 200
    ids = [r["id"] for r in response.json()["results"]]
    assert test_action_history.id in ids
    assert build_action_history.id in ids
