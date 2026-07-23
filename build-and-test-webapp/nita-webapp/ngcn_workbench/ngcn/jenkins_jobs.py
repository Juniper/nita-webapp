# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Shared helpers for invoking Jenkins jobs and streaming their console output.

This module centralises the authenticated (CSRF-crumbed) Jenkins build
invocation and the Server-Sent-Events console stream generator so that the
per-network action trigger, network create, network delete, and network-type
load flows all behave consistently instead of duplicating crumb/auth logic.

All imports of project modules and the Jenkins client libraries are performed
lazily inside the functions to avoid import-time cycles and to keep the Django
startup path clean.
"""

import logging
import re
import time
import urllib.error
import urllib.request

from django.http import StreamingHttpResponse

logger = logging.getLogger(__name__)

# Matches ANSI colour / control escape sequences emitted by Jenkins console.
_ANSI_ESCAPE = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")


def robot_summary(job_name, build_no):
    """Return normalized Robot Framework result totals for a build, or ``None``.

    Relays the Jenkins Robot Framework plugin's per-build summary
    (``/job/{job}/{build}/robot/api/json``). Returns a dict with ``total``,
    ``passed``, ``failed``, ``skipped`` and ``pass_percentage`` keys, or ``None``
    when the build has no Robot results or Jenkins is unreachable.
    """
    import base64
    import json

    from ngcn.jenkins_config import (
        JENKINS_SERVER_PASS,
        JENKINS_SERVER_URL,
        JENKINS_SERVER_USER,
    )

    url = f"{JENKINS_SERVER_URL}/job/{job_name}/{build_no}/robot/api/json"
    req = urllib.request.Request(url)
    token = base64.b64encode(
        f"{JENKINS_SERVER_USER}:{JENKINS_SERVER_PASS}".encode()
    ).decode()
    req.add_header("Authorization", "Basic " + token)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return None

    if not isinstance(data, dict) or "overallTotal" not in data:
        return None

    total = data.get("overallTotal", 0) or 0
    passed = data.get("overallPassed", 0) or 0
    failed = data.get("overallFailed", 0) or 0
    skipped = data.get("overallSkipped", 0) or 0
    pass_percentage = data.get("passPercentage")
    if pass_percentage is None:
        pass_percentage = round((passed / total) * 100, 1) if total else 0.0
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "pass_percentage": pass_percentage,
    }


def _make_crumbed_jenkins():
    """Return a jenkinsapi ``Jenkins`` client configured with a CSRF crumb."""
    from jenkinsapi.jenkins import Jenkins
    from jenkinsapi.utils.crumb_requester import CrumbRequester

    from ngcn.jenkins_config import (
        JENKINS_SERVER_PASS,
        JENKINS_SERVER_URL,
        JENKINS_SERVER_USER,
    )

    crumb = CrumbRequester(
        baseurl=JENKINS_SERVER_URL,
        username=JENKINS_SERVER_USER,
        password=JENKINS_SERVER_PASS,
    )
    return Jenkins(
        JENKINS_SERVER_URL,
        username=JENKINS_SERVER_USER,
        password=JENKINS_SERVER_PASS,
        requester=crumb,
    )


def invoke_job(job_name, build_params=None, files=None):
    """Invoke a Jenkins job with an authenticated crumb and return its build no.

    Reserves the job's ``nextBuildNumber`` (the number the started build will
    use), performs the authenticated invocation, retries once on a ``Forbidden``
    crumb error, and re-raises on any other error (e.g. Jenkins unreachable) so
    that callers can translate it into a ``503`` response.

    :param job_name: the Jenkins job name to invoke.
    :param build_params: optional dict of build parameters.
    :param files: optional dict of files to upload (e.g. ``{"app.zip": fh}``).
    :returns: the reserved build number for this invocation.
    """
    from ngcn.jenkins_config import _make_jenkins_server

    server = _make_jenkins_server()
    build_number = server.get_job_info(job_name)["nextBuildNumber"]

    def _do_invoke():
        kwargs = {}
        if build_params is not None:
            kwargs["build_params"] = build_params
        if files is not None:
            kwargs["files"] = files
        _make_crumbed_jenkins().get_job(job_name).invoke(**kwargs)

    try:
        _do_invoke()
    except Exception as exc:  # most likely a Jenkins crumb (Forbidden) issue
        if "Forbidden" in str(exc):
            logger.warning("Jenkins crumb rejected for %s; retrying once", job_name)
            _do_invoke()
        else:
            raise
    return build_number


def progressive_text_events(job_name, build_no):
    """Yield SSE events streaming a Jenkins build's progressive console text.

    Polls the Jenkins ``progressiveText`` API and yields ``data: <line>`` events
    for each output line, then one of:
    - ``event: done\\ndata: \\n\\n``    — build finished normally
    - ``event: error\\ndata: <msg>\\n\\n`` — Jenkins unreachable / exception
    - ``event: timeout\\ndata: \\n\\n``  — 30-minute cap reached

    ANSI escape codes are stripped from emitted output. The initial window
    during which the build is still queued (Jenkins returns ``404``) is
    tolerated for up to ``max_queued_polls`` attempts.
    """
    from ngcn.jenkins_config import JENKINS_SERVER_URL

    base_url = f"{JENKINS_SERVER_URL}/job/{job_name}/{build_no}/logText/progressiveText"
    offset = 0
    max_polls = 1800  # 30 minutes at 1-second intervals
    # How many consecutive 404s to tolerate before giving up. Jenkins keeps the
    # build in queue for a few seconds before the executor picks it up; during
    # that window progressiveText returns 404.
    max_queued_polls = 60
    queued_polls = 0

    for _ in range(max_polls):
        try:
            url = f"{base_url}?start={offset}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
                chunk = resp.read().decode("utf-8", errors="replace")
                more_data = resp.headers.get("X-More-Data", "false").lower() == "true"
                new_offset = resp.headers.get("X-Text-Size")
                if new_offset:
                    offset = int(new_offset)
            queued_polls = 0  # reset once build is reachable
        except urllib.error.HTTPError as exc:
            if exc.code == 404 and queued_polls < max_queued_polls:
                # Build is still queued / executor not yet started — wait, retry.
                queued_polls += 1
                time.sleep(1)
                continue
            yield f"event: error\ndata: {exc}\n\n"
            return
        except Exception as exc:
            yield f"event: error\ndata: {exc}\n\n"
            return

        cleaned = _ANSI_ESCAPE.sub("", chunk)
        for line in cleaned.splitlines():
            if line:
                yield f"data: {line}\n\n"

        if not more_data:
            yield "event: done\ndata: \n\n"
            return

        time.sleep(1)

    yield "event: timeout\ndata: \n\n"


def stream_response(job_name, build_no):
    """Return a ``StreamingHttpResponse`` of a job's console as SSE.

    Sets the headers required for real-time SSE delivery through the nginx
    reverse proxy (``X-Accel-Buffering: no``) and to prevent caching.
    """
    response = StreamingHttpResponse(
        progressive_text_events(job_name, build_no),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
