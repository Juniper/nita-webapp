# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Custom DRF authentication for NITA.

DRF's SessionAuthentication.enforce_csrf() hard-codes CsrfViewMiddleware for
its internal CSRF check, bypassing the project's LabCsrfMiddleware (which
accepts any Origin/Referer and relies solely on the CSRF token).  This means
requests from kubectl port-forward / SSH tunnel URLs are rejected with 403 even
when a valid CSRF token is present.

LabSessionAuthentication overrides enforce_csrf() to use LabCsrfMiddleware so
that the same relaxed-origin policy applied by the Django middleware stack is
also applied to DRF session-based API requests.
"""

from rest_framework.authentication import SessionAuthentication
from rest_framework import exceptions

from ngcn_workbench.csrf import LabCsrfMiddleware


class _LabCSRFCheck(LabCsrfMiddleware):
    """Thin wrapper that makes LabCsrfMiddleware usable as a CSRF checker."""

    def _reject(self, request, reason):
        # Store the rejection reason so enforce_csrf() can retrieve it.
        return reason


class LabSessionAuthentication(SessionAuthentication):
    """SessionAuthentication that uses LabCsrfMiddleware for CSRF validation.

    Inherits all session/user resolution logic from SessionAuthentication;
    only the CSRF check is replaced so that Origin/Referer host verification
    is skipped for lab/tunnel access while the CSRF token itself is still
    validated.
    """

    def enforce_csrf(self, request):
        def dummy_get_response(request):  # pragma: no cover
            return None

        check = _LabCSRFCheck(dummy_get_response)
        # Populate request.META['CSRF_COOKIE'] from the incoming cookie.
        check.process_request(request)
        reason = check.process_view(request, None, (), {})
        if reason:
            raise exceptions.PermissionDenied("CSRF Failed: %s" % reason)
