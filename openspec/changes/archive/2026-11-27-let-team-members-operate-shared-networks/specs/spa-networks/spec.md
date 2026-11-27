## ADDED Requirements

### Requirement: Delete control is shown only to users who may delete
The Networks page SHALL show a row's Delete control only when the signed-in user
is the network's owner (`owner_username` equals their username) or has role
`power_user` or `admin`. Team members who may modify and operate a shared
network SHALL NOT see its Delete control.

#### Scenario: Team member does not see Delete
- **GIVEN** a `user`-role member of a team the network is shared with, who is not its owner
- **WHEN** they view the networks list
- **THEN** the row shows Modify/Actions/History but no Delete control

#### Scenario: Owner and privileged roles see Delete
- **GIVEN** the network's owner, or any `power_user` / `admin`
- **WHEN** they view the networks list
- **THEN** the row shows the Delete control
