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
