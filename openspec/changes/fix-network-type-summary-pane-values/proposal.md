## Why

Selecting a network type from the left-hand tree should populate the detail pane with the selected type's metadata, but the right-hand summary currently renders blank or incomplete values for users. That makes it difficult to confirm which network type is active and hides information that already exists in the underlying record.

## What Changes

- Ensure the network-type detail pane displays the selected type's name, application zip, and description.
- Keep the network-type retrieve payload as the source of truth for the summary pane.
- Add regression coverage so selecting a network type continues to surface its metadata in the UI.

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `network-types`: Extend the selected network-type experience so the detail pane renders the record's summary metadata instead of leaving fields blank.

## Impact

- Affects the campus-type detail template and its client-side data binding in the web UI.
- May require a focused regression test for the selected network-type view.
- No API shape changes are expected.