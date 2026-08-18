## MODIFIED Requirements

### Requirement: Team Management (Power User / Admin)
The SPA SHALL provide a `Teams` screen at `/teams` for `power_user` and `admin`
to create and delete teams and add/remove members, backed by the `/api/v1/teams/`
endpoints. A regular `user` SHALL NOT have access to this screen. The Teams screen
SHALL also provide a per-member **Reset password** action that opens the set-password
dialog and calls `POST /api/v1/users/{id}/set_password/`; for a `power_user` this
action is available for `role=user` members of teams they created (the server
authorises the request).

#### Scenario: Power user creates a team and adds a member
- **GIVEN** a logged-in `power_user`
- **WHEN** they create a team and add a user as a member
- **THEN** `POST /api/v1/teams/` and `POST /api/v1/teams/{id}/members/` are called and the UI reflects the new team/membership

#### Scenario: Power user resets a member's password from the Teams screen
- **GIVEN** a logged-in `power_user` viewing a team they created with a `role=user` member
- **WHEN** they use the member's **Reset password** action and submit a valid password
- **THEN** `POST /api/v1/users/{member_id}/set_password/` is called and a success confirmation is shown

#### Scenario: Regular user cannot reach Teams
- **GIVEN** a logged-in user with `role=user`
- **WHEN** they attempt to open `/teams`
- **THEN** the client redirects them to `/`
