## MODIFIED Requirements

### Requirement: Upload Workbook
The system SHALL parse and store configuration data from an Excel (.xlsx) file
via POST /api/v1/networks/{id}/workbook/upload/.

The multipart form field name for the uploaded file SHALL be `file` (previously
documented as `up_file`).

#### Scenario: Successful upload
- GIVEN a valid .xlsx file for the network's topology
- WHEN it is posted as multipart/form-data with field name `file`
- THEN a 200 response with `status: success` and the parsed workbook data is returned

#### Scenario: Invalid host column
- GIVEN an .xlsx file with an unrecognised value in the host column
- WHEN it is uploaded with field name `file`
- THEN a 400 response is returned with message describing the invalid host data

#### Scenario: No file provided
- GIVEN the POST body contains no file or uses an incorrect field name
- WHEN POST /api/v1/networks/{id}/workbook/upload/ is called
- THEN a 400 response is returned

### Requirement: Retrieve Workbook
The system SHALL return the current workbook data for a network via
GET /api/v1/networks/{id}/workbook/.

Each sheet in the returned `workbook` list SHALL provide data in a structured
form with a `headers` array (column names from the first row of the sheet) and a
`rows` array (each element is an array of cell values, one element per subsequent
row), in addition to the sheet `name`.

#### Scenario: Workbook data returned with structured shape
- GIVEN a network with an uploaded workbook containing at least one data row
- WHEN GET /api/v1/networks/{id}/workbook/ is called
- THEN a 200 response with `status: success` and a `workbook` list is returned
- AND each item contains `name` (sheet name), `headers` (array of strings), and `rows` (array of arrays)

#### Scenario: Sheet with no data rows returns empty rows array
- GIVEN a workbook sheet that contains only a header row
- WHEN GET /api/v1/networks/{id}/workbook/ is called
- THEN the sheet entry contains `headers` with the header values and `rows` as an empty array

#### Scenario: Empty workbook returns empty list
- GIVEN a network with no uploaded workbook
- WHEN GET /api/v1/networks/{id}/workbook/ is called
- THEN a 200 response with `workbook: []` is returned
