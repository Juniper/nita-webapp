## MODIFIED Requirements

### Requirement: User can delete a Network
The page SHALL allow deleting a network via `DELETE /api/v1/networks/{id}/` with inline confirmation, and SHALL show the Delete control only when the signed-in user is the network's owner (`owner_username` equals their username) or has role `power_user` or `admin`. On a successful delete, the page SHALL open the live console panel using the streaming handle (`job_name`, `build_no`) returned by the delete response, connecting to `GET /api/v1/jenkins/jobs/{job_name}/{build_no}/stream/`, so the user can watch the delete job run.

#### Scenario: Delete with confirmation opens the console
- **WHEN** the user clicks Delete on a row then confirms
- **THEN** `DELETE /api/v1/networks/{id}/` is called, the row is removed, and the live console panel opens streaming the delete job

#### Scenario: Team member does not see Delete
- **GIVEN** a `user`-role member of a team the network is shared with, who is not its owner
- **WHEN** they view the networks list
- **THEN** the row shows Modify/Actions/History but no Delete control

#### Scenario: Owner and privileged roles see Delete
- **GIVEN** the network's owner, or any `power_user` / `admin`
- **WHEN** they view the networks list
- **THEN** the row shows the Delete control
