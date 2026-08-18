# SPA User Management Specification

## Purpose
Native, dark-themed SPA screens for administering users and teams — replacing the
Django Admin as the primary path — backed by the existing `user-management` REST
API. Covers the admin Users screen, guided ownership transfer on protected
delete, the power-user/admin Teams screen, a member-picker roster endpoint, and
surfacing network ownership/team in the SPA.

## Requirements

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

### Requirement: Member Picker Directory
The system SHALL provide a read-only roster endpoint `GET /api/v1/users/directory/`
returning only `id` and `username` for each user, accessible to `power_user` and
`admin`, so team member pickers can select users by name rather than by raw id.

#### Scenario: Power user retrieves the roster
- **GIVEN** a logged-in `power_user`
- **WHEN** `GET /api/v1/users/directory/` is called
- **THEN** a 200 response is returned listing `{id, username}` for all users

#### Scenario: Regular user cannot access the roster
- **GIVEN** a logged-in user with `role=user`
- **WHEN** `GET /api/v1/users/directory/` is called
- **THEN** a 403 response is returned

### Requirement: Network Ownership and Team Visible in the SPA
The `CampusNetwork` API SHALL expose read-only `owner_username` and `team_name`
fields. The SPA networks list SHALL show Owner and Team, and the network detail
view SHALL let an owner/admin (or team-managing power_user) assign or clear the
network's team via `PATCH /api/v1/networks/{id}/`.

#### Scenario: Networks list shows owner and team
- **GIVEN** a network owned by a user and shared with a team
- **WHEN** the networks list is rendered
- **THEN** the row shows the owner's username and the team's name

#### Scenario: Owner assigns a team from the detail view
- **GIVEN** an owner viewing their network's detail page with teams available
- **WHEN** they select a team
- **THEN** `PATCH /api/v1/networks/{id}/` is sent with the team id and the network reflects the new team

### Requirement: Create User (Admin UI)
The admin `Users` screen SHALL provide a **New user** action that opens a dialog
collecting `username`, `email`, `role`, and an initial `password`, and submits it
to `POST /api/v1/users/`. On success the new user SHALL appear in the list. The
dialog SHALL offer a way to generate and copy the password client-side, and SHALL
surface `400` validation errors (duplicate username, weak password) inline. The
password SHALL only exist client-side for copying; it SHALL never be displayed
from a server response.

#### Scenario: Admin creates a user from the UI
- **GIVEN** a logged-in admin on `/users`
- **WHEN** they open **New user**, enter a username, email, role, and password, and submit
- **THEN** `POST /api/v1/users/` is sent and, on 201, the new user appears in the list

#### Scenario: Validation errors are shown in the dialog
- **GIVEN** the New user dialog is open
- **WHEN** submission returns a 400 (e.g. duplicate username or weak password)
- **THEN** the dialog stays open and shows the error next to the relevant field

### Requirement: Reset User Password (Admin UI)
Each row on the `Users` screen SHALL provide a **Reset password** action that
opens a dialog collecting a new `password` and submits it to
`POST /api/v1/users/{id}/set_password/`. The dialog SHALL offer generate/copy for
the password and SHALL surface `400` validation errors inline. On success it
SHALL confirm the reset. The password SHALL never be displayed from a server
response.

#### Scenario: Admin resets a user's password from the UI
- **GIVEN** a logged-in admin on `/users`
- **WHEN** they choose **Reset password** on a row, enter a new password, and submit
- **THEN** `POST /api/v1/users/{id}/set_password/` is sent and, on 200, a confirmation is shown

#### Scenario: Weak reset password is rejected in the dialog
- **GIVEN** the Reset password dialog is open
- **WHEN** submission returns a 400 for a weak password
- **THEN** the dialog stays open and shows the validation error
