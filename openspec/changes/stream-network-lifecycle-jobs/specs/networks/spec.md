## MODIFIED Requirements

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
