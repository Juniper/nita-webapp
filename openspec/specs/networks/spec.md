# Networks Specification

## Purpose
Networks (CampusNetwork) are instances of a network type, representing a
specific deployment with its own host inventory and configuration data.

## Requirements

### Requirement: Create a Network
The system SHALL create a new network via POST /api/v1/networks/ with name,
status, description, host_file, and campus_type fields.

#### Scenario: Successful creation
- GIVEN a valid campus_type id and an Ansible INI inventory string
- WHEN POST /api/v1/networks/ is called with the required fields
- THEN a 201 response is returned with the new network's id and name

#### Scenario: Duplicate name rejected
- GIVEN a network named `my-network` already exists
- WHEN POST /api/v1/networks/ is called with the same name
- THEN a 400 response is returned

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

#### Scenario: Successful delete
- GIVEN an existing network id
- WHEN DELETE /api/v1/networks/{id}/ is called
- THEN a 204 No Content response is returned
- AND the network no longer appears in the list

### Requirement: Dynamic Ansible Workspace
A network MAY have the `dynamic_ansible_workspace` flag set, which causes
NITA to use a per-network build directory at runtime.

#### Scenario: Dynamic workspace path
- GIVEN a network with dynamic_ansible_workspace true
- WHEN a build action is triggered
- THEN the build directory is set to /var/tmp/build/<type>-<network>
