## MODIFIED Requirements

### Requirement: Team Management (Power User / Admin)
The SPA SHALL provide a `Teams` screen at `/teams` for `power_user` and `admin`
to create and delete teams and add/remove members across **all** teams, backed by
the `/api/v1/teams/` endpoints. A regular `user` SHALL NOT have access to this
screen. The Teams screen SHALL also provide a per-member **Reset password** action
that opens the set-password dialog and calls `POST /api/v1/users/{id}/set_password/`.

#### Scenario: Power user creates a team and adds a member
- **GIVEN** a logged-in `power_user`
- **WHEN** they create a team and add a user as a member
- **THEN** `POST /api/v1/teams/` and `POST /api/v1/teams/{id}/members/` are called and the UI reflects the new team/membership

#### Scenario: Power user resets a member's password from the Teams screen
- **GIVEN** a logged-in `power_user` viewing a team with a non-admin member
- **WHEN** they use the member's **Reset password** action and submit a valid password
- **THEN** `POST /api/v1/users/{member_id}/set_password/` is called and a success confirmation is shown

#### Scenario: Regular user cannot reach Teams
- **GIVEN** a logged-in user with `role=user`
- **WHEN** they attempt to open `/teams`
- **THEN** the client redirects them to `/`

### Requirement: User Management Screen (Power User / Admin)
The SPA SHALL make the **User Management** screen at `/users` and its navigation
link available to both `power_user` and `admin`. For a `power_user` the screen
SHALL support viewing users, resetting passwords, toggling active status, and
changing roles — while the **New user** and **Delete** controls SHALL be shown to
`admin` only, and the role picker SHALL NOT offer `admin` to a power user. A
regular `user` SHALL be redirected away from `/users`.

#### Scenario: Power user opens User Management
- **GIVEN** a logged-in `power_user`
- **WHEN** they open `/users`
- **THEN** the User Management screen renders with the user list, and no `admin`
  accounts are shown

#### Scenario: Admin-only controls are hidden from power users
- **GIVEN** a logged-in `power_user` on `/users`
- **WHEN** the screen renders
- **THEN** the **New user** and **Delete** controls are not shown, and the role
  picker does not include `admin`

#### Scenario: Admin sees full controls
- **GIVEN** a logged-in `admin` on `/users`
- **WHEN** the screen renders
- **THEN** the **New user**, **Delete**, and full role picker (including `admin`)
  are available

#### Scenario: Regular user cannot reach User Management
- **GIVEN** a logged-in user with `role=user`
- **WHEN** they attempt to open `/users`
- **THEN** the client redirects them to `/`
