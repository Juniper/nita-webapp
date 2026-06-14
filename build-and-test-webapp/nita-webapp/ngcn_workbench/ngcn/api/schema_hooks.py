# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""drf-spectacular post-processing hooks for the generated OpenAPI schema."""

# Upper bound on the number of entries the lifecycle-runs list can return:
# ``LifecycleRunViewSet._MAX_BUILDS`` (50) inspected per lifecycle kind, across
# the three kinds (network_create, network_delete, network_type_load).
_LIFECYCLE_RUNS_MAX_ITEMS = 150


def bound_array_lengths(result, generator, request, public):
    """Add ``maxItems`` to bounded array schemas.

    The lifecycle-runs list response is capped server-side, so advertise that
    bound in the schema. This also satisfies linters (e.g. checkov
    ``CKV_OPENAPI_21``) that require arrays to declare a maximum length.
    """

    def walk(node):
        if isinstance(node, dict):
            items = node.get("items")
            if (
                node.get("type") == "array"
                and "maxItems" not in node
                and isinstance(items, dict)
                and str(items.get("$ref", "")).endswith("/LifecycleRun")
            ):
                node["maxItems"] = _LIFECYCLE_RUNS_MAX_ITEMS
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(result)
    return result
