## Why

The repository ships two webapps: the original server-rendered Django UI (the "legacy" app) served at the site root `/`, and the newer React single-page application (SPA) served under `/app/`. The SPA is now the intended interface, but the legacy UI still occupies the default URL, so users landing on `/` get the old app. Maintaining both doubles the surface area (templates, `django_tables2` tables, forms, jQuery/SlickGrid static assets, legacy views and their tests) and creates confusion about which UI is canonical.

This change makes the SPA the default application at `/`, and removes the legacy server-rendered UI and all references to it.

The work is not a simple deletion: the "legacy" `ngcn/views.py` (1258 lines) is a fusion of two concerns. Most of it is server-rendered HTTP views used only by the legacy `ngcn/urls.py`, but it also contains **shared business logic and Jenkins configuration constants** that the new SPA's API (`ngcn/api/views.py`) and `ngcn/jenkins_jobs.py` import at runtime (often via lazy, in-function imports). Those shared symbols must be extracted into neutral modules **before** the legacy code is deleted, or the SPA will break.

## What Changes

- **Re-root the SPA to `/`**: change React Router `basename` from `/app` to `/`, and update Django URL routing so `GET /` and client-side deep links resolve to the SPA `index.html`, while reserved backend prefixes (`api/`, `admin/`, `assets/`, `jenkins/`, `api/schema`, `api/docs`) still route to their handlers.
- **Extract shared logic out of `ngcn/views.py`** into neutral modules so the API and `jenkins_jobs` no longer depend on the legacy views module: `GridDataManager`, `create_new_inv`, `create_workbook`, `create_workbook_from_db`, `parse_workbook`, `updateCampusNetworkStatusOnDB`, `_make_jenkins_server`, `escape_ansi`, and the `JENKINS_SERVER_URL` / `JENKINS_SERVER_USER` / `JENKINS_SERVER_PASS` constants.
- **BREAKING**: Remove the legacy server-rendered UI entirely — `ngcn/urls.py` legacy routes, `ngcn/templates/ngcn/**`, `ngcn/tables.py`, `ngcn/forms.py`, the legacy-only static assets under `ngcn/static/**`, the legacy HTTP views in `ngcn/views.py`, and the legacy-only test suites (`tests/test_views_coverage.py`, `tests/test_views_integration.py`, and the legacy portions of `tests/test_supporting_units.py`). All URLs under `/` that previously served legacy pages (e.g. `/campustype/`, `/campusnetwork/`, `/campus_network/<id>/...`) cease to exist.
- **Drop the `django_tables2` dependency**: remove it from `requirements.txt` and from `INSTALLED_APPS` in `settings.py`.
- **Clean routing/proxy cruft**: remove the dead `rewrite ^/webapp(.*)$` rule from `nginx/nginx.conf`.
- **Regenerate license notices**: `NOTICES.txt` / `NOTICES.spdx.json` no longer list `django-tables2` or the legacy template files.

## Capabilities

### Modified Capabilities

- `django-spa-serve`: The SPA becomes the default application served at `/` (React Router `basename="/"`) instead of `/app/`. Django serves `index.html` for the root and all non-reserved client-side routes; reserved backend prefixes (`api/`, `admin/`, `assets/`, `jenkins/`) take precedence over the SPA catch-all. The legacy server-rendered template UI that previously occupied `/` is removed.

## Impact

- **Backend routing**: `ngcn_workbench/urls.py` — remove `path("", include("ngcn.urls"))`; replace `path("app/", spa_index)` + `re_path(r"^app/.*$")` with a root `spa_index` mount plus a negative-lookahead catch-all that excludes reserved prefixes.
- **Backend code**: new neutral modules (e.g. `ngcn/workbook.py`, `ngcn/jenkins_config.py`) holding the extracted shared symbols; `ngcn/api/views.py` and `ngcn/jenkins_jobs.py` updated to import from the new modules instead of `ngcn.views`.
- **Deleted**: `ngcn/urls.py` (legacy routes), `ngcn/templates/ngcn/**`, `templates/base.html` + `templates/base_site.html` (legacy chrome), `ngcn/tables.py`, `ngcn/forms.py`, legacy static assets under `ngcn/static/**`, legacy views in `ngcn/views.py`, `tests/test_views_coverage.py`, `tests/test_views_integration.py`, legacy portions of `tests/test_supporting_units.py`.
- **Frontend**: `frontend/src/App.tsx` — `<BrowserRouter basename="/app">` → `basename="/"`. API calls, asset URLs, and downloads are already root-relative and unaffected.
- **Dependencies / config**: `requirements.txt` (drop `django-tables2==2.7.0`), `settings.py` (drop `"django_tables2"` from `INSTALLED_APPS`), `pyproject.toml` (drop stale ruff `per-file-ignores` for `forms.py`/`views.py`).
- **nginx**: `nginx/nginx.conf` — remove the `rewrite ^/webapp(.*)$` rule.
- **Docs / generated**: `NOTICES.txt`, `NOTICES.spdx.json` regenerated via `merge_spdx.sh`; `IMPLEMENTATION_PLAN.md` and `openapi.yaml` references updated where they mention the legacy UI (low priority).
- **Existing spec modified**: `django-spa-serve`.
- **Breaking**: every legacy `/` URL is removed and now returns HTTP 404 (Django serves the SPA only for its own client routes). Any bookmark, script, or integration pointing at a legacy page path will 404. The SPA at `/` is the sole UI.
