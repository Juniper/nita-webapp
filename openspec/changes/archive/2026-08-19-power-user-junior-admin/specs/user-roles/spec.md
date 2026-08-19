## MODIFIED Requirements

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
