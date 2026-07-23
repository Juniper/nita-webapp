# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Tests for SPA routing after the re-root to ``/``.

The React SPA is the default application served at ``/`` and owns its own
client-side routes. Removed legacy server-rendered paths must return HTTP 404
(never the SPA shell), and backend routes (``/api/**``, ``/admin/**``) must not
be swallowed by the SPA. The ``SPA_ROUTES`` list mirrors the top-level routes in
``frontend/src/App.tsx`` and the allowlist in ``ngcn_workbench/urls.py`` — if the
two drift apart these tests fail.
"""

import pytest
from django.urls import Resolver404, resolve

from ngcn_workbench.urls import spa_index

# Top-level SPA routes — keep in sync with frontend/src/App.tsx and the
# allowlist regex in ngcn_workbench/urls.py.
SPA_ROUTES = ["/", "/login", "/network-types", "/networks", "/networks/5"]

# Paths that used to be served by the deleted legacy server-rendered UI.
REMOVED_LEGACY_ROUTES = [
    "/campustype/",
    "/campusnetwork/",
    "/tree_pane/",
    "/campus_network/5/summary/",
]


@pytest.mark.parametrize("path", SPA_ROUTES)
def test_spa_routes_resolve_to_spa_view(path):
    """Each known SPA route resolves to the SPA index view."""
    assert resolve(path).func is spa_index


@pytest.mark.parametrize("path", REMOVED_LEGACY_ROUTES)
def test_removed_legacy_paths_do_not_resolve(path):
    """Removed legacy paths match no URL pattern (not even the SPA allowlist)."""
    with pytest.raises(Resolver404):
        resolve(path)


@pytest.mark.parametrize("path", ["/api/v1/network-types/", "/admin/"])
def test_backend_routes_not_swallowed_by_spa(path):
    """Backend routes take precedence over the SPA and never resolve to it."""
    assert resolve(path).func is not spa_index


@pytest.mark.parametrize("path", SPA_ROUTES)
def test_spa_routes_serve_index_html(client, settings, tmp_path, path):
    """Each SPA route serves the built index.html with a 200 (drift guard)."""
    (tmp_path / "index.html").write_text("<!doctype html><title>spa</title>")
    settings.WHITENOISE_ROOT = str(tmp_path)

    response = client.get(path)

    assert response.status_code == 200
    assert response["Content-Type"] == "text/html"


@pytest.mark.parametrize("path", REMOVED_LEGACY_ROUTES)
def test_removed_legacy_paths_return_404(client, path):
    """Removed legacy paths return HTTP 404, not the SPA shell."""
    assert client.get(path).status_code == 404
