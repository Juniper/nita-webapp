# Network Hosts Editor Specification

## Purpose
The Network Detail page SHALL allow users to view and edit a network's host
file (Ansible INI inventory) directly in the browser through a dedicated Hosts
tab, persisting changes to the network record.

## Requirements

### Requirement: Hosts tab on the Network Detail page
The Network Detail page SHALL present a **Hosts** tab as the **first** tab,
ordered before the Workbook, Actions, and History tabs. The Hosts tab SHALL be
the tab that is active when the page first loads.

#### Scenario: Hosts tab is first and active by default
- GIVEN a user opens the Network Detail page for any network
- WHEN the page finishes loading the network record
- THEN the tab bar shows tabs in the order Hosts, Workbook, Actions, History
- AND the Hosts tab is the active tab

#### Scenario: Switching away and back to Hosts
- GIVEN the user has selected the Workbook tab
- WHEN the user clicks the Hosts tab
- THEN the Hosts tab content is shown

### Requirement: View and edit the host file
The Hosts tab SHALL display the network's `host_file` contents in an editable
multi-line text editor, pre-populated from the network record. The editor SHALL
allow the user to modify the text in place.

#### Scenario: Host file is shown pre-populated
- GIVEN a network whose `host_file` contains an Ansible INI inventory
- WHEN the user views the Hosts tab
- THEN the editor displays the current `host_file` contents

#### Scenario: Editing updates local state only
- GIVEN the Hosts tab editor is shown
- WHEN the user types changes into the editor
- THEN the editor reflects the new text
- AND the change is held in local state until saved

#### Scenario: Loading state before the network resolves
- GIVEN the network record has not yet loaded
- WHEN the user is on the Hosts tab
- THEN a loading indicator is shown instead of the editor

### Requirement: Save host file edits
The Hosts tab SHALL provide a Save control that persists the edited host file by
sending `PATCH /api/v1/networks/{id}/` with a body containing the `host_file`
field. The Save control SHALL be disabled when there are no unsaved changes and
while a save is in progress.

#### Scenario: Save persists the host file
- GIVEN the user has edited the host file in the Hosts tab
- WHEN the user clicks Save
- THEN the SPA sends `PATCH /api/v1/networks/{id}/` with the updated `host_file`
- AND on success the saved value becomes the new baseline
- AND the unsaved-changes affordance is cleared

#### Scenario: Save failure shows an error
- GIVEN the user has edited the host file
- WHEN the save PATCH returns a non-2xx response
- THEN an error message is displayed
- AND the edited text is preserved for retry

#### Scenario: Save disabled without changes
- GIVEN the Hosts tab editor shows the host file with no unsaved edits
- WHEN the user views the Save control
- THEN the Save control is disabled

### Requirement: Discard host file edits
The Hosts tab SHALL allow the user to discard unsaved edits, reverting the
editor to the last saved host file value without making a request.

#### Scenario: Discard reverts unsaved edits
- GIVEN the Hosts tab editor has one or more unsaved edits
- WHEN the user clicks Discard
- THEN the editor reverts to the last saved `host_file` value
- AND no PATCH request is made
