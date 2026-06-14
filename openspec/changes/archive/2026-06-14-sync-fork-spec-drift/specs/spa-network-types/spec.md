## MODIFIED Requirements

### Requirement: User can upload a new Network Type
The page SHALL allow the user to select a zip file and upload it via `POST /api/v1/network-types/upload/`. The file SHALL be sent as multipart form data using the field name `app_zip_file` (the field name the backend expects). On success the list SHALL refresh.

#### Scenario: Successful upload
- **WHEN** the user selects a zip file and confirms upload
- **THEN** the file is POSTed to the API as multipart form data with the field name `app_zip_file`, and on a 2xx response the network types list refreshes

#### Scenario: Upload in progress
- **WHEN** a zip file upload is in progress
- **THEN** the upload button SHALL be disabled

#### Scenario: Upload error
- **WHEN** the upload request returns a non-2xx response
- **THEN** an error message SHALL be displayed
