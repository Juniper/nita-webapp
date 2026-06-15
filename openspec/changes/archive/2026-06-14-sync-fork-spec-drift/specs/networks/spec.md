## MODIFIED Requirements

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
