## MODIFIED Requirements

### Requirement: Default Credentials
The system SHALL ship with a bootstrap admin mechanism. The default
`vagrant/vagrant123` credential is superseded by the `create_admin` management
command and the `NITA_BOOTSTRAP_ADMIN_*` environment variable path (see
`user-registration` capability). Development and CI environments SHALL use the
bootstrap mechanism to create the initial admin user.

#### Scenario: Bootstrap admin can log in after fresh install
- **GIVEN** NITA has just been installed with bootstrap env vars or `create_admin`
- **WHEN** `POST /api/v1/auth/login/` is called with the configured credentials
- **THEN** a session is established and `GET /api/v1/auth/me/` returns `"role": "admin"`

## ADDED Requirements

### Requirement: Me Endpoint Returns Role and Teams
The system SHALL extend the `GET /api/v1/auth/me/` response to include the
authenticated user's `role` and a list of team IDs they belong to.

#### Scenario: Me response includes role
- **GIVEN** a logged-in user with `role=power_user`
- **WHEN** `GET /api/v1/auth/me/` is called
- **THEN** the response includes `"role": "power_user"`

#### Scenario: Me response includes team memberships
- **GIVEN** a logged-in user who is a member of teams with ids 1 and 3
- **WHEN** `GET /api/v1/auth/me/` is called
- **THEN** the response includes `"teams": [1, 3]`
