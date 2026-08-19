# User Roles Specification

## Purpose
Three-tier role system (user/power_user/admin) on the custom user model and
role-based permission enforcement across the API.

## Requirements

### Requirement: Custom User Model with Role Field
The system SHALL use a custom User model (subclassing `AbstractUser`) with a
`role` field that takes exactly one of three values: `user`, `power_user`, or
`admin`. The default value SHALL be `user`.

#### Scenario: New user defaults to role=user
- WHEN a user account is created without specifying a role
- THEN `user.role` equals `"user"`

#### Scenario: Role field is readable via me endpoint
- GIVEN a logged-in user with role `power_user`
- WHEN `GET /api/v1/auth/me/` is called
- THEN the response includes `"role": "power_user"`

### Requirement: Role-Based Permission Enforcement
The system SHALL enforce access control based on the requesting user's role
across all API endpoints. Three permission classes SHALL be applied:

- `IsAdminRole`: grants access only when `request.user.role == "admin"`
- `IsPowerUserOrAdmin`: grants access when role is `"power_user"` or `"admin"`
- `IsOwnerOrAdmin`: grants access when the requesting user owns the object or
  has `role == "admin"`

#### Scenario: Admin accesses any resource
- GIVEN a user with `role=admin`
- WHEN any API endpoint is called
- THEN access is granted regardless of object ownership

#### Scenario: User cannot access admin-only endpoint
- GIVEN a user with `role=user`
- WHEN `GET /api/v1/users/` is called (admin-only endpoint)
- THEN a 403 response is returned

#### Scenario: Power user cannot access an admin-only endpoint
- GIVEN a user with `role=power_user`
- WHEN `POST /api/v1/users/` (create) is called (admin-only endpoint)
- THEN a 403 response is returned

### Requirement: Role Assignment (Admin grants admin; Power User up to power_user)
Granting the `admin` role SHALL be restricted to users with `role=admin`. A
`power_user` MAY change the `role` of a **non-admin** user among `user` and
`power_user` as part of junior-admin user management, but SHALL NOT set any user's
role to `admin` and SHALL NOT modify an `admin` account. A regular `user` SHALL
NOT change any user's role.

#### Scenario: Admin promotes a user to admin
- GIVEN a user with `role=admin`
- WHEN `PATCH /api/v1/users/{id}/` is called with `{"role": "admin"}`
- THEN the target user's role becomes `admin` and a 200 response is returned

#### Scenario: Power user promotes a user to power_user
- GIVEN a user with `role=power_user` and a target with `role=user`
- WHEN `PATCH /api/v1/users/{id}/` is called with `{"role": "power_user"}`
- THEN the target user's role becomes `power_user` and a 200 response is returned

#### Scenario: Power user cannot grant the admin role
- GIVEN a user with `role=power_user`
- WHEN `PATCH /api/v1/users/{id}/` is called with `{"role": "admin"}`
- THEN a 403 response is returned and the role is unchanged

#### Scenario: Non-admin, non-power-user cannot change roles
- GIVEN a user with `role=user`
- WHEN `PATCH /api/v1/users/{id}/` is called with any `role`
- THEN a 403 response is returned and the role is unchanged
