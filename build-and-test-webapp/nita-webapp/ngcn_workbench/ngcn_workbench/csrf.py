# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Custom CSRF middleware for NITA.

NITA is a private lab tool that may be accessed through arbitrary hosts,
IP addresses, or port-forwarding tunnels (e.g. VS Code remote, kubectl
port-forward, or SSH tunnels).  Django 4.0+ added a strict Origin/Referer
host check in addition to the CSRF token check.  That host check requires
every possible access URL to be listed in CSRF_TRUSTED_ORIGINS, which is
impractical for tunnel-based access.

This middleware keeps CSRF token validation (the cryptographic protection)
while skipping the Origin/Referer host check that is only relevant when the
webapp is reachable from the public internet.
"""

from django.middleware.csrf import CsrfViewMiddleware


class LabCsrfMiddleware(CsrfViewMiddleware):
    """CSRF middleware that validates the token but skips the host origin check."""

    def _check_referer(self, request):  # noqa: D401
        """Accept any Origin/Referer host; rely solely on the CSRF token."""
        return None
