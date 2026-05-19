# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

from django.contrib import admin
from django.urls import include, path
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
    path("", include("ngcn.urls")),
]
