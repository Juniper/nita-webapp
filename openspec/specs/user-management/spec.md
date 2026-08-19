# User Management Specification

## Purpose
Admin-only API for listing users, assigning roles, deactivating accounts, bulk
ownership transfer, and protected deletion.

## Requirements

### Requirement: List Users (Admin; Power User sees non-admins)
The system SHALL provide `GET /api/v1/users/` to `role=admin` (all users) and to
`role=power_user` (with `role=admin` accounts excluded — see "Power User Manages
Non-Admin Users"). A `role=user` SHALL receive `403`.
The response SHALL include `id`, `username`, `email`, `role`, and `is_active`
for each user.

#### Scenario: Admin retrieves user list
- GIVEN a user with `role=admin`
- WHEN `GET /api/v1/users/` is called
- THEN a 200 response is returned with a list of all users

#### Scenario: Regular user cannot list users
- GIVEN a user with `role=user`
- WHEN `GET /api/v1/users/` is called
- THEN a 403 response is returned

### Requirement: Update User Role and Status (Admin; Power User for non-admins)
The system SHALL provide `PATCH /api/v1/users/{id}/` for updating a user's `role`
and `is_active` fields. `role=admin` may update any user (subject to the
last-admin protection); `role=power_user` may update **non-admin** users only,
with role changes capped at `power_user` (see "Power User Manages Non-Admin
Users"). A `role=user` SHALL receive `403`.

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

### Requirement: Set User Password (Admin any user; Power User any non-admin)
The system SHALL provide `POST /api/v1/users/{id}/set_password/` accessible to
`role=admin` for any user, and to `role=power_user` for any target whose `role`
is **not** `admin`. The request body SHALL accept a write-only `password`
validated with the configured Django password validators. The endpoint SHALL set
the target user's password and MAY target the caller's own account (admin). The
password SHALL NOT appear in any response body or log output. A power user
targeting an `admin`, and any requester with `role=user`, SHALL receive `403`.

#### Scenario: Admin resets another user's password
- GIVEN a user with `role=admin` and a target user
- WHEN `POST /api/v1/users/{target_id}/set_password/` is called with a valid `password`
- THEN a 200 response is returned and the target user can authenticate with the
  new password
- AND the response body does not contain the password

#### Scenario: Power user resets any non-admin
- GIVEN a `power_user` and a target user with `role=user`
- WHEN the power user calls `POST /api/v1/users/{target_id}/set_password/` with a
  valid `password`
- THEN a 200 response is returned and the target can authenticate with the new password

#### Scenario: Power user cannot reset an admin
- GIVEN a `power_user` and a target user with `role=admin`
- WHEN the power user calls `POST /api/v1/users/{admin_id}/set_password/`
- THEN a 403 response is returned

#### Scenario: Weak password is rejected
- GIVEN an admin or a power user
- WHEN `POST /api/v1/users/{id}/set_password/` is called with a password failing
  the validators
- THEN a 400 response is returned

#### Scenario: Regular user cannot set passwords
- GIVEN a user with `role=user`
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

### Requirement: Power User Manages Non-Admin Users
A `power_user` acts as a junior administrator over **non-admin** accounts. The
system SHALL allow a `power_user` to:
- `GET /api/v1/users/` — list users, with `role=admin` accounts **excluded** from
  the results;
- `GET /api/v1/users/{id}/` — view any non-admin user (`id`, `username`, `email`,
  `role`, `is_active`);
- `PATCH /api/v1/users/{id}/` — change the `is_active` status and/or the `role` of
  any non-admin user, where a role change SHALL be capped at `power_user` (setting
  `role=admin` is rejected).

The system SHALL reject with `403` any attempt by a `power_user` to view or modify
an `admin` account, or to set a user's `role` to `admin`. Creating and deleting
user accounts SHALL remain restricted to `role=admin`, and the last-active-admin
protection SHALL remain in force.

#### Scenario: Power user lists non-admin users
- GIVEN a `power_user` and a mix of `user`, `power_user`, and `admin` accounts
- WHEN `GET /api/v1/users/` is called
- THEN a 200 response is returned whose results include the non-admin accounts and
  contain no `admin` accounts

#### Scenario: Power user changes a non-admin's role and status
- GIVEN a `power_user` and a target with `role=user`
- WHEN the power user PATCHes `{"role": "power_user"}` and then `{"is_active": false}`
- THEN both requests return 200 and the changes are applied

#### Scenario: Power user cannot grant the admin role
- GIVEN a `power_user` and a non-admin target
- WHEN the power user PATCHes `{"role": "admin"}`
- THEN a 403 response is returned and the target's role is unchanged

#### Scenario: Power user cannot view or modify an admin
- GIVEN a `power_user` and an `admin` target
- WHEN the power user calls `GET` or `PATCH` on `/api/v1/users/{admin_id}/`
- THEN a 403 response is returned

#### Scenario: Power user cannot create or delete accounts
- GIVEN a `power_user`
- WHEN `POST /api/v1/users/` or `DELETE /api/v1/users/{id}/` is called
- THEN a 403 response is returned

### Requirement: Audit Power-User Password Resets
The system SHALL record an audit-log entry whenever a `power_user` resets another
user's password, capturing at least the acting user's id, the target user's id,
and a timestamp. The password itself SHALL NOT appear in the log.

#### Scenario: Power-user reset is audited
- GIVEN a `power_user` who resets a non-admin user's password via
  `POST /api/v1/users/{id}/set_password/`
- WHEN the reset succeeds
- THEN an audit-log entry is recorded identifying the acting power user, the
  target user, and the time of the reset
- AND the log entry does not contain the password
