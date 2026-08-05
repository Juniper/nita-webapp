# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""drf-spectacular post-processing hooks for the generated OpenAPI schema."""

# Upper bound on the number of entries the lifecycle-runs list can return:
# ``LifecycleRunViewSet._MAX_BUILDS`` (50) inspected per lifecycle kind, across
# the three kinds (network_create, network_delete, network_type_load).
_LIFECYCLE_RUNS_MAX_ITEMS = 150

# Generic upper bound for any other array so the schema never advertises an
# unbounded collection (satisfies checkov ``CKV_OPENAPI_21``).
_DEFAULT_MAX_ITEMS = 1000


def bound_array_lengths(result, generator, request, public):
    """Add ``maxItems`` to every array schema that lacks one.

    Lifecycle-run lists get their specific server-side cap; all other arrays get
    a generic upper bound so no array is advertised as unbounded (checkov
    ``CKV_OPENAPI_21``).
    """

    def walk(node):
        if isinstance(node, dict):
            items = node.get("items")
            if node.get("type") == "array" and "maxItems" not in node:
                if isinstance(items, dict) and str(items.get("$ref", "")).endswith(
                    "/LifecycleRun"
                ):
                    node["maxItems"] = _LIFECYCLE_RUNS_MAX_ITEMS
                else:
                    node["maxItems"] = _DEFAULT_MAX_ITEMS
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(result)
    return result


def add_global_security(result, generator, request, public):
    """Declare a document-level default security requirement (``tokenAuth``).

    Individual public endpoints still opt out with an empty ``security: []``.
    Satisfies checkov ``CKV_OPENAPI_4`` (global security field defined).
    """
    if not result.get("security"):
        result["security"] = [{"tokenAuth": []}]
    return result
