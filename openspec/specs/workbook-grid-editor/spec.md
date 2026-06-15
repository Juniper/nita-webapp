# Workbook Grid Editor Specification

## Purpose
The Network Detail page SHALL render uploaded workbook data as an interactive
editable grid, allowing users to view and modify configuration values in-browser.

## Requirements

### Requirement: Render Workbook Sheets as Editable Grid
The SPA SHALL render each worksheet of an uploaded workbook as an editable
data grid in the Network Detail page, displaying the sheet's rows and columns
with the first row of each sheet used as column headers.

#### Scenario: Uploaded workbook renders as tabs
- GIVEN a network with an uploaded workbook containing multiple sheets
- WHEN the user navigates to the Network Detail page
- THEN each sheet is shown as a selectable tab
- AND the active tab renders the sheet data as a table with column headers from the first row

#### Scenario: Empty workbook shows upload prompt
- GIVEN a network with no uploaded workbook
- WHEN the user navigates to the Network Detail page workbook section
- THEN an upload prompt is displayed instead of the grid

#### Scenario: Sheet with no data rows renders headers only
- GIVEN a workbook sheet that contains only a header row
- WHEN that sheet's tab is selected
- THEN the table renders with the header row and an empty body

### Requirement: Edit Workbook Cell Values
The SPA SHALL allow users to modify individual cell values in the workbook grid
by clicking on a cell and typing a new value.

#### Scenario: User edits a cell
- GIVEN a rendered workbook grid
- WHEN the user clicks on a data cell and types a new value
- THEN the cell displays the new value
- AND the change is held in local state (not yet persisted)

#### Scenario: Edited cells are visually distinguished
- GIVEN a workbook grid with one or more unsaved edits
- WHEN the user views the grid
- THEN edited cells are visually distinguished from unedited cells

### Requirement: Save Workbook Edits
The SPA SHALL provide a Save button that persists all in-progress edits by
POSTing the updated grid data to `POST /api/v1/networks/{id}/workbook/save/`.

#### Scenario: Save persists edits
- GIVEN a workbook grid with one or more edited cells
- WHEN the user clicks Save
- THEN the SPA POSTs the updated data to the save endpoint
- AND on success, the grid reflects the saved state
- AND the visual distinction for edited cells is cleared

#### Scenario: Save failure shows error message
- GIVEN a workbook grid with pending edits
- WHEN the save POST returns a non-200 response
- THEN an error message is displayed to the user
- AND the edited cell values are preserved for retry

### Requirement: Discard Workbook Edits
The SPA SHALL allow users to discard unsaved edits by clicking a Discard / Reset
button, reverting the grid to the last saved state.

#### Scenario: Discard reverts unsaved edits
- GIVEN a workbook grid with one or more unsaved edits
- WHEN the user clicks Discard
- THEN all cells revert to their last saved values
- AND no POST request is made
