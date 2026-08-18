# User Management Specification

## Purpose
Admin-only API for listing users, assigning roles, deactivating accounts, bulk
ownership transfer, and protected deletion.

## Requirements

### Requirement: List Users (Admin Only)
The system SHALL provide `GET /api/v1/users/` accessible only to `role=admin`.
The response SHALL include `id`, `username`, `email`, `role`, and `is_active`
for each user.

#### Scenario: Admin retrieves user list
- GIVEN a user with `role=admin`
- WHEN `GET /api/v1/users/` is called
- THEN a 200 response is returned with a list of all users

#### Scenario: Non-admin cannot list users
- GIVEN a user with `role=user` or `role=power_user`
- WHEN `GET /api/v1/users/` is called
- THEN a 403 response is returned

### Requirement: Update User Role and Status (Admin Only)
The system SHALL provide `PATCH /api/v1/users/{id}/` accessible only to
`role=admin` for updating a user's `role` and `is_active` fields.

#### Scenario: Admin deactivates a user
- GIVEN a user with `role=admin`
- WHEN `PATCH /api/v1/users/{id}/` is called with `{"is_active": false}`
- THEN the target user is deactivated and a 200 response is returned

#### Scenario: Admin changes a user role to power_user
- GIVEN a user with `role=admin`
- WHEN `PATCH /api/v1/users/{id}/` is called with `{"role": "power_user"}`
- THEN the target user's role is updated to `power_user`

### Requirement: Bulk Ownership Transfer (Admin Only)
The system SHALL provide `POST /api/v1/users/{id}/transfer/` accessible only to
`role=admin`. The endpoint SHALL reassign all `CampusNetwork` rows owned by the
target user to a specified recipient user, and all `CampusType` rows created by
the target user to a specified recipient user.

#### Scenario: Admin transfers all resources before deletion
- GIVEN user Alice owns 3 networks and 2 types
- WHEN `POST /api/v1/users/{alice_id}/transfer/` is called with
  `{"networks_to": <bob_id>, "types_to": <bob_id>}`
- THEN all 3 networks have `owner=bob` and all 2 types have `created_by=bob`
- AND a 200 response is returned

#### Scenario: Transfer with invalid recipient returns 400
- WHEN `POST /api/v1/users/{id}/transfer/` is called with a non-existent `networks_to` user id
- THEN a 400 response is returned

### Requirement: Protected User Deletion (Admin Only)
The system SHALL provide `DELETE /api/v1/users/{id}/` accessible only to
`role=admin`. Deletion SHALL be blocked (409 Conflict) if the target user still
owns `CampusNetwork` or `CampusType` rows. The 409 response body SHALL list the
blocking resources.

#### Scenario: Delete user with no owned resources
- GIVEN a user who owns no networks and no types
- WHEN `DELETE /api/v1/users/{id}/` is called by an admin
- THEN the user is deleted and a 204 response is returned

#### Scenario: Delete blocked by owned networks
- GIVEN a user who owns at least one network
- WHEN `DELETE /api/v1/users/{id}/` is called by an admin
- THEN a 409 response is returned listing the owned networks

#### Scenario: Admin cannot delete themselves
- GIVEN a user with `role=admin`
- WHEN `DELETE /api/v1/users/{own_id}/` is called
- THEN a 400 response is returned

### Requirement: Create User (Admin Only)
The system SHALL provide `POST /api/v1/users/` accessible only to `role=admin`
for creating a new user account. The request body SHALL accept `username`,
`email`, `role`, and `password`. The `password` SHALL be validated with the
configured Django password validators and stored write-only — it SHALL NOT
appear in any response body or log output. The response SHALL return the created
user's `id`, `username`, `email`, `role`, and `is_active`.

#### Scenario: Admin creates a power_user
- GIVEN a user with `role=admin`
- WHEN `POST /api/v1/users/` is called with
  `{"username": "carol", "email": "carol@example.com", "role": "power_user", "password": "<valid>"}`
- THEN a 201 response is returned with the new user's id, username, email,
  role=power_user, and is_active=true
- AND the response body does not contain the password

#### Scenario: Weak password is rejected
- GIVEN a user with `role=admin`
- WHEN `POST /api/v1/users/` is called with a password failing the validators
- THEN a 400 response is returned describing the password error

#### Scenario: Duplicate username is rejected
- GIVEN an existing user `carol`
- WHEN `POST /api/v1/users/` is called with `username=carol`
- THEN a 400 response is returned

#### Scenario: Non-admin cannot create users
- GIVEN a user with `role=user` or `role=power_user`
- WHEN `POST /api/v1/users/` is called
- THEN a 403 response is returned

### Requirement: Set User Password (Admin Only)
The system SHALL provide `POST /api/v1/users/{id}/set_password/` accessible only
to `role=admin`. The request body SHALL accept a write-only `password` validated
with the configured Django password validators. The endpoint SHALL set the
target user's password and MAY target the caller's own account. The password
SHALL NOT appear in any response body or log output.

#### Scenario: Admin resets another user's password
- GIVEN a user with `role=admin` and a target user
- WHEN `POST /api/v1/users/{target_id}/set_password/` is called with a valid `password`
- THEN a 200 response is returned and the target user can authenticate with the new password
- AND the response body does not contain the password

#### Scenario: Admin resets their own password
- GIVEN a user with `role=admin`
- WHEN `POST /api/v1/users/{own_id}/set_password/` is called with a valid `password`
- THEN a 200 response is returned and the password is updated

#### Scenario: Weak password is rejected
- GIVEN a user with `role=admin`
- WHEN `POST /api/v1/users/{id}/set_password/` is called with a password failing the validators
- THEN a 400 response is returned

#### Scenario: Non-admin cannot set passwords
- GIVEN a user with `role=user` or `role=power_user`
- WHEN `POST /api/v1/users/{id}/set_password/` is called
- THEN a 403 response is returned

### Requirement: Protect the Last Administrator
The system SHALL reject any operation that would leave zero active
administrators (an active administrator is a user with `role=admin` AND
`is_active=true`). This applies to changing the last active admin's role away
from `admin`, deactivating the last active admin, and deleting the last active
admin, and it applies regardless of whether the target is the caller or another
user. Rejected operations SHALL return a 400 response with a message naming the
reason.

#### Scenario: Cannot demote the last active admin
- GIVEN exactly one active admin exists
- WHEN `PATCH /api/v1/users/{that_admin_id}/` is called with `{"role": "power_user"}`
- THEN a 400 response is returned and the user remains an admin

#### Scenario: Cannot deactivate the last active admin
- GIVEN exactly one active admin exists
- WHEN `PATCH /api/v1/users/{that_admin_id}/` is called with `{"is_active": false}`
- THEN a 400 response is returned and the user remains active

#### Scenario: Cannot delete the last active admin
- GIVEN exactly one active admin exists
- WHEN `DELETE /api/v1/users/{that_admin_id}/` is called
- THEN a 400 response is returned and the user is not deleted

#### Scenario: Operation allowed when another active admin exists
- GIVEN two active admins exist
- WHEN one of them is demoted, deactivated, or deleted
- THEN the operation succeeds
