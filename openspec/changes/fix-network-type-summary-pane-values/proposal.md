## Why

Selecting a network type from the left-hand tree should populate the detail pane with the selected type's metadata and associated actions, but the right-hand pane currently renders blank or incomplete values for users. That makes it difficult to confirm which network type is active and hides information that already exists in the underlying record.

## What Changes

- Ensure the network-type detail pane displays the selected type's name, application zip, and description.
- Populate the actions table for the selected network type from the existing filtered actions endpoint.
- Keep the network-type retrieve payload as the source of truth for the summary pane and the actions endpoint as the source of truth for the table.
- Add regression coverage so selecting a network type continues to surface its metadata and actions in the UI.

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `network-types`: Extend the selected network-type experience so the detail pane renders the record's summary metadata and associated actions instead of leaving fields blank.

## Impact

- Affects the campus-type detail template and its client-side data binding in the web UI.
- Affects the campus-type detail template, its actions table binding, and focused regression tests.
- No API shape changes are expected.