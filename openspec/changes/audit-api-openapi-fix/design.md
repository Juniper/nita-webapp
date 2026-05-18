## Context

The `openapi.yaml` at the workspace root is the canonical OpenAPI 3.0 contract
for the NITA Webapp REST API. It is served live at `GET /api/schema/` and powers
both the Swagger UI at `GET /api/docs/` and any generated client SDKs.

An audit of the file against the Django/DRF implementation
(`ngcn/api/views.py`, `ngcn/api/serializers.py`) identified seven concrete
discrepancies. The existing spec files in `openspec/specs/` accurately describe
the intended behaviour; the mismatches are all in `openapi.yaml`.

## Goals / Non-Goals

**Goals:**
- Correct `openapi.yaml` so that every documented endpoint accurately reflects
  the live implementation (request shapes, response schemas, security, query
  parameters).
- Keep changes minimal and scoped to `openapi.yaml` only.

**Non-Goals:**
- Changing Django view logic, serializers, models, or URL configuration.
- Regenerating `openapi.yaml` from scratch via `drf-spectacular`; targeted manual
  patches are preferred to avoid re-introducing annotation gaps.
- Modifying existing `spec.md` files (they are already correct).

## Decisions

### Decision 1 — Manual patch vs. schema regeneration

**Choice**: Patch `openapi.yaml` manually.

**Rationale**: Re-running `drf-spectacular` would overwrite the entire file and
risk re-introducing the same errors (the `@extend_schema` annotations are
incomplete — e.g., workbook views use the wrong response serializer class). A
targeted diff is safer, reviewable, and doesn't require a running database.

**Alternative considered**: Update `@extend_schema` annotations first, then
regenerate. Rejected because it would widen the scope of change to application
source code and require a live environment to run the generator.

---

### Decision 2 — Workbook response schema: inline vs. named component

**Choice**: Define inline schemas for the workbook envelope responses.

**Rationale**: The `{"workbook": [...], "status": "..."}` envelope is specific to
two endpoints and would add noise to `components/schemas` if extracted. The
existing `Workbook` schema (a model-backed object with `id`, `name`, etc.) is
conceptually different from the ad-hoc response envelope, so re-using it is
incorrect. Inline schemas are the least invasive fix.

---

### Decision 3 — Auth token endpoint security

**Choice**: Set `security: []` on `POST /api/v1/auth/token/`.

**Rationale**: The endpoint accepts credentials in the request body (form-encoded
`username`/`password`). Requiring `cookieAuth` or `tokenAuth` is circular —
the caller does not yet have a token or session. The OpenAPI convention for
"no authentication required" is an explicit empty security array overriding the
global default.

**Alternative considered**: Add a `basicAuth` security scheme. Rejected because
DRF's `ObtainAuthToken` view accepts credentials in the body, not in the HTTP
`Authorization` header.

---

### Decision 4 — `action_id` path parameter type

**Choice**: Change from `type: string` (with pattern) to `type: integer`.

**Rationale**: All other ID path parameters use `type: integer`. The trigger
endpoint uses `action_id` as a database primary key (`Action.objects.get(pk=action_id)`).
Documenting it as a string is inconsistent and misleads client generators into
serialising it as a string rather than an integer.

---

### Decision 5 — Upload endpoint response schema

**Choice**: Document the upload response as an object with `result` (string),
`name` (string, optional), and `id` (integer, optional).

**Rationale**: `NetworkTypeParser.parseProjectFile` returns `{"result": "success",
"name": ct.name, "id": ct.id}` on the happy path and `{"result": "failure",
"reason": ...}` on errors. `name` and `id` are absent in the fallback branch
(`CampusType.DoesNotExist`), so they are optional. This matches the existing
`@extend_schema` annotation in `CampusTypeViewSet.upload` (which already lists
`result` and `name`), extended with `id`.

## Risks / Trade-offs

- **Swagger UI behavioural change** → The corrected schema will change what the
  Swagger UI renders (e.g., the trigger endpoint will no longer show a request
  body editor). This is intentional and the correct behaviour; no mitigation
  needed.

- **Existing generated clients** → Any clients generated from the old, incorrect
  schema will need to be regenerated. This is unavoidable and desirable.
  Mitigation: document in release notes.

- **`openapi.yaml` drift risk** → The file is not auto-generated on every build,
  so future view changes could silently introduce new drift. Mitigation (out of
  scope for this change): consider adding a CI step that regenerates and diffs the
  schema.
