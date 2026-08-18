## MODIFIED Requirements

### Requirement: Set User Password (Admin, or Power User for Own Team Members)
The system SHALL provide `POST /api/v1/users/{id}/set_password/` accessible to
`role=admin` for any user, and to `role=power_user` **only** when the target user
has `role=user` and is a member of a team the requesting power user created. The
request body SHALL accept a write-only `password` validated with the configured
Django password validators. The endpoint SHALL set the target user's password and
MAY target the caller's own account (admin). The password SHALL NOT appear in any
response body or log output. Any request that does not satisfy the admin or the
scoped power-user condition SHALL return `403`.

#### Scenario: Admin resets another user's password
- GIVEN a user with `role=admin` and a target user
- WHEN `POST /api/v1/users/{target_id}/set_password/` is called with a valid `password`
- THEN a 200 response is returned and the target user can authenticate with the
  new password
- AND the response body does not contain the password

#### Scenario: Admin resets their own password
- GIVEN a user with `role=admin`
- WHEN `POST /api/v1/users/{own_id}/set_password/` is called with a valid `password`
- THEN a 200 response is returned and the password is updated

#### Scenario: Power user resets a member of their own team
- GIVEN a `power_user` who created `"Team-X"`, and a `role=user` member of `"Team-X"`
- WHEN the power user calls `POST /api/v1/users/{member_id}/set_password/` with a
  valid `password`
- THEN a 200 response is returned and the member can authenticate with the new password

#### Scenario: Power user cannot reset a non-member
- GIVEN a `power_user` and a `role=user` who is NOT a member of any team the power
  user created
- WHEN the power user calls `POST /api/v1/users/{user_id}/set_password/`
- THEN a 403 response is returned

#### Scenario: Power user cannot reset an elevated account
- GIVEN a `power_user` and a target member whose `role` is `power_user` or `admin`
  (even if that target is a member of the power user's team)
- WHEN the power user calls `POST /api/v1/users/{target_id}/set_password/`
- THEN a 403 response is returned

#### Scenario: Weak password is rejected
- GIVEN an admin or an authorised power user
- WHEN `POST /api/v1/users/{id}/set_password/` is called with a password failing
  the validators
- THEN a 400 response is returned

#### Scenario: Regular user cannot set passwords
- GIVEN a user with `role=user`
- WHEN `POST /api/v1/users/{id}/set_password/` is called
- THEN a 403 response is returned

## ADDED Requirements

### Requirement: Power User Views a Managed Team Member
The system SHALL allow a `power_user` to retrieve `GET /api/v1/users/{id}/` for a
target user that has `role=user` and is a member of a team the requesting power
user created, returning the standard user representation (`id`, `username`,
`email`, `role`, `is_active`). Admins retain full retrieve and list access. The
full `GET /api/v1/users/` list SHALL remain restricted to `role=admin`, and any
retrieve that does not satisfy the admin or scoped power-user condition SHALL
return `403`.

#### Scenario: Power user views a member they manage
- GIVEN a `power_user` who created `"Team-X"`, and a `role=user` member of `"Team-X"`
- WHEN the power user calls `GET /api/v1/users/{member_id}/`
- THEN a 200 response is returned with the member's `id`, `username`, `email`,
  `role`, and `is_active`

#### Scenario: Power user cannot view a non-member
- GIVEN a `power_user` and a `role=user` who is not a member of any team the power
  user created
- WHEN the power user calls `GET /api/v1/users/{user_id}/`
- THEN a 403 response is returned

#### Scenario: Power user cannot list all users
- GIVEN a `power_user`
- WHEN `GET /api/v1/users/` is called
- THEN a 403 response is returned

### Requirement: Audit Power-User Password Resets
Because the team-membership scope on power-user password reset is intentionally
soft (a power user can add any `role=user` to a team they created), the system
SHALL record an audit-log entry whenever a `power_user` resets another user's
password, capturing at least the acting user's id, the target user's id, and a
timestamp. The password itself SHALL NOT appear in the log.

#### Scenario: Power-user reset is audited
- GIVEN a `power_user` who resets a managed member's password via
  `POST /api/v1/users/{member_id}/set_password/`
- WHEN the reset succeeds
- THEN an audit-log entry is recorded identifying the acting power user, the
  target member, and the time of the reset
- AND the log entry does not contain the password
