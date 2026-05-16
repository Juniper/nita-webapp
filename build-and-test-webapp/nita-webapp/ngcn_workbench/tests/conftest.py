# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""pytest fixtures shared across the entire NITA Webapp test suite."""

import re
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from ngcn.models import (
    Action,
    ActionCategory,
    ActionProperty,
    CampusNetwork,
    CampusType,
)
from playwright.sync_api import sync_playwright


@pytest.fixture
def user(db):
    model = get_user_model()
    return model.objects.create_user(username="tester", password="secret")


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def campus_type(db):
    return CampusType.objects.create(
        name="sample_type",
        description="Sample type",
        app_zip_name="sample.zip",
    )


@pytest.fixture
def action_category(db):
    return ActionCategory.objects.create(category_name="TEST")


@pytest.fixture
def build_action_category(db):
    return ActionCategory.objects.create(category_name="BUILD")


@pytest.fixture
def action(db, campus_type, action_category):
    prop = ActionProperty.objects.create(
        shell_command="echo ok",
        output_path="/tmp/out",
        custom_workspace="",
    )
    return Action.objects.create(
        action_name="run_test",
        jenkins_url="job-test",
        action_category=action_category,
        campus_type_id=campus_type,
        action_property=prop,
    )


@pytest.fixture
def campus_network(db, campus_type):
    return CampusNetwork.objects.create(
        name="campus_one",
        status="Initialized",
        description="Campus one",
        host_file="hosts data",
        campus_type=campus_type,
    )


# ── GUI screenshot infrastructure ─────────────────────────────────────────────


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Store the per-phase outcome on the node so fixtures can read pass/fail."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(scope="session")
def screenshot_dir():
    """Session-scoped directory that collects all GUI snapshots."""
    d = Path("ci-screenshots")
    d.mkdir(exist_ok=True)
    return d


@pytest.fixture
def _browser_page(live_server, user):
    """Playwright page pre-authenticated via a forged Django session cookie.

    pytest-django shares the in-memory SQLite connection with the live server
    thread, so a session created here with force_login is immediately visible
    to requests the browser makes against live_server.
    """
    from django.test import Client as DjangoClient

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context()

        dc = DjangoClient()
        dc.force_login(user)
        session_id = dc.cookies["sessionid"].value
        context.add_cookies(
            [{"name": "sessionid", "value": session_id, "url": live_server.url}]
        )

        page = context.new_page()
        yield page

        context.close()
        browser.close()


@pytest.fixture(autouse=True)
def _screenshot_on_pass(request, screenshot_dir):
    """After each *passing* @pytest.mark.screenshot test, save a GUI snapshot.

    The live server and browser page are set up BEFORE the test body runs so
    that pytest's reverse-teardown order guarantees they are still live when
    this fixture runs its teardown (the screenshot step).
    """
    marker = request.node.get_closest_marker("screenshot")
    if marker is not None:
        # Request live_server and _browser_page NOW (before yield) so they
        # remain active during teardown (pytest finalises in reverse-setup order).
        # Swallow errors so a missing browser binary never breaks the test.
        try:
            _live = request.getfixturevalue("live_server")
            _page = request.getfixturevalue("_browser_page")
        except Exception:
            _live = _page = None
    else:
        _live = _page = None

    yield

    if _page is None:
        return
    rep = getattr(request.node, "rep_call", None)
    if rep is None or not rep.passed:
        return

    url_template = marker.args[0]

    def _resolve(m):
        try:
            val = request.getfixturevalue(m.group(1))
            return str(getattr(val, "id", val))
        except Exception:
            return m.group(0)

    url = re.sub(r"\{(\w+)\}", _resolve, url_template)

    try:
        _page.goto(_live.url + url, wait_until="domcontentloaded", timeout=10_000)
        _page.wait_for_load_state("networkidle", timeout=5_000)
    except Exception:
        return

    safe = re.sub(r"[^\w]", "_", request.node.nodeid)
    _page.screenshot(path=str(screenshot_dir / f"{safe}.png"), full_page=True)
