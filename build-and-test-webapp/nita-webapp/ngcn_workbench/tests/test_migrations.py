# Copyright (c) Hewlett Packard Enterprise, 2026. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Migration-integrity tests.

The main test suite runs with ``MIGRATION_MODULES = {"ngcn": None}`` (see
``ngcn_workbench.test_settings``), which builds the schema directly from the
models and therefore never exercises the real migration graph. That gap let a
migration-ordering bug ship undetected: the custom ``User`` model is created in
``ngcn.0005``, but Django resolves the swappable ``AUTH_USER_MODEL`` dependency
to the app's *first* migration, so migrations that FK the user model
(``admin.LogEntry``, ``authtoken.Token``) could be applied before ``ngcn.User``
existed, failing with ``Related model 'ngcn.user' cannot be resolved``. The fix
is a ``run_before`` on ``ngcn.0005``.

These tests run the actual migration graph (via a subprocess using
``ngcn_workbench.migration_test_settings``, which keeps migrations enabled on
SQLite) so that any regression in migration ordering or completeness is caught.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

# tests/ -> ngcn_workbench/ (where manage.py lives)
_WORKBENCH_DIR = Path(__file__).parent.parent
_SETTINGS = "ngcn_workbench.migration_test_settings"


def _run_manage(*args: str) -> subprocess.CompletedProcess:
    """Run ``manage.py`` with migrations enabled on SQLite."""
    return subprocess.run(
        [sys.executable, "manage.py", *args],
        cwd=str(_WORKBENCH_DIR),
        capture_output=True,
        text=True,
        env={**os.environ, "DJANGO_SETTINGS_MODULE": _SETTINGS},
    )


def test_all_migrations_apply_cleanly():
    """The full migration graph applies end-to-end without errors."""
    result = _run_manage("migrate", "--skip-checks", "--noinput")
    combined = result.stdout + result.stderr
    assert result.returncode == 0, combined
    assert "cannot be resolved" not in combined, combined
    assert "Traceback" not in combined, combined


def test_custom_user_migration_ordered_before_dependents():
    """``ngcn.0005`` (creates ``User``) must precede migrations that FK the user.

    ``admin.0001_initial`` (LogEntry) and ``authtoken.0001_initial`` (Token)
    both reference ``AUTH_USER_MODEL`` and must be applied *after* the custom
    user model is created. This is what the ``run_before`` on ``ngcn.0005``
    guarantees.
    """
    result = _run_manage("migrate", "--plan", "--skip-checks")
    assert result.returncode == 0, result.stdout + result.stderr
    plan = result.stdout

    idx_user = plan.find("ngcn.0005_user_team")
    idx_admin = plan.find("admin.0001_initial")
    idx_token = plan.find("authtoken.0001_initial")

    assert idx_user != -1, f"ngcn.0005 not in plan:\n{plan}"
    assert idx_admin != -1 and idx_user < idx_admin, (
        f"ngcn.0005 must come before admin.0001:\n{plan}"
    )
    assert idx_token != -1 and idx_user < idx_token, (
        f"ngcn.0005 must come before authtoken.0001:\n{plan}"
    )
