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

#### Scenario: Power user cannot access admin-only endpoint
- GIVEN a user with `role=power_user`
- WHEN `GET /api/v1/users/` is called (admin-only endpoint)
- THEN a 403 response is returned

### Requirement: Role Assignment Restricted to Admin
The system SHALL only allow users with `role=admin` to change another user's
role. A `power_user` or `user` SHALL NOT be able to elevate their own or
another user's role.

#### Scenario: Admin promotes user to power_user
- GIVEN a user with `role=admin`
- WHEN `PATCH /api/v1/users/{id}/` is called with `{"role": "power_user"}`
- THEN the target user's role is updated and a 200 response is returned

#### Scenario: Non-admin cannot change role
- GIVEN a user with `role=user`
- WHEN `PATCH /api/v1/users/{id}/` is called with `{"role": "power_user"}`
- THEN a 403 response is returned and the role is unchanged
