## REMOVED Requirements

### Requirement: Nested Roles and Resources
**Reason**: The `Role` and `Resource` models were never populated — the code that would parse roles and resources from `project.yaml` was commented out before the feature shipped. The concept of roles and resources does not exist in NITA's architecture. The M2M join tables are always empty. Carrying dead fields in the API and UI creates maintenance burden and confusion.
**Migration**: No migration path needed. The `roles` and `resources` fields in `GET /api/v1/network-types/{id}/` are always empty arrays. Clients that read these fields will receive a 400 or simply find the fields absent; since the arrays are always `[]`, no functional behaviour changes.

## MODIFIED Requirements

### Requirement: Retrieve a Network Type
The system SHALL return the full detail of a single network type via
GET /api/v1/network-types/{id}/.

The response SHALL NOT include `roles` or `resources` fields.

#### Scenario: Retrieve by id
- GIVEN a network type with a known id
- WHEN GET /api/v1/network-types/{id}/ is called
- THEN a 200 response with `name` and `description` fields is returned
- AND the response body does NOT contain `roles` or `resources` fields

### Requirement: List Network Types
The system SHALL return a paginated list of all registered network types via
GET /api/v1/network-types/.

List items SHALL NOT include `roles` or `resources` fields.

#### Scenario: List returns all types
- GIVEN one or more network types are registered
- WHEN GET /api/v1/network-types/ is called with a valid token
- THEN a 200 response with `count` and `results` fields is returned
- AND no item in `results` contains `roles` or `resources` fields
