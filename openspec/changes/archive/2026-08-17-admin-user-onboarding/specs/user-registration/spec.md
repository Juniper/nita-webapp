## MODIFIED Requirements

### Requirement: Self-Service Account Registration
The system SHALL provide an unauthenticated endpoint `POST /api/v1/auth/register/`
that creates a new user account with `role=user`. The endpoint SHALL require
`username`, `password`, and optionally `email`.

Self-service registration SHALL be controlled by a configuration flag
`SELF_REGISTRATION_ENABLED`, sourced from the environment variable
`NITA_SELF_REGISTRATION_ENABLED` and defaulting to **enabled** (`True`) so that
both self-registration and admin-created onboarding are active out of the box.
When the flag is disabled, the endpoint SHALL return `403` with a message
directing the requester to contact an administrator, and no account SHALL be
created. Accepted "disabled" values follow the existing boolean-env convention
(anything other than `"True"` disables the flag).

#### Scenario: Successful registration
- GIVEN no existing user with the chosen username
- AND self-registration is enabled (the default)
- WHEN `POST /api/v1/auth/register/` is called with `username` and `password`
- THEN a 201 response is returned with the new user's `id`, `username`, and `role`
- AND the created user has `role=user`

#### Scenario: Duplicate username rejected
- GIVEN a user with username `"alice"` already exists
- WHEN `POST /api/v1/auth/register/` is called with `username=alice`
- THEN a 400 response is returned indicating the username is taken

#### Scenario: Weak password rejected
- WHEN `POST /api/v1/auth/register/` is called with a password shorter than 8 characters
- THEN a 400 response is returned with password validation errors

#### Scenario: Registration does not grant elevated role
- WHEN `POST /api/v1/auth/register/` is called with `{"role": "admin"}` in the body
- THEN the created user has `role=user` regardless of the supplied role value

#### Scenario: Registration disabled by configuration
- GIVEN `NITA_SELF_REGISTRATION_ENABLED` is set to a disabling value
- WHEN `POST /api/v1/auth/register/` is called with valid `username` and `password`
- THEN a 403 response is returned and no account is created
