## ADDED Requirements

### Requirement: List Users (Admin Only)
The system SHALL provide `GET /api/v1/users/` accessible only to `role=admin`.
The response SHALL include `id`, `username`, `email`, `role`, and `is_active`
for each user.

#### Scenario: Admin retrieves user list
- **GIVEN** a user with `role=admin`
- **WHEN** `GET /api/v1/users/` is called
- **THEN** a 200 response is returned with a list of all users

#### Scenario: Non-admin cannot list users
- **GIVEN** a user with `role=user` or `role=power_user`
- **WHEN** `GET /api/v1/users/` is called
- **THEN** a 403 response is returned

### Requirement: Update User Role and Status (Admin Only)
The system SHALL provide `PATCH /api/v1/users/{id}/` accessible only to
`role=admin` for updating a user's `role` and `is_active` fields.

#### Scenario: Admin deactivates a user
- **GIVEN** a user with `role=admin`
- **WHEN** `PATCH /api/v1/users/{id}/` is called with `{"is_active": false}`
- **THEN** the target user is deactivated and a 200 response is returned

#### Scenario: Admin changes a user role to power_user
- **GIVEN** a user with `role=admin`
- **WHEN** `PATCH /api/v1/users/{id}/` is called with `{"role": "power_user"}`
- **THEN** the target user's role is updated to `power_user`

### Requirement: Bulk Ownership Transfer (Admin Only)
The system SHALL provide `POST /api/v1/users/{id}/transfer/` accessible only to
`role=admin`. The endpoint SHALL reassign all `CampusNetwork` rows owned by the
target user to a specified recipient user, and all `CampusType` rows created by
the target user to a specified recipient user.

#### Scenario: Admin transfers all resources before deletion
- **GIVEN** user Alice owns 3 networks and 2 types
- **WHEN** `POST /api/v1/users/{alice_id}/transfer/` is called with
  `{"networks_to": <bob_id>, "types_to": <bob_id>}`
- **THEN** all 3 networks have `owner=bob` and all 2 types have `created_by=bob`
- **AND** a 200 response is returned

#### Scenario: Transfer with invalid recipient returns 400
- **WHEN** `POST /api/v1/users/{id}/transfer/` is called with a non-existent `networks_to` user id
- **THEN** a 400 response is returned

### Requirement: Protected User Deletion (Admin Only)
The system SHALL provide `DELETE /api/v1/users/{id}/` accessible only to
`role=admin`. Deletion SHALL be blocked (409 Conflict) if the target user still
owns `CampusNetwork` or `CampusType` rows. The 409 response body SHALL list the
blocking resources.

#### Scenario: Delete user with no owned resources
- **GIVEN** a user who owns no networks and no types
- **WHEN** `DELETE /api/v1/users/{id}/` is called by an admin
- **THEN** the user is deleted and a 204 response is returned

#### Scenario: Delete blocked by owned networks
- **GIVEN** a user who owns at least one network
- **WHEN** `DELETE /api/v1/users/{id}/` is called by an admin
- **THEN** a 409 response is returned listing the owned networks

#### Scenario: Admin cannot delete themselves
- **GIVEN** a user with `role=admin`
- **WHEN** `DELETE /api/v1/users/{own_id}/` is called
- **THEN** a 400 response is returned
