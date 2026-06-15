## MODIFIED Requirements

### Requirement: CSRF-Aware API Client
The system SHALL provide `src/api/client.ts` that wraps the browser `fetch` API:
- For GET requests: forwards the request with `credentials: 'include'`.
- For POST/PUT/PATCH/DELETE requests: first calls `GET /api/v1/auth/csrf/` (cached after first call) to obtain the CSRF token, then attaches it as the `X-CSRFToken` request header alongside `credentials: 'include'`.
- The client SHALL default the `Content-Type` to `application/json` only when the request body is NOT a `FormData` instance and no `Content-Type` header has been supplied. For `FormData` bodies the client SHALL NOT set `Content-Type`, so the browser can supply the correct `multipart/form-data` boundary (forcing `application/json` causes the server to reject uploads with HTTP 415).

#### Scenario: GET request is sent without CSRF header
- GIVEN the API client is used to call a GET endpoint
- WHEN the request is made
- THEN no `X-CSRFToken` header is attached

#### Scenario: POST request includes CSRF token
- GIVEN the API client is used to call a POST endpoint
- WHEN the request is made
- THEN `X-CSRFToken` is present in the request headers with a non-empty value

#### Scenario: JSON body gets a JSON content type
- GIVEN the API client is used to POST a non-FormData body with no explicit Content-Type
- WHEN the request is made
- THEN the `Content-Type` header is set to `application/json`

#### Scenario: FormData upload preserves the multipart boundary
- GIVEN the API client is used to POST a `FormData` body
- WHEN the request is made
- THEN the client does NOT set a `Content-Type` header
- AND the browser sets `Content-Type: multipart/form-data` with a boundary
