# Networks Specification

## Purpose
Networks (CampusNetwork) are instances of a network type, representing a
specific deployment with its own host inventory and configuration data.

## Requirements

### Requirement: Create a Network
The system SHALL create a new network via POST /api/v1/networks/ with name,
status, description, host_file, and campus_type fields.

Creation SHALL synchronously run the `network_template_mgr` Jenkins job with
`operation=create` and block until the job completes. The database row SHALL be
persisted only if the job succeeds. If the job runs but fails, the system SHALL
trigger a cleanup `operation=delete` job and return `502 Bad Gateway`. If the
Jenkins service is unreachable, the system SHALL return `503 Service
Unavailable`. The error responses SHALL include a JSON body with `status`,
`name`, and a human-readable `reason`.

#### Scenario: Successful creation
- GIVEN a valid campus_type id and an Ansible INI inventory string
- WHEN POST /api/v1/networks/ is called with the required fields
- AND the `network_template_mgr` create job succeeds
- THEN a 201 response is returned with the new network's id and name
- AND the network row is persisted

#### Scenario: Duplicate name rejected
- GIVEN a network named `my-network` already exists
- WHEN POST /api/v1/networks/ is called with the same name
- THEN a 400 response is returned

#### Scenario: Jenkins create job fails
- GIVEN a valid create request
- WHEN the `network_template_mgr` create job runs but fails
- THEN a cleanup `operation=delete` job is triggered
- AND a 502 response is returned with a failure reason
- AND no network row is persisted

#### Scenario: Jenkins unreachable on create
- GIVEN the Jenkins service is not reachable from the Django container
- WHEN POST /api/v1/networks/ is called
- THEN a 503 response is returned with a failure reason
- AND no network row is persisted

### Requirement: List Networks
The system SHALL return a paginated list of networks via GET /api/v1/networks/.

#### Scenario: List returns all networks
- GIVEN one or more networks exist
- WHEN GET /api/v1/networks/ is called
- THEN a 200 response with count and results is returned

#### Scenario: Filter by campus type
- GIVEN networks of multiple types exist
- WHEN GET /api/v1/networks/?campus_type_id=<id> is called
- THEN only networks belonging to that campus type are returned

### Requirement: Retrieve a Network
The system SHALL return full network detail including campus_type_name via
GET /api/v1/networks/{id}/.

#### Scenario: Retrieve includes campus_type_name
- GIVEN a network associated with a campus type
- WHEN GET /api/v1/networks/{id}/ is called
- THEN the response includes `campus_type_name` as a string field

#### Scenario: Host file stored verbatim
- GIVEN a network was created with a specific host_file string
- WHEN GET /api/v1/networks/{id}/ is called
- THEN `host_file` in the response matches the original string exactly

### Requirement: Update a Network
The system SHALL support full replacement via PUT and partial update via PATCH
on /api/v1/networks/{id}/.

#### Scenario: Partial update
- GIVEN an existing network
- WHEN PATCH /api/v1/networks/{id}/ is called with only `description`
- THEN a 200 response is returned with the description updated

### Requirement: Delete a Network
The system SHALL remove a network via DELETE /api/v1/networks/{id}/.

Deletion SHALL synchronously run the `network_template_mgr` Jenkins job with
`operation=delete` and block until the job completes. The database row SHALL be
removed only if the job succeeds. If the job runs but fails, the system SHALL
return `502 Bad Gateway`; if the Jenkins service is unreachable, the system
SHALL return `503 Service Unavailable`.

#### Scenario: Successful delete
- GIVEN an existing network id
- WHEN DELETE /api/v1/networks/{id}/ is called
- AND the `network_template_mgr` delete job succeeds
- THEN a 204 No Content response is returned
- AND the network no longer appears in the list

#### Scenario: Jenkins delete job fails
- GIVEN an existing network id
- WHEN the `network_template_mgr` delete job runs but fails
- THEN a 502 response is returned with a failure reason
- AND the network row is NOT removed

#### Scenario: Jenkins unreachable on delete
- GIVEN the Jenkins service is not reachable from the Django container
- WHEN DELETE /api/v1/networks/{id}/ is called
- THEN a 503 response is returned with a failure reason
- AND the network row is NOT removed

### Requirement: Dynamic Ansible Workspace
The system SHALL always use a per-network build directory at runtime. The
`dynamic_ansible_workspace` flag has been removed; the dynamic workspace is
the permanent, only behaviour.

#### Scenario: Dynamic workspace path
- GIVEN any network
- WHEN a build action is triggered
- THEN the build directory is set to /var/tmp/build/<type>-<network>
