## Context

The NITA Webapp already exposes a DRF REST API at `/api/v1/`. A full SPA rewrite will consume this API exclusively, so completeness and accuracy of the API contract are prerequisites for all subsequent frontend work.

An audit of the current Django template views against `/api/v1/` endpoints found two genuine filtering gaps and one process gap:

1. **`?action_category_id=` on `GET /api/v1/actions/`** — the `actionsView` template filters the Action queryset by `action_category_id` but the DRF `ActionViewSet` only supports `?campus_type_id=`. The SPA will need both filters simultaneously.
2. **`?action_category_id=` on `GET /api/v1/action-history/`** — the `actionHistoryDetailView` template filters ActionHistory by both `campus_network_id` and `action_category_id`; the `ActionHistoryViewSet` only supports `?campus_network_id=`.
3. **OpenAPI drift** — `openapi.yaml` is currently generated manually and can silently fall out of sync with the implementation. There is no CI check asserting they match.

### Dropped item: dedicated summary endpoint

The initial proposal mentioned adding `GET /api/v1/networks/{id}/summary/`. Investigation of `summary.html` shows it already assembles all displayed data from two existing endpoints (`GET /api/v1/networks/{id}/` for name/type/status/description and `GET /api/v1/actions/?campus_type_id=…` for the action table). No new endpoint is needed.

## Goals / Non-Goals

**Goals:**
- `?action_category_id=` query parameter accepted by both `ActionViewSet` and `ActionHistoryViewSet` (combinable with existing filters).
- `openapi.yaml` regenerated to include the new parameters.
- A pytest test (`tests/test_api_schema.py`) that shells out to `manage.py spectacular --file -` and diffs against the committed `openapi.yaml`, failing on any deviation.

**Non-Goals:**
- SSE / streaming console (→ `api-v1-streaming`)
- Session/CSRF auth endpoints for SPA (→ `api-v1-csrf-and-session`)
- Any frontend code
- Summary endpoint (not needed — data already available via existing endpoints)

## Decisions

### Decision: `get_queryset` pattern, not `django-filters`

**Options considered:**
- A) Hand-written `get_queryset` override (current pattern in the codebase for `campus_type_id` filter)
- B) Introduce `django-filter` + `DjangoFilterBackend`

**Choice: A**

Rationale: The existing codebase uses hand-written `get_queryset` overrides consistently. Introducing `django-filter` for two new query parameters would add a dependency and diverge from the established pattern without material benefit. An AI implementer copying the pattern in the file is lower risk than being asked to integrate a new library.

### Decision: Drift test uses `manage.py spectacular` output, not schema parsing

**Options considered:**
- A) Parse `openapi.yaml` and check specific keys
- B) Shell out to `manage.py spectacular --file -`, write to a temp file, diff against committed `openapi.yaml`

**Choice: B**

Rationale: Option B catches every class of drift (missing endpoints, changed schemas, new parameters) with no maintenance. It is the same command used to regenerate the file, so there is no ambiguity. The test only needs to be added once and then passively guards the contract forever.

### Decision: `openapi.yaml` regenerated and committed in this change

The drift test needs a baseline. The committed `openapi.yaml` should reflect the new parameters before the test is added, otherwise the test fails immediately on the CI baseline. The implementer MUST regenerate `openapi.yaml` as part of this change.

## Risks / Trade-offs

- **Drift test is strict** — any formatting difference between `drf-spectacular`'s output and the committed file will fail the test, not just semantic differences. Mitigation: the test must strip or normalise any timestamp/version fields that `drf-spectacular` injects before comparing.
- **`page_size=1000` pattern in summary.html** — the current template requests up to 1000 actions to populate the summary pane, bypassing pagination. This is a code smell but is not addressed in this change (out of scope). The SPA can later address this with proper pagination.
- **No rollback concern** — all changes are additive (new query params, new test). No data migration needed.

## Decisions — DO NOT REVISIT

(For AI implementers: these decisions are final for this change.)
- Do not introduce `django-filter` or any new pip dependency.
- Do not add a `/summary/` endpoint to networks.
- Do not modify any template views.
- Follow the existing `get_queryset` pattern exactly as it appears for `campus_type_id` in `ActionViewSet`.
- After adding the view changes, regenerate `openapi.yaml` via `manage.py spectacular --file openapi.yaml` before writing the drift test.
