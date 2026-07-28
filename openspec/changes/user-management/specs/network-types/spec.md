## MODIFIED Requirements

### Requirement: List Network Types
The system SHALL return a paginated list of all registered network types via
GET /api/v1/network-types/ to any authenticated user regardless of role.

#### Scenario: List returns all types
- **GIVEN** one or more network types are registered
- **WHEN** GET /api/v1/network-types/ is called with a valid session or token
- **THEN** a 200 response with `count` and `results` fields is returned
- **AND** no item in `results` contains `roles` or `resources` fields

#### Scenario: Filter by name
- **GIVEN** a network type named `evpn_vxlan_erb_dc_1.3` is registered
- **WHEN** GET /api/v1/network-types/?name=evpn_vxlan_erb_dc_1.3 is called
- **THEN** only that network type appears in results

### Requirement: Retrieve a Network Type
The system SHALL return the full detail of a single network type via
GET /api/v1/network-types/{id}/ to any authenticated user regardless of role.

#### Scenario: Retrieve by id
- **GIVEN** a network type with a known id
- **WHEN** GET /api/v1/network-types/{id}/ is called
- **THEN** a 200 response with `name` and `description` fields is returned

## ADDED Requirements

### Requirement: Network Type Create/Update/Delete Restricted to Power User and Admin
The system SHALL restrict `POST`, `PATCH`, `PUT`, and `DELETE` on
`/api/v1/network-types/` and `/api/v1/network-types/{id}/` to users with
`role=power_user` or `role=admin`. A regular `user` SHALL receive 403 on any
mutating request.

#### Scenario: Power user creates a network type
- **GIVEN** a user with `role=power_user`
- **WHEN** `POST /api/v1/network-types/` is called with valid data
- **THEN** a 201 response is returned and `created_by` is set to the requesting user

#### Scenario: Regular user cannot create a network type
- **GIVEN** a user with `role=user`
- **WHEN** `POST /api/v1/network-types/` is called
- **THEN** a 403 response is returned

#### Scenario: Only creator or admin can update a network type
- **GIVEN** power_user Alice created network type `"evpn_template"` and power_user Bob exists
- **WHEN** Bob calls `PATCH /api/v1/network-types/{id}/`
- **THEN** a 403 response is returned

#### Scenario: Creator can update their own network type
- **GIVEN** power_user Alice created network type `"evpn_template"`
- **WHEN** Alice calls `PATCH /api/v1/network-types/{id}/` with updated data
- **THEN** a 200 response is returned

#### Scenario: Admin can update any network type
- **GIVEN** a user with `role=admin`
- **WHEN** `PATCH /api/v1/network-types/{id}/` is called for any type
- **THEN** a 200 response is returned
