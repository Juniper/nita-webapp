## MODIFIED Requirements

### Requirement: Networks page lists all networks
The `/networks` page SHALL fetch and display all networks from `GET /api/v1/networks/` in a table with columns: Name, Network Type, Description, Status, and Actions (Modify + Delete).

#### Scenario: Page loads with data
- **WHEN** the user navigates to `/networks`
- **THEN** a table is displayed with one row per network showing name, network type name, description, and status

#### Scenario: Modify link navigates to detail
- **WHEN** the user clicks "Modify" on a network row
- **THEN** the browser navigates to `/app/networks/:id`

### Requirement: User can add a new Network
The page SHALL provide an inline form (toggled by "Add Network" button) with fields for name, description, network type (dropdown), and a required Host File upload. The Host File field SHALL be a file input; on submit the file contents SHALL be read and sent as the `host_file` value. The submit SHALL POST to `POST /api/v1/networks/` with an initial `status` of `Initialized`, and refresh the list on success.

#### Scenario: Successful network creation
- **WHEN** the user fills in the required fields, selects a host file, and submits the Add form
- **THEN** a POST is made to `/api/v1/networks/` with `host_file` set to the uploaded file's contents and `status` set to `Initialized`, the form closes, and the new network appears in the list

#### Scenario: Host File is required
- **WHEN** the user attempts to submit the Add form without selecting a host file
- **THEN** the form is not submitted (the file input is required)

#### Scenario: Network type dropdown populated
- **WHEN** the user opens the Add form
- **THEN** the Network Type dropdown is populated with types from `GET /api/v1/network-types/`

#### Scenario: Form submission error
- **WHEN** the POST request fails
- **THEN** an error message is displayed inside the form

## ADDED Requirements

### Requirement: Action history console viewer
The network detail page SHALL allow the user to view the Jenkins console output for any action-history entry. Each action-history row SHALL provide a View button that opens a modal which fetches `GET /api/v1/action-history/{id}/console/` and displays the returned console text.

The modal SHALL show a loading indicator while fetching, an error message if the request fails, and a placeholder when the console output is empty. The modal SHALL be dismissable (close button or backdrop click).

#### Scenario: Open console viewer for a history entry
- **WHEN** the user clicks the View button on an action-history row
- **THEN** a modal opens and `GET /api/v1/action-history/{id}/console/` is requested
- **AND** the returned console text is displayed in the modal

#### Scenario: Console fetch error
- **WHEN** the console fetch returns a non-2xx response
- **THEN** the modal displays a "Failed to load console output" error message

#### Scenario: Empty console output
- **WHEN** the console fetch succeeds but returns no console text
- **THEN** the modal displays a "No console output available." placeholder

#### Scenario: Dismiss the modal
- **WHEN** the user clicks Close or the modal backdrop
- **THEN** the modal closes
