## Context

The REST API for network types is at `/api/v1/network-types/`. The session cookie set by `/api/v1/auth/login/` authenticates requests. The `apiFetch` helper in `frontend/src/api/client.ts` handles CSRF tokens on mutating requests. `CampusType` schema: `{ id, name, description, app_zip_name, roles: Role[], resources: Resource[] }`. Upload creates a new type from a zip; there is no PATCH/PUT — edits are not supported by the API.

## Goals / Non-Goals

**Goals:**
- Fetch and display all network types in a table on page load
- Upload a zip → show success/error toast → refresh list
- Delete with an inline "Are you sure?" confirmation step → remove row on success
- Loading skeleton while fetching; error banner on failure
- All in a single `NetworkTypesPage.tsx` file using `AppLayout`

**Non-Goals:**
- Pagination UI (page size 50 is sufficient for typical NITA deployments)
- Detail view / editing a network type
- Drag-and-drop upload

## Decisions

### Single-file component with local state
**Decision**: All state (`networkTypes`, `loading`, `error`, `uploading`, `deletingId`, `confirmDeleteId`) lives in `NetworkTypesPage` via `useState`/`useEffect`.  
**Rationale**: No shared state needed — this is a self-contained CRUD page. A global store would be over-engineering for a single page.

### Inline confirmation (not a modal dialog)
**Decision**: Clicking Delete once sets `confirmDeleteId`. The button text changes to "Confirm?" with a Cancel option. A second click executes the DELETE.  
**Rationale**: Avoids a modal component dependency. Simple, accessible, already seen in many admin UIs.

### File input via hidden `<input type="file">` + ref
**Decision**: A hidden file input triggered by an "Upload zip" button via `useRef`.  
**Rationale**: Standard pattern; allows full control over button styling without a third-party file picker.

### TypeScript interface for API shape
**Decision**: Define a local `NetworkType` interface matching the API schema.  
**Rationale**: Full type safety without pulling in a generated client.

## Risks / Trade-offs

- [Risk] Upload endpoint returns 200/201 but with no standard body shape — check actual response and handle gracefully → Mitigation: treat any 2xx as success; refresh list regardless
- [Risk] Large zip files may take several seconds to upload → Mitigation: disable Upload button while `uploading === true` and show a spinner label
