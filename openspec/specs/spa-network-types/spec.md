## ADDED Requirements

### Requirement: Network Types page lists all types
The `/network-types` page SHALL fetch and display all network types from `GET /api/v1/network-types/` in a table with columns: Name, Description, Zip File, Roles, Resources, Actions.

#### Scenario: Page loads with data
- **WHEN** the user navigates to `/network-types`
- **THEN** a table is displayed with one row per network type showing its name, description, zip filename, role count, and resource count

#### Scenario: Loading state
- **WHEN** the page is fetching network types
- **THEN** a loading indicator SHALL be shown in place of the table

#### Scenario: Fetch error
- **WHEN** the fetch request fails
- **THEN** an error message SHALL be displayed

### Requirement: User can upload a new Network Type
The page SHALL allow the user to select a zip file and upload it via `POST /api/v1/network-types/upload/`. On success the list SHALL refresh.

#### Scenario: Successful upload
- **WHEN** the user selects a zip file and confirms upload
- **THEN** the file is POSTed to the API, and on a 2xx response the network types list refreshes

#### Scenario: Upload in progress
- **WHEN** a zip file upload is in progress
- **THEN** the upload button SHALL be disabled

#### Scenario: Upload error
- **WHEN** the upload request returns a non-2xx response
- **THEN** an error message SHALL be displayed

### Requirement: User can delete a Network Type
The page SHALL allow the user to delete a network type via `DELETE /api/v1/network-types/{id}/` with an inline confirmation step. On success the row SHALL be removed.

#### Scenario: Delete with confirmation
- **WHEN** the user clicks Delete on a row
- **THEN** the button changes to a confirmation state; clicking again executes `DELETE /api/v1/network-types/{id}/` and removes the row

#### Scenario: Cancel delete
- **WHEN** the user clicks Delete and then Cancel
- **THEN** no request is made and the row remains

### Requirement: Network Types is reachable from sidebar navigation
The sidebar link for "Network Types" SHALL navigate to the `/network-types` route and the page SHALL be protected (requires authentication).

#### Scenario: Sidebar link works
- **WHEN** the user clicks "Network Types" in the sidebar
- **THEN** the browser navigates to `/app/network-types` and the page is displayed
