# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""OpenAPI schema drift test.

Fails when the committed openapi.yaml at the repo root no longer matches
the schema generated live by `manage.py spectacular`.  Run after any change
to DRF viewsets, serializers, or @extend_schema decorators.

To fix a failure:
    cd build-and-test-webapp/nita-webapp/ngcn_workbench
    DJANGO_SETTINGS_MODULE=ngcn_workbench.test_settings \\
        python3 manage.py spectacular --file ../../../../../../../openapi.yaml
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

# Locate key paths relative to this file.
# tests/ -> ngcn_workbench/ (manage.py lives here)
_WORKBENCH_DIR = Path(__file__).parent.parent
# ngcn_workbench/ -> nita-webapp/ -> build-and-test-webapp/ -> repo root
_REPO_ROOT = _WORKBENCH_DIR.parent.parent.parent
_COMMITTED_SCHEMA = _REPO_ROOT / "openapi.yaml"


def _strip_volatile(schema: dict) -> dict:
    """Remove fields that may legitimately differ between runs.

    - ``info.version`` — bumped independently of the API shape.
    - Integer ``format`` / ``minimum`` / ``maximum`` — Python 3.9 + SQLite
      omits these constraints; Python 3.12 + SQLite emits them.  Neither
      difference affects runtime behaviour, so we normalise them away.
    """
    info = schema.get("info", {})
    info.pop("version", None)
    _strip_integer_constraints(schema)
    return schema


def _strip_integer_constraints(node: object) -> None:
    """Recursively remove format/min/max from integer-typed schema nodes."""
    if isinstance(node, dict):
        if node.get("type") == "integer":
            node.pop("format", None)
            node.pop("minimum", None)
            node.pop("maximum", None)
        for value in node.values():
            _strip_integer_constraints(value)
    elif isinstance(node, list):
        for item in node:
            _strip_integer_constraints(item)


@pytest.mark.django_db
def test_openapi_schema_matches_committed():
    """Committed openapi.yaml must match the live DRF-generated schema."""
    assert (
        _COMMITTED_SCHEMA.exists()
    ), f"Committed schema not found: {_COMMITTED_SCHEMA}"

    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp:
        tmp_path = tmp.name

    result = subprocess.run(
        [sys.executable, "manage.py", "spectacular", "--file", tmp_path],
        cwd=str(_WORKBENCH_DIR),
        capture_output=True,
        text=True,
        env={
            **__import__("os").environ,
            "DJANGO_SETTINGS_MODULE": "ngcn_workbench.test_settings",
        },
    )
    assert result.returncode == 0, f"manage.py spectacular failed:\n{result.stderr}"

    live = _strip_volatile(yaml.safe_load(Path(tmp_path).read_text()))
    committed = _strip_volatile(yaml.safe_load(_COMMITTED_SCHEMA.read_text()))

    assert live == committed, (
        "openapi.yaml is out of sync with the implementation.\n"
        "To fix, run from build-and-test-webapp/nita-webapp/ngcn_workbench/:\n"
        "  DJANGO_SETTINGS_MODULE=ngcn_workbench.test_settings "
        "python3 manage.py spectacular --file " + str(_COMMITTED_SCHEMA)
    )
