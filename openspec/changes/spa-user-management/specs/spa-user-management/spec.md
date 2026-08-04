## ADDED Requirements

### Requirement: SPA User List (Admin)
The SPA SHALL provide an admin-only `Users` screen at `/users` that lists all
users via `GET /api/v1/users/`, showing `username`, `email`, `role`, and active
status, styled consistently with the existing SPA tables.

#### Scenario: Admin opens the user list
- **GIVEN** a logged-in user with `role=admin`
- **WHEN** they navigate to `/users`
- **THEN** the page renders a table of all users with role and status

#### Scenario: Non-admin cannot reach the user list
- **GIVEN** a logged-in user with `role=user` or `role=power_user`
- **WHEN** they attempt to open `/users`
- **THEN** the client redirects them to `/` and the API would return 403 if called

#### Scenario: User list route survives a direct load / refresh
- **WHEN** `/users` is requested directly from the server (not via client navigation)
- **THEN** the server serves the SPA shell (HTTP 200), not a 404

### Requirement: Inline Role and Status Management
The `Users` screen SHALL let an admin change a user's `role` and toggle
`is_active` inline via `PATCH /api/v1/users/{id}/`, with the controls always
visible on each row. An admin SHALL NOT be able to change the role of, or
deactivate, their own row from this control.

#### Scenario: Admin promotes a user
- **GIVEN** the user list is open
- **WHEN** the admin selects `Power user` in a user's role control
- **THEN** `PATCH /api/v1/users/{id}/` is sent with `{"role": "power_user"}` and the row updates

#### Scenario: Admin deactivates a user
- **WHEN** the admin clicks Deactivate on another user's row
- **THEN** `PATCH /api/v1/users/{id}/` is sent with `{"is_active": false}` and the status shows Inactive

#### Scenario: Self-row is protected
- **GIVEN** the admin's own row
- **THEN** its role/deactivate/delete controls are disabled or absent

### Requirement: Guided Ownership Transfer on Protected Delete
When deleting a user returns `409` (the user still owns networks or network
types), the SPA SHALL present a transfer dialog listing the blocking resources
and allow the admin to reassign them via `POST /api/v1/users/{id}/transfer/`
before retrying the delete. Self-deletion (`400`) SHALL be shown as an inline
message.

#### Scenario: Delete blocked, then transferred and deleted
- **GIVEN** a user who owns one or more networks
- **WHEN** the admin clicks Delete
- **THEN** a dialog lists the owned resources
- **AND** choosing a recipient and confirming calls `transfer`, then re-issues the delete on success

#### Scenario: Admin cannot delete themselves
- **WHEN** the admin attempts to delete their own account
- **THEN** an inline error is shown and no account is removed

### Requirement: Team Management (Power User / Admin)
The SPA SHALL provide a `Teams` screen at `/teams` for `power_user` and `admin`
to create and delete teams and add/remove members, backed by the `/api/v1/teams/`
endpoints. A regular `user` SHALL NOT have access to this screen.

#### Scenario: Power user creates a team and adds a member
- **GIVEN** a logged-in `power_user`
- **WHEN** they create a team and add a user as a member
- **THEN** `POST /api/v1/teams/` and `POST /api/v1/teams/{id}/members/` are called and the UI reflects the new team/membership

#### Scenario: Regular user cannot reach Teams
- **GIVEN** a logged-in user with `role=user`
- **WHEN** they attempt to open `/teams`
- **THEN** the client redirects them to `/`
