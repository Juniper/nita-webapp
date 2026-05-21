## MODIFIED Requirements

### Requirement: OpenAPI Schema Accuracy
The `openapi.yaml` file SHALL accurately reflect all implemented API endpoints,
including their HTTP methods, path parameters, query parameters, request body
schemas, response schemas, and security requirements.

A CI-enforced test SHALL fail when the committed `openapi.yaml` differs from the
schema generated live by `manage.py spectacular`, preventing silent drift.

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
- **WHEN** an endpoint does not require authentication
- **THEN** the endpoint declares `security: []` in `openapi.yaml` to override
  the global default

#### Scenario: Committed schema matches live schema
- **GIVEN** the committed `openapi.yaml` in the repository
- **WHEN** `manage.py spectacular --file -` is executed in the test environment
- **THEN** the output is identical to the committed file (excluding any generated
  timestamp or comment fields), and the pytest drift test exits 0
