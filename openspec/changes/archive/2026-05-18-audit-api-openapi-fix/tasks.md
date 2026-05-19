## 1. Add Missing Upload Endpoint

- [x] 1.1 Add `POST /api/v1/network-types/upload/` path entry to `openapi.yaml`
  under the `paths` section (after `/api/v1/network-types/{id}/`)
- [x] 1.2 Define the request body as `multipart/form-data` with a single binary
  field `app_zip_file`
- [x] 1.3 Define the 200 response schema as an inline object with `result`
  (string, required), `name` (string, optional), and `id` (integer, optional)
- [x] 1.4 Define the 400 response schema as an inline object with `result`
  (string) and `reason` (string)
- [x] 1.5 Apply standard `cookieAuth` / `tokenAuth` security to the new endpoint

## 2. Fix Workbook Download Response

- [x] 2.1 Locate `GET /api/v1/networks/{id}/workbook/download/` in `openapi.yaml`
- [x] 2.2 Replace the `application/json` content block (which incorrectly
  references `CampusNetwork`) with an
  `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` block
- [x] 2.3 Set the response schema to `type: string, format: binary`

## 3. Remove Spurious Trigger Request Body

- [x] 3.1 Locate `POST /api/v1/networks/{id}/trigger/{action_id}/` in
  `openapi.yaml`
- [x] 3.2 Remove the `requestBody` block (which incorrectly references
  `CampusNetwork`)
- [x] 3.3 Verify the path parameters (`id` and `action_id`) remain intact

## 4. Fix `action_id` Path Parameter Type

- [x] 4.1 In the trigger endpoint's `parameters`, change `action_id` from
  `type: string` (with pattern) to `type: integer`
- [x] 4.2 Add a description consistent with other ID parameters (e.g.
  "A unique integer value identifying the action to trigger.")

## 5. Add Missing Filter Query Parameters

- [x] 5.1 Add `campus_type_id` (integer, optional) query parameter to
  `GET /api/v1/networks/`
- [x] 5.2 Add `campus_type_id` (integer, optional) query parameter to
  `GET /api/v1/actions/`
- [x] 5.3 Add `campus_network_id` (integer, optional) query parameter to
  `GET /api/v1/action-history/`
- [x] 5.4 Add `name` (string, optional) query parameter to
  `GET /api/v1/network-types/`

## 6. Fix Auth Token Endpoint Security

- [x] 6.1 Locate `POST /api/v1/auth/token/` in `openapi.yaml`
- [x] 6.2 Add `security: []` to override the global default and mark the
  endpoint as unauthenticated

## 7. Fix Workbook Endpoint Response Schemas

- [x] 7.1 Locate `GET /api/v1/networks/{id}/workbook/` in `openapi.yaml`
- [x] 7.2 Replace the `Workbook` schema reference with an inline object schema:
  `status` (string) and `workbook` (array of objects, each with `name` (string)
  and `data` (oneOf object/array/string))
- [x] 7.3 Locate `POST /api/v1/networks/{id}/workbook/upload/` in `openapi.yaml`
- [x] 7.4 Apply the same inline response schema correction as step 7.2

## 8. Verify and Review

- [x] 8.1 Validate the updated `openapi.yaml` is well-formed YAML (e.g. with
  `python -c "import yaml; yaml.safe_load(open('openapi.yaml'))"`)
- [x] 8.2 Confirm all `$ref` targets in the updated file still resolve (no
  dangling references)
- [x] 8.3 Load `GET /api/docs/` in a browser and confirm all seven corrected
  endpoints render correctly in the Swagger UI
