# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Tests for the SSE streaming endpoint GET /api/v1/action-history/{id}/stream/."""

import urllib.error
from unittest.mock import patch

import pytest
from django.utils import timezone
from ngcn.models import ActionHistory
from rest_framework.test import APIClient

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


# ── View-level tests ───────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_stream_yields_sse_events_and_done(api_client, action_history):
    """The stream endpoint returns text/event-stream with data and done events."""
    fake_events = [
        "data: line one\n\n",
        "data: line two\n\n",
        "event: done\ndata: \n\n",
    ]
    with patch(
        "ngcn.jenkins_jobs.progressive_text_events",
        return_value=iter(fake_events),
    ):
        response = api_client.get(
            f"/api/v1/action-history/{action_history.id}/stream/",
            HTTP_ACCEPT="text/event-stream",
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.get("Content-Type", "")

    body = b"".join(response.streaming_content)
    assert b"data: line one" in body
    assert b"data: line two" in body
    assert b"event: done" in body


@pytest.mark.django_db
def test_stream_requires_authentication(action_history):
    """Unauthenticated requests are rejected before streaming begins."""
    unauthenticated = APIClient()
    response = unauthenticated.get(
        f"/api/v1/action-history/{action_history.id}/stream/"
    )
    assert response.status_code in (401, 403)


# ── Generator unit tests ───────────────────────────────────────────────────────


def test_generator_emits_error_event_on_jenkins_failure():
    """Generator yields a single error event when urllib raises URLError."""
    from ngcn.jenkins_jobs import progressive_text_events

    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        events = list(progressive_text_events("job-test", 1))

    assert len(events) == 1
    assert events[0].startswith("event: error")


def test_generator_emits_done_when_no_more_data():
    """Generator yields data lines then done when X-More-Data is absent/false."""
    from unittest.mock import MagicMock

    from ngcn.jenkins_jobs import progressive_text_events

    fake_response = MagicMock()
    fake_response.read.return_value = b"build step one\nbuild step two\n"
    fake_response.headers.get.side_effect = lambda key, default=None: {
        "X-More-Data": "false",
        "X-Text-Size": "30",
    }.get(key, default)
    fake_response.__enter__ = lambda s: s
    fake_response.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=fake_response):
        events = list(progressive_text_events("job-test", 1))

    data_events = [e for e in events if e.startswith("data:")]
    done_events = [e for e in events if e.startswith("event: done")]
    assert len(data_events) == 2
    assert len(done_events) == 1
