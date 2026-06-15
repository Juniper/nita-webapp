## Why

Before any SPA frontend work begins, every piece of behaviour the new UI will need must be reachable through `/api/v1/` and faithfully documented in `openapi.yaml`. An audit of the current REST surface against the existing Django template views reveals a small number of gaps that, if left in place, would force the SPA to either call template URLs (entangling it with HTML rendering) or hand-roll endpoints later under time pressure. Closing these gaps now — and adding a CI assertion that the OpenAPI schema cannot silently drift — gives the generated TypeScript API client a stable, complete contract to be built against.

## What Changes

- Extend `GET /api/v1/actions/` with an optional `?action_category_id=<id>` query parameter (combinable with the existing `?campus_type_id=`), matching the filter the `actionsView` template applies.
- Extend `GET /api/v1/action-history/` with an optional `?action_category_id=<id>` query parameter (combinable with the existing `?campus_network_id=`), matching the filter the `actionHistoryDetailView` template applies.
- Regenerate `openapi.yaml` from the live DRF schema so the new endpoints and parameters are reflected verbatim.
- Add an automated check (pytest + CI step) that fails when the committed `openapi.yaml` differs from a freshly generated schema, locking the contract.

### Out of scope (handled by later changes)

- Server-Sent Events / streaming console output (→ `api-v1-streaming`).
- Login / logout / `me` endpoints and CSRF documentation for browser SPA usage (→ `api-v1-csrf-and-session`).
- Removing the Django template views and their URLs (→ `remove-django-template-ui`, Phase 3).
- Any frontend code.

## Capabilities

### New Capabilities
_None._

### Modified Capabilities
- `actions`: add a `?action_category_id=` filter requirement on the list endpoints for actions and action-history.
- `api`: add a CI-enforced OpenAPI drift assertion requirement that fails the build when `openapi.yaml` no longer matches the live DRF schema.

## Impact

- **Code**: `ngcn/api/views.py` (expanded `get_queryset` on `ActionViewSet` and `ActionHistoryViewSet`); no serializer changes needed.
- **Schema**: `openapi.yaml` regenerated; committed.
- **Tests**: new DRF tests under `ngcn/tests/` covering the three endpoint changes, plus a single OpenAPI-drift test that shells out to `manage.py spectacular --file -` and compares with the committed file.
- **CI**: existing pytest run will now fail on schema drift; no new pipeline job needed.
- **Dependencies**: none added. `drf-spectacular` is already in use.
- **Template UI**: unchanged — the legacy Django templates continue to function exactly as before, since the API additions are purely additive.
