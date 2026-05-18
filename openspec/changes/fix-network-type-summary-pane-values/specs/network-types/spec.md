## ADDED Requirements

### Requirement: Selected Network Type Summary Pane
The system SHALL display the selected network type's name, application zip, and description in the detail pane when a network type is selected from the left-hand tree.

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