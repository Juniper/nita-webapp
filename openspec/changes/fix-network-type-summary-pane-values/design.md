## Context

The campus type detail page is loaded when a network type node is selected in the tree. Today the page depends on client-side loading to populate the summary labels for the selected type, even though the route already identifies which record should be shown.

The underlying API already exposes the selected type's summary fields, so the defect is in the rendering path rather than in the data model or serializer shape.

## Goals / Non-Goals

**Goals:**
- Selected network types show their summary metadata and associated actions reliably in the right-hand pane.
- Preserve the current API contract and tree navigation flow.
- Keep the change narrowly scoped to the network-type detail view.

**Non-Goals:**
- No model or serializer changes.
- No new API endpoint.
- No redesign of the tree or table layouts.

## Decisions

- Render the selected type's summary values in the detail template using the selected id from the route context, and keep the existing AJAX fetch as a refresh path for the same data.
  - Why: the route already identifies the selected type, and server-rendered values avoid a blank first paint while reducing dependence on browser timing.
  - Alternative considered: keep the page entirely client-side and only adjust the DOM binding. Rejected because it preserves the blank-or-undefined failure mode and is harder to regress-test with the current suite.

- Continue using the network-type retrieve payload as the canonical data shape for summary values.
  - Why: the API already contains the needed fields and keeps summary display aligned with the underlying record.
  - Alternative considered: duplicate summary fields into the tree payload. Rejected because it duplicates data and couples list rendering to detail rendering.

- Initialize the actions table with the shared `campus_type_actions_table` handle and the existing filtered actions endpoint.
  - Why: the page already defines a shared table variable for campus-type actions, and using a different name leaves the table uninitialized.
  - Alternative considered: introduce a new page-local actions table variable. Rejected because it duplicates existing state and risks diverging from the shared scripts.

- Add a regression test around the selected-type detail view.
  - Why: the bug is about rendered values, so a view/template-level regression is more valuable than another API-only check.
  - Alternative considered: API serializer coverage only. Rejected because the serializer already passes and would not catch the blank-pane issue.

## Risks / Trade-offs

- [Risk] Rendering the same values in both server markup and client-side refresh can drift -> Mitigation: source both from the same model/API field names and keep the client-side code limited to refresh.
- [Risk] A view-level test may not fully simulate browser behavior -> Mitigation: keep the test focused on the selected detail HTML and the route context that drives it.
- [Risk] Small template changes could affect existing styling -> Mitigation: preserve the current structure and element ids.
- [Risk] A stale JavaScript table handle can prevent actions from rendering -> Mitigation: keep the detail page aligned with the shared `campus_type_actions_table` variable used by the rest of the app.

## Migration Plan

- No data migration or deployment choreography is required.
- Rollback is limited to reverting the view/template change if the detail pane regresses.

## Open Questions

- None.