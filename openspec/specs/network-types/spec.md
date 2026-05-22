# Network Types Specification

## Purpose
Network types (CampusType) represent reusable project templates that define the
Ansible roles, resources, and actions available for a class of network topology.

## Requirements

### Requirement: List Network Types
The system SHALL return a paginated list of all registered network types via
GET /api/v1/network-types/.

#### Scenario: List returns all types
- GIVEN one or more network types are registered
- WHEN GET /api/v1/network-types/ is called with a valid token
- THEN a 200 response with `count` and `results` fields is returned

#### Scenario: Filter by name
- GIVEN a network type named `evpn_vxlan_erb_dc_1.3` is registered
- WHEN GET /api/v1/network-types/?name=evpn_vxlan_erb_dc_1.3 is called
- THEN only that network type appears in results

### Requirement: Retrieve a Network Type
The system SHALL return the full detail of a single network type via
GET /api/v1/network-types/{id}/.

#### Scenario: Retrieve by id
- GIVEN a network type with a known id
- WHEN GET /api/v1/network-types/{id}/ is called
- THEN a 200 response with name, description, roles and resources is returned

### Requirement: Upload a Network Type
The system SHALL register a new network type from a zip archive via
POST /api/v1/network-types/upload/.

#### Scenario: Successful upload
- GIVEN a valid project zip with project.yaml and ansible.cfg
- WHEN the zip is posted as multipart/form-data with field name `app_zip_file`
- THEN a 200 response with `result: success`, `name`, and `id` is returned
- AND the network type appears in subsequent GET /api/v1/network-types/ calls

#### Scenario: Missing file
- GIVEN no file is included in the POST body
- WHEN POST /api/v1/network-types/upload/ is called
- THEN a 400 response with `result: failure` and a reason is returned

### Requirement: Delete a Network Type
The system SHALL remove a network type via DELETE /api/v1/network-types/{id}/.

#### Scenario: Successful delete
- GIVEN a network type with a known id
- WHEN DELETE /api/v1/network-types/{id}/ is called
- THEN a 204 No Content response is returned
- AND the type no longer appears in the list

### Requirement: Nested Roles and Resources
The network type response SHALL include nested lists of associated Ansible roles
and resources.

#### Scenario: Roles included in response
- GIVEN a network type with one or more roles defined in project.yaml
- WHEN GET /api/v1/network-types/{id}/ is called
- THEN the response body contains a non-empty `roles` list with id and name

### Requirement: Pagination
The system SHALL paginate list responses with a default page size of 50 items.

#### Scenario: Paginated response envelope
- GIVEN any call to GET /api/v1/network-types/
- WHEN the response is received
- THEN it contains `count`, `next`, `previous`, and `results` fields

### Requirement: Selected Network Type Summary Pane
The system SHALL display the selected network type's name, application zip, and
description in the detail pane when a network type is selected from the left-hand
tree.

#### Scenario: Detail pane shows the selected type
- GIVEN two or more network types exist with distinct names, application zips, and descriptions
- WHEN the user selects one of those network types in the tree
- THEN the right-hand detail pane displays the selected type's name, application zip, and description
- AND the values correspond to the selected network type, not the previously selected one

#### Scenario: Switching selection updates the pane
- GIVEN a different network type is selected after the first
- WHEN the user changes the selection
- THEN the detail pane updates to the newly selected network type's values
- AND the pane does not continue showing the old selection's metadata

### Requirement: Selected Network Type Actions Table
The system SHALL display the actions associated with the selected network type in
the detail pane when a network type is selected from the left-hand tree.

#### Scenario: Actions table shows selected type actions
- GIVEN a network type with one or more actions exists
- WHEN the user selects that network type in the tree
- THEN the actions table is populated with the actions belonging to that network type
- AND the actions are loaded using the selected network type id

#### Scenario: Switching selection updates actions
- GIVEN a different network type is selected after the first
- WHEN the user changes the selection
- THEN the actions table updates to show the newly selected network type's actions
- AND previously loaded actions are not retained
