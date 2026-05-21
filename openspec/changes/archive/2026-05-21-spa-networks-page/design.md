## Context

`CampusNetwork` fields: `id`, `name`, `description`, `status`, `campus_type` (int FK), `campus_type_name` (read-only convenience), `host_file` (string), `dynamic_ansible_workspace` (boolean). Required on create: `campus_type`, `name`, `description`. The network type dropdown is populated by fetching `GET /api/v1/network-types/`. The "View" link navigates to `/networks/:id` which will be fleshed out in a later change (workbook + actions).

## Goals / Non-Goals

**Goals:**
- Fetch and display all networks in a table (name, type, description, status, actions)
- Inline "Add Network" panel (toggled): form with name, description, network type selector, host_file, dynamic_ansible_workspace — POST on submit, dismiss + refresh on success
- Per-row delete with inline confirmation
- "View" link per row that navigates to `/networks/:id`
- Stub `NetworkDetailPage` at `/networks/:id` using `AppLayout` (content: "Network detail coming soon" + back link) — placeholder for the next change
- Loading/error states on list and on form submission

**Non-Goals:**
- Editing an existing network (no PUT/PATCH UI in this change)
- Pagination controls
- The detail page content (workbook, actions) — that's the next change

## Decisions

### Inline form panel rather than a modal
**Decision**: A collapsible panel below the header row (toggled by "Add Network" button), not a modal dialog.  
**Rationale**: Avoids a modal/portal dependency; keeps the component self-contained. The panel slides in using a simple conditional render with `showAddForm` boolean state.

### Fetch network types once on mount for the dropdown
**Decision**: `useEffect` fetches `GET /api/v1/network-types/` when the add-form panel opens (lazy fetch, only when needed).  
**Rationale**: If there are no network types yet, the form can show an informative empty state rather than an empty dropdown.

### Separate stub `NetworkDetailPage`
**Decision**: Create a minimal `NetworkDetailPage` at `/networks/:id` now so the "View" links are functional and don't 404.  
**Rationale**: Keeps navigation consistent across the app. The detail page will be filled out in the next change.

## Risks / Trade-offs

- [Risk] `host_file` field purpose is unclear from the schema — it's an optional string. Include it as a text input with placeholder "optional" → no mitigation needed beyond labelling
- [Risk] `dynamic_ansible_workspace` is a boolean — render as a labelled checkbox, default unchecked
