# User Registration Specification

## Purpose
Self-service account registration plus bootstrap-admin creation on fresh
deployments.

## Requirements

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

### Requirement: Bootstrap Admin on Fresh Deployment
The system SHALL support creating an initial admin user on a fresh deployment
via two mechanisms:

1. A management command: `python manage.py create_admin --username X --email Y --password Z`
2. Environment variables `NITA_BOOTSTRAP_ADMIN_USERNAME`, `NITA_BOOTSTRAP_ADMIN_EMAIL`,
   and `NITA_BOOTSTRAP_ADMIN_PASSWORD`, checked at application startup. The env-var
   path SHALL only fire when zero users exist in the database.

The created admin SHALL have `role=admin` and `is_staff=True`.

#### Scenario: Management command creates admin
- GIVEN no user with the specified username exists
- WHEN `python manage.py create_admin --username admin --email admin@example.com --password secret`
  is run
- THEN a user with `role=admin` and `is_staff=True` is created

#### Scenario: Bootstrap env vars create admin on empty database
- GIVEN the database has zero users
- AND `NITA_BOOTSTRAP_ADMIN_USERNAME`, `_EMAIL`, and `_PASSWORD` are set
- WHEN the Django application starts
- THEN an admin user with `role=admin` is created automatically

#### Scenario: Bootstrap env vars do nothing when users already exist
- GIVEN at least one user exists in the database
- AND bootstrap env vars are set
- WHEN the Django application starts
- THEN no new user is created and no error is raised
