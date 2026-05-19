# API Specification

## Purpose
General cross-cutting concerns for the NITA Webapp REST API — versioning,
pagination, content types, and the Swagger/Redoc documentation endpoints.
## Requirements
### Requirement: API Versioning
All REST endpoints SHALL be served under the `/api/v1/` prefix.

#### Scenario: Correct URL prefix
- GIVEN any API endpoint call
- WHEN the URL is inspected
- THEN it begins with /api/v1/

### Requirement: Pagination
All list endpoints SHALL return a paginated envelope containing `count`, `next`,
`previous`, and `results`. The default page size SHALL be 50.

#### Scenario: Paginated envelope present
- GIVEN any list endpoint (e.g. GET /api/v1/networks/)
- WHEN a 200 response is received
- THEN the body contains count, next, previous, and results fields

#### Scenario: Page parameter
- GIVEN more than 50 resources exist
- WHEN GET /api/v1/networks/?page=2 is called
- THEN the second page of results is returned

### Requirement: JSON Content Type
All API responses SHALL use `application/json` content type except for binary
downloads.

#### Scenario: JSON response
- GIVEN any non-download API call
- WHEN the response is received
- THEN Content-Type is application/json

### Requirement: OpenAPI Schema Endpoint
The system SHALL serve the live OpenAPI 3.0 schema at GET /api/schema/.

#### Scenario: Schema endpoint returns YAML
- GIVEN NITA is running
- WHEN GET /api/schema/ is called with a valid token
- THEN a 200 response is returned containing a valid OpenAPI 3.0 YAML document

### Requirement: Swagger UI
The system SHALL serve an interactive Swagger UI at GET /api/docs/.

#### Scenario: Swagger UI loads
- GIVEN NITA is running
- WHEN a browser navigates to /api/docs/
- THEN the Swagger UI is rendered with all API endpoints listed

### Requirement: HTTPS Enforcement
The nginx proxy SHALL terminate TLS and forward all HTTP traffic to the webapp
on port 8000. The proxy SHALL listen on port 443 for HTTPS and port 8000
within the cluster.

#### Scenario: HTTPS access
- GIVEN the proxy pod is running with a valid certificate
- WHEN a client connects to the host on port 443
- THEN the connection is served over TLS

### Requirement: OpenAPI Schema Accuracy
The `openapi.yaml` file SHALL accurately reflect all implemented API endpoints,
including their HTTP methods, path parameters, query parameters, request body
schemas, response schemas, and security requirements.

#### Scenario: All implemented endpoints are documented
- **WHEN** the `openapi.yaml` is compared to the registered DRF viewsets
- **THEN** every endpoint (including custom actions) has a corresponding path
  entry in `openapi.yaml`

#### Scenario: Response schemas match actual response bodies
- **WHEN** an API endpoint returns a response
- **THEN** the response body structure matches the schema documented in
  `openapi.yaml` for that endpoint and status code

#### Scenario: Request body schemas match actual consumed fields
- **WHEN** an API endpoint's `openapi.yaml` entry documents a request body
- **THEN** the documented request body schema reflects fields the endpoint
  actually reads from the request

#### Scenario: Filter query parameters are documented
- **WHEN** an endpoint supports `?<param>=<value>` query-string filtering
- **THEN** that parameter is listed under the endpoint's `parameters` in
  `openapi.yaml`

#### Scenario: Unauthenticated endpoints use empty security override
- **WHEN** an endpoint does not require authentication (e.g. the token issuance
  endpoint where credentials are in the request body)
- **THEN** the endpoint declares `security: []` in `openapi.yaml` to override
  the global default

