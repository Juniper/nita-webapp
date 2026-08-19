## MODIFIED Requirements

### Requirement: User can delete a Network Type
The page SHALL offer the **Delete** control only to users with `role=power_user`
or `role=admin`; a regular `user` SHALL NOT see it. Deletion goes through
`DELETE /api/v1/network-types/{id}/` with an inline confirmation step. On success
the row SHALL be removed. When the API responds `409` (the type is still used by
one or more networks), the page SHALL surface the returned message and the
blocking network names rather than a bare status code.

#### Scenario: Delete with confirmation
- **GIVEN** a logged-in `power_user` or `admin`
- **WHEN** the user clicks Delete on a row
- **THEN** the button changes to a confirmation state; clicking again executes `DELETE /api/v1/network-types/{id}/` and removes the row

#### Scenario: Cancel delete
- **WHEN** the user clicks Delete and then Cancel
- **THEN** no request is made and the row remains

#### Scenario: Blocked delete explains which networks are using the type
- **GIVEN** a network type still referenced by networks
- **WHEN** the user confirms deletion and the API responds `409`
- **THEN** the page shows the blocking network names and the row remains

#### Scenario: Regular user does not see the Delete control
- **GIVEN** a logged-in user with `role=user`
- **WHEN** the Network Types page renders
- **THEN** no Delete control is shown for any row
