# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os

from django.conf import settings
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from drf_spectacular.openapi import AutoSchema
from rest_framework.authtoken.views import ObtainAuthToken


class TokenAuthSchema(AutoSchema):
    def get_operation(self, path, path_regex, path_prefix, method, registry):
        operation = super().get_operation(
            path, path_regex, path_prefix, method, registry
        )
        operation["security"] = []
        return operation


class TokenAuthView(ObtainAuthToken):
    schema = TokenAuthSchema()

    pass


def spa_index(request, **kwargs):
    """Serve the compiled React SPA for all /app/* routes."""
    index_path = os.path.join(
        getattr(settings, "WHITENOISE_ROOT", ""),
        "index.html",
    )
    if not os.path.isfile(index_path):
        return HttpResponse(
            "SPA not built. Run: cd frontend && npm run build",
            status=503,
            content_type="text/plain",
        )
    with open(index_path, "rb") as f:
        return HttpResponse(f.read(), content_type="text/html")


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("ngcn.api.urls")),
    path("api/v1/auth/token/", TokenAuthView.as_view(), name="api-token-auth"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # React SPA — served at /app/ with React Router basename="/app"
    path("app/", spa_index, name="spa"),
    re_path(r"^app/.*$", spa_index),
    path("", include("ngcn.urls")),
]
