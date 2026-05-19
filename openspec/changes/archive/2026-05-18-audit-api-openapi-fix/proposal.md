## Why

The `openapi.yaml` contract document contains several errors that contradict both
the live Django/DRF implementation and the existing spec files: a whole endpoint
is missing, response schemas are wrong, a request body is fabricated, filter
query parameters are undocumented, and the token endpoint incorrectly requires
authentication. These errors cause generated client SDKs to produce incorrect
code, the Swagger UI to mislead API consumers, and client developers to work
from inaccurate documentation.

## What Changes

- **Add missing endpoint**: `POST /api/v1/network-types/upload/` is implemented
  in `CampusTypeViewSet.upload` and documented in the network-types spec, but is
  entirely absent from `openapi.yaml`.
- **Fix workbook download response type**: `GET /api/v1/networks/{id}/workbook/download/`
  documents an `application/json` `CampusNetwork` response but the view returns a
  `FileResponse` with content type
  `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.
- **Remove spurious trigger request body**: `POST /api/v1/networks/{id}/trigger/{action_id}/`
  documents a required `CampusNetwork` request body that the implementation never
  reads. The request body entry shall be removed.
- **Add missing filter query parameters**: Four endpoints support query-string
  filtering in the implementation but the parameters are absent from `openapi.yaml`:
  - `GET /api/v1/networks/` — `?campus_type_id=`
  - `GET /api/v1/actions/` — `?campus_type_id=`
  - `GET /api/v1/action-history/` — `?campus_network_id=`
  - `GET /api/v1/network-types/` — `?name=`
- **Fix auth token endpoint security**: `POST /api/v1/auth/token/` documents
  `cookieAuth` and `tokenAuth` as required security schemes, but this is the
  endpoint used to *obtain* a token — credentials are in the request body. It
  shall use `security: []`.
- **Fix workbook endpoint response schemas**: Both `GET …/workbook/` and
  `POST …/workbook/upload/` return `{"workbook": [...], "status": "..."}` but
  `openapi.yaml` declares a `Workbook` model schema for both. The inline
  response schemas shall be corrected to match the actual response envelope.
- **Fix `action_id` path parameter type**: In the trigger endpoint, `action_id`
  is documented as `type: string`; it shall be `type: integer` for consistency
  with all other ID path parameters.

No changes are made to Django source code, models, serializers, or views — all
fixes are confined to `openapi.yaml`.

## Capabilities

### New Capabilities
<!-- None — no new endpoints or features are being introduced -->

### Modified Capabilities
- `api`: Add a requirement that the `openapi.yaml` file SHALL accurately reflect
  all implemented endpoints, their request/response schemas, security requirements,
  and all supported query parameters.

## Impact

- `openapi.yaml` — primary file being corrected (all seven issues above)
- Swagger UI at `GET /api/docs/` will display accurate documentation after the fix
- Any generated client using `GET /api/schema/` will produce correct code
- No Django source files, migrations, or existing `spec.md` files require changes
