# Networks Specification

## Purpose
Networks (CampusNetwork) are instances of a network type, representing a
specific deployment with its own host inventory and configuration data.
## Requirements
### Requirement: Create a Network
The system SHALL create a new network via POST /api/v1/networks/ with name,
status, description, host_file, and campus_type fields.

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
- GIVEN a valid campus_type id and an Ansible INI inventory string
- WHEN POST /api/v1/networks/ is called with the required fields
- THEN the network row is persisted immediately with status `Initializing`
- AND the `network_template_mgr` create job is invoked
- AND a `201` response is returned with the network data and a streaming handle
  (`job_name`, `build_no`) without waiting for the build to finish

#### Scenario: Duplicate name rejected
- GIVEN a network named `my-network` already exists
- WHEN POST /api/v1/networks/ is called with the same name
- THEN a 400 response is returned

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

Deletion SHALL be non-blocking. The system SHALL reserve the build number and
invoke the `network_template_mgr` Jenkins job with `operation=delete` through
the shared invocation library, remove the database row immediately
(optimistically), and return without waiting for the build to complete. The
response SHALL include a streaming handle (`job_name` and `build_no`) so the SPA
can watch the live console of the delete job, which runs against the shared
`network_template_mgr` job and therefore does not depend on the removed row. If
the Jenkins service is unreachable the system SHALL NOT remove the row and SHALL
return `503 Service Unavailable` with a failure reason.

#### Scenario: Successful delete starts the job and streams
- GIVEN an existing network id
- WHEN DELETE /api/v1/networks/{id}/ is called
- THEN the `network_template_mgr` delete job is invoked
- AND the network row is removed immediately
- AND a `202` response is returned with a streaming handle (`job_name`,
  `build_no`) without waiting for the build to finish

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

