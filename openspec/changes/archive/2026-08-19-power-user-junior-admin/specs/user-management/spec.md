## MODIFIED Requirements

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

## ADDED Requirements

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
