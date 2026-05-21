## ADDED Requirements

### Requirement: Networks page lists all networks
The `/networks` page SHALL fetch and display all networks from `GET /api/v1/networks/` in a table with columns: Name, Network Type, Description, Status, and Actions (View + Delete).

#### Scenario: Page loads with data
- **WHEN** the user navigates to `/networks`
- **THEN** a table is displayed with one row per network showing name, network type name, description, and status

#### Scenario: View link navigates to detail
- **WHEN** the user clicks "View" on a network row
- **THEN** the browser navigates to `/app/networks/:id`

### Requirement: User can add a new Network
The page SHALL provide an inline form (toggled by "Add Network" button) with fields for name, description, network type (dropdown), host_file, and dynamic_ansible_workspace. On submit it SHALL POST to `POST /api/v1/networks/` and refresh the list on success.

#### Scenario: Successful network creation
- **WHEN** the user fills in the required fields and submits the Add form
- **THEN** a POST is made to `/api/v1/networks/`, the form closes, and the new network appears in the list

#### Scenario: Network type dropdown populated
- **WHEN** the user opens the Add form
- **THEN** the Network Type dropdown is populated with types from `GET /api/v1/network-types/`

#### Scenario: Form submission error
- **WHEN** the POST request fails
- **THEN** an error message is displayed inside the form

### Requirement: User can delete a Network
The page SHALL allow deleting a network via `DELETE /api/v1/networks/{id}/` with inline confirmation.

#### Scenario: Delete with confirmation
- **WHEN** the user clicks Delete on a row then confirms
- **THEN** `DELETE /api/v1/networks/{id}/` is called and the row is removed

### Requirement: Network detail stub route exists
A stub `NetworkDetailPage` SHALL exist at `/networks/:id` showing the network name and a back link, as a placeholder for the next change.

#### Scenario: Detail page renders without error
- **WHEN** the user navigates to `/app/networks/1`
- **THEN** the page renders inside `AppLayout` without a 404 or blank screen
