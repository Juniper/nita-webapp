## ADDED Requirements

### Requirement: History tab shows who triggered each run
The History tab on the network detail page SHALL display a **Triggered by**
column showing the `triggered_by_username` value of each action-history entry.
When the value is empty — as it is for runs recorded before the field existed —
the cell SHALL render an em dash (`—`) rather than an empty cell, so that
"unknown actor" is visually distinct from a rendering failure.

#### Scenario: Triggering user is shown
- **GIVEN** an action-history entry whose `triggered_by_username` is `"alice"`
- **WHEN** the user opens the History tab
- **THEN** that row displays `alice` in the Triggered by column

#### Scenario: Unknown actor is shown as an em dash
- **GIVEN** an action-history entry whose `triggered_by_username` is empty
- **WHEN** the user opens the History tab
- **THEN** that row displays `—` in the Triggered by column
