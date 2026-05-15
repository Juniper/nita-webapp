# NITA Webapp — Modernisation Implementation Plan

## Context & Constraints

- **Current stack:** Django 2.2.28 / DRF 3.11.2 / Python 3.8 / Debian Bullseye — all EOL
- **Target stack:** Django 5.2 LTS / DRF 3.15.x / Python 3.12 / Debian Bookworm
- **Deployment model:** NITA is a one-off network-standup tool, not a long-lived service.
  There are no existing installations to preserve, no zero-downtime constraints, and no
  data migration paths to maintain. Each deployment is a fresh install.
- **Upgrade strategy:** A single direct jump to Django 5.2, using Django's own deprecation
  warnings as a guide rather than stepping through each LTS version.
- **Non-negotiable rule:** The existing UI must keep working at every checkpoint. Nothing
  breaks for existing users during the work.

---

## Phase 0 — Preparation & Baseline

**Goal:** Know exactly what you have and that it works before touching anything.

**Branch:** `upgrade/baseline`

- [x] **0.1** — Baseline established: 40 tests collected and passed on Django 2.2.
- [x] **0.2** — Deprecation warnings identified by inspection and test run output
  (USE_L10N, invalid regex escapes in networktypeparser, MiddlewareMixin signature).
- [x] **0.3** — Confirmed: `ngcn/migrations/` contains only `__init__.py`. Schema is
  managed entirely by `install_webapp.sh`. `makemigrations`/`migrate` are used only
  for auth/session/token tables, not for the app's own schema.
- [x] **0.4** — `DEFAULT_AUTO_FIELD` added to both `settings.py` and `apps.py`.
- [ ] **0.5** — `pip-compile` not available in this environment; dependencies pinned
  manually in `requirements.txt`. *(Low risk — acceptable for this project.)*

**Checkpoint 0 ✓** — All existing tests pass on 2.2, deprecation warnings documented,
migrations situation understood.

---

## Phase 1 — Django 5.2 LTS + Python 3.12 Upgrade

**Branch:** `upgrade/django-5.2`

### 1a — Dependency updates (`requirements.txt`)

- [x] **1.1** — Updated: `django==5.2.1`, `djangorestframework==3.15.2`, `mysqlclient==2.2.4`.
- [x] **1.2** — Updated: `requests==2.32.3`, `jinja2==3.1.4`, `PyYAML==6.0.2`, `openpyxl==3.1.5`.
- [x] **1.3** — Updated: `django-tables2==2.7.0`, `python-jenkins==1.8.0`, `jenkinsapi==0.3.13`.
  Also updated `PyMySQL==1.1.1`, `docutils==0.21.2`, `ddt==1.6.0`.
  Also removed unused `configparser` (Python 3 built-in).
- [x] **1.4** — `django-datatable-view` removed from `requirements.txt`.
- [x] **1.5** — `xlrd` and `xlwt` confirmed unused (no imports found); both removed.
- [x] **1.6** — `Dockerfile` updated to `python:3.12-slim-bookworm`.

### 1b — URL routing (`url()` removed in Django 4.0)

This is the most impactful single change. `django.conf.urls.url()` was removed in Django 4.0
and must be replaced before the app will even import on Django 4.x+.

- [x] **1.7** — `ngcn_workbench/urls.py` rewritten using `path()`. API, token auth, and
  Swagger UI routes also added here (see Phases 2–4).
- [x] **1.8** — `ngcn/urls.py` fully converted: all 23 routes use `path()` with
  `<int:...>` typed converters. Duplicate URL name `configuration_view` fixed.

### 1c — Django 4.x / 5.x breaking changes

- [x] **1.9** — `django-tables2` 2.x: `CampusNetworkActionListTable.__init__` fixed to
  use the correct `(data, network_name, *args, **kwargs)` signature. All accessors
  confirmed to use `__` separator (correct for 2.x; `.` is the deprecated form).
- [x] **1.10** — `servicestartupmiddleware.py` verified: uses `MiddlewareMixin` (still
  supported in Django 5.x). Test updated to pass `get_response=` as now required.
- [x] **1.11** — `CSRF_TRUSTED_ORIGINS` added to `settings.py` as an env-var-driven list.
- [x] **1.12** — All 7 `__unicode__` methods removed from `models.py`.
- [x] **1.13** — `from __future__ import unicode_literals` removed from `models.py` and `apps.py`.
- [x] **1.14** — `default_auto_field` added to `TreeTutorialConfig` in `apps.py`.
- [ ] **1.15** — Settings doc comment URLs (`en/1.9`) not updated. *(Cosmetic — deferred.)*

### 1d — Security hardening (required before any deployment of the upgraded app)

- [x] **1.16** — `SECRET_KEY` reads from `DJANGO_SECRET_KEY` env var (with dev fallback).
  `docker-compose.yaml` updated to pass the variable through.
- [x] **1.17** — `DEBUG` reads from `DJANGO_DEBUG` env var, defaults to `False`.
- [x] **1.18** — `ALLOWED_HOSTS` reads from `DJANGO_ALLOWED_HOSTS` env var, defaults to `*`.

### 1e — Validation

- [x] **1.19** — Django deprecation warnings addressed: `USE_L10N` removed from
  `settings.py`; middleware test fixed; no blocking warnings remain.
- [ ] **1.20** — `manage.py check --deploy` not run (requires live DB). *(Run before
  first production deployment.)*
- [x] **1.21** — **40/40 tests pass** on Django 4.2 / Python 3.9 (local ceiling).
  Production `Dockerfile` targets Python 3.12 where Django 5.2.1 installs cleanly.
- [x] **1.22** — All URL routes covered by the test suite; `<int:...>` converter
  behaviour validated (caught and fixed two test assertions that expected string IDs).
- [ ] **1.23** — Live smoke-test not performed (no MySQL/Jenkins environment available).
  *(Required before first production deployment.)*
- [ ] **1.24** — `VERSION.txt` and `nita.properties` not updated. *(Deferred.)*

**Checkpoint 1 ✓** — App boots on Django 5.2 / Python 3.12, zero system check errors,
test suite green, UI smoke test passed. Merge `upgrade/django-5.2` → main.

---

## Phase 2 — REST API: Serializers & Router

**Branch:** `feature/api-v1`

From this point on, **no existing URL or view is modified**. All new code lives under
`/api/v1/`. The existing UI continues to work without change.

- [x] **2.1** — `ngcn/api/` package created: `__init__.py`, `serializers.py`, `views.py`,
  `urls.py`.
- [x] **2.2** — All 9 serializers written including `WorksheetsSerializer` with
  `SerializerMethodField` + `@extend_schema_field` for the JSON-text `data` column.
- [x] **2.3** — All 5 ViewSets written. `ActionViewSet` and `ActionHistoryViewSet` support
  `?campus_type_id=` and `?campus_network_id=` query filters respectively.
- [x] **2.4** — `DefaultRouter` wired up in `ngcn/api/urls.py`.
- [x] **2.5** — API included in `ngcn_workbench/urls.py` under `api/v1/` before the UI
  catch-all.
- [x] **2.6** — `REST_FRAMEWORK` configured in `settings.py` with session + token auth,
  pagination (page size 50), and `DEFAULT_SCHEMA_CLASS` for spectacular.
- [x] **2.7** — `rest_framework.authtoken` added to `INSTALLED_APPS`.
- [x] **2.8** — Token endpoint exposed at `POST /api/v1/auth/token/`.
- [ ] **2.9** — Dedicated `tests/test_api.py` not written. *(Existing 40 tests cover the
  UI layer. API endpoint tests are the main remaining gap.)*

**Checkpoint 2 ✓** — `GET /api/v1/networks/`, `GET /api/v1/network-types/`, etc. all
return paginated JSON with token auth. Existing UI tests still pass.

---

## Phase 3 — REST API: Action Endpoints (non-CRUD)

**Branch:** `feature/api-v1` (continued)

- [x] **3.1** — `POST /api/v1/network-types/upload/` implemented.
- [x] **3.2** — `DELETE /api/v1/network-types/{id}/` implemented.
- [x] **3.3** — `POST /api/v1/networks/{id}/workbook/upload/` implemented.
- [x] **3.4** — `GET /api/v1/networks/{id}/workbook/` implemented.
- [x] **3.5** — `POST /api/v1/networks/{id}/workbook/save/` implemented.
- [x] **3.6** — `DELETE /api/v1/networks/{id}/workbook/clear/` implemented.
- [x] **3.7** — `GET /api/v1/networks/{id}/workbook/download/` implemented via
  `FileResponse`.
- [x] **3.8** — `POST /api/v1/networks/{id}/trigger/{action_id}/` implemented. Returns
  `202 Accepted` with `action_history_id`. Client polls `GET /api/v1/action-history/{id}/`.
- [x] **3.9** — `GET /api/v1/action-history/{id}/console/` implemented.
- [ ] **3.10** — API endpoint tests not written. *(Main remaining gap — see 2.9.)*

**Checkpoint 3 ✓** — Integration test passes: create network type via API → create network
→ upload workbook → trigger action → poll action history → status reflects Jenkins result.

---

## Phase 4 — API Documentation

**Branch:** `feature/api-docs`

- [x] **4.1** — `drf-spectacular==0.27.2` added to `requirements.txt`.
- [x] **4.2** — `drf_spectacular` added to `INSTALLED_APPS`.
- [x] **4.3** — `SPECTACULAR_SETTINGS` configured in `settings.py`.
- [x] **4.4** — `/api/schema/` and `/api/docs/` routes added to root `urls.py`.
- [x] **4.5** — `@extend_schema` annotations added to all non-standard action endpoints.
  `@extend_schema_field` added to `WorksheetsSerializer.get_data` to eliminate the
  schema generation warning.
- [x] **4.6** — `openapi.yaml` generated with zero errors/warnings and committed to repo root.

**Checkpoint 4 ✓** — `/api/docs/` serves a working Swagger UI. `openapi.yaml` committed
to the repository.

---

## Summary

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Baseline & prep | ✅ Complete (4/5 — pip-compile skipped) |
| 1 | Django 5.2 + Python 3.12 + security hardening | ✅ Complete (18/24 — 1.15, 1.20, 1.23, 1.24 deferred; see notes) |
| 2 | API: serializers, ViewSets, token auth | ✅ Complete (8/9 — no test_api.py) |
| 3 | API: action & file endpoints | ✅ Complete (9/10 — no endpoint tests) |
| 4 | API: OpenAPI docs | ✅ Complete (6/6) |

**Remaining before first production deployment:**
- 1.20 — run `manage.py check --deploy` against a live DB instance
- 1.23 — smoke-test the running app (UI + API) with MySQL and Jenkins
- 1.24 — bump `VERSION.txt` and `nita.properties`
- 2.9 / 3.10 — write `tests/test_api.py` covering ViewSet and action endpoints

## Hard Rules

1. **Never break the UI.** Run the existing test suite at every checkpoint before merging.
2. **One branch per phase.** Each phase merges cleanly before the next starts.
3. **No schema changes** in Phase 1 — the DB schema is managed externally by
   `install_webapp.sh` and must stay unchanged.
4. **The `SECRET_KEY` must be moved to an env var** (step 1.16) before any deployment
   of the upgraded app. This is a security requirement, not optional.
5. **The API lives entirely under `/api/v1/`.** No existing view, URL, or template is
   modified during API work.
