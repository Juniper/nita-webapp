## ADDED Requirements

### Requirement: Network Owner Assignment on Creation
The system SHALL automatically set `owner=request.user` on a `CampusNetwork`
when it is created via `POST /api/v1/networks/`. Any authenticated user MAY
create a network.

#### Scenario: Network created by user is owned by that user
- **GIVEN** a logged-in user with `role=user`
- **WHEN** `POST /api/v1/networks/` is called with valid data
- **THEN** the created network has `owner` equal to the requesting user's id

### Requirement: Network Visibility Scoping
The system SHALL scope `GET /api/v1/networks/` and `GET /api/v1/networks/{id}/`
so that a requesting user sees only:
- Networks they own (`owner=request.user`)
- Networks belonging to a team they are a member of (`team__members=request.user`)
- All networks if `role=admin`

#### Scenario: User sees only own networks
- **GIVEN** user Alice owns networks `"Net-A"` and `"Net-B"`, and user Bob owns `"Net-C"`
- **WHEN** Alice calls `GET /api/v1/networks/`
- **THEN** only `"Net-A"` and `"Net-B"` appear in the results

#### Scenario: User sees team-shared networks
- **GIVEN** user Alice is a member of `"Team-X"` which has network `"Shared-Net"`
  owned by Bob
- **WHEN** Alice calls `GET /api/v1/networks/`
- **THEN** `"Shared-Net"` appears in Alice's results

#### Scenario: User cannot retrieve another user's network directly
- **GIVEN** Bob owns network `"Net-C"` and Alice is not in Bob's team
- **WHEN** Alice calls `GET /api/v1/networks/{net_c_id}/`
- **THEN** a 404 response is returned

#### Scenario: Admin sees all networks
- **GIVEN** multiple users own multiple networks
- **WHEN** an admin calls `GET /api/v1/networks/`
- **THEN** all networks are returned

### Requirement: Network Edit and Delete Restricted to Owner or Admin
The system SHALL restrict `PATCH`, `PUT`, and `DELETE` on `GET /api/v1/networks/{id}/`
to the network's owner or a user with `role=admin`.

#### Scenario: Owner can update their network
- **GIVEN** Alice owns `"Net-A"`
- **WHEN** Alice calls `PATCH /api/v1/networks/{net_a_id}/`
- **THEN** a 200 response is returned and the network is updated

#### Scenario: Team member cannot modify a shared network
- **GIVEN** Alice is a member of a team that has access to Bob's `"Net-C"`
- **WHEN** Alice calls `PATCH /api/v1/networks/{net_c_id}/`
- **THEN** a 403 response is returned

### Requirement: Network Team Assignment
The system SHALL allow a network owner or admin to assign or change the team
for a network via `PATCH /api/v1/networks/{id}/` with a `team` field. Setting
`team=null` removes the team assignment.

#### Scenario: Owner assigns their network to a team
- **GIVEN** Alice owns `"Net-A"` and is a member of `"Team-X"`
- **WHEN** Alice calls `PATCH /api/v1/networks/{net_a_id}/` with `{"team": <team_x_id>}`
- **THEN** `"Net-A"` is associated with `"Team-X"` and all team members can now see it

## MODIFIED Requirements

### Requirement: Create a Network
The system SHALL create a new network via POST /api/v1/networks/ with name,
status, description, host_file, and campus_type fields. The system SHALL
automatically set `owner` to the authenticated requesting user.

Creation SHALL be non-blocking. The system SHALL persist the network row
immediately with status `Initializing`, invoke the `network_template_mgr`
Jenkins job with `operation=create` through the shared invocation library, and
return without waiting for the build to complete. The response SHALL include the
new network's data together with a streaming handle (`job_name` and `build_no`)
so the SPA can watch the live console. If the Jenkins service is unreachable the
system SHALL NOT persist the row and SHALL return `503 Service Unavailable` with
a JSON body containing `status`, `name`, and a human-readable `reason`. The
streamed console — not a blocking HTTP response — is the signal the user watches
for success or failure; a network whose build fails remains in the list in an
error state for the user to delete.

#### Scenario: Successful creation starts the job and streams
- **GIVEN** a valid campus_type id and an Ansible INI inventory string
- **WHEN** POST /api/v1/networks/ is called with the required fields
- **THEN** the network row is persisted immediately with status `Initializing`
- **AND** `owner` is set to the requesting user
- **AND** the `network_template_mgr` create job is invoked
- **AND** a `201` response is returned with the network data and a streaming handle
  (`job_name`, `build_no`) without waiting for the build to finish
