## Context

`NetworkDetailPage.tsx` manages its tabs through a single state variable:

```ts
const [activeTab, setActiveTab] = useState<'workbook' | 'actions' | 'history'>('workbook')
const [loaded, setLoaded] = useState({ workbook: false, actions: false, history: false })
```

and renders the tab bar from a literal tuple:

```tsx
{(['workbook', 'actions', 'history'] as const).map(tab => ( … ))}
```

The network record (including `host_file`) is already fetched on mount and held
in `network` state. `CampusNetworkSerializer` uses `fields = "__all__"`, so
`host_file` is writable, and `CampusNetworkViewSet` does not override `update`
/ `partial_update` — a plain `PATCH /api/v1/networks/{id}/` with
`{ host_file }` updates the inventory without triggering any Jenkins job
(unlike create/destroy).

The workbook editor (`WorkbookGrid`) already establishes the UX vocabulary this
feature should mirror: an editable surface, a Save action, a Discard/Reset
action, a visible "unsaved changes" affordance, and inline error reporting.

## Goals / Non-Goals

**Goals:**
- A Hosts tab, ordered first, that shows and edits `host_file`.
- Save via `PATCH /api/v1/networks/{id}/`; Discard reverts to last saved value.
- Clear unsaved/saving/error/success feedback.

**Non-Goals:**
- No INI/syntax validation or linting of the host file contents (free text,
  same contract as creation).
- No backend changes, no new endpoint, no Jenkins job on save.
- No diffing or version history of the host file.

## Decisions

### Edit via PATCH on the existing network resource
Saving issues `PATCH /api/v1/networks/{id}/` with a JSON body
`{ "host_file": "<text>" }`. This reuses the existing, already-specced Update a
Network requirement and avoids a bespoke endpoint. PATCH (partial update) is
chosen over PUT so unrelated fields are untouched.

### Hosts tab is first; tab order becomes Hosts → Workbook → Actions → History
The `activeTab` union and the tab-bar tuple gain `'hosts'` as the first element.
The default `activeTab` initial value changes from `'workbook'` to `'hosts'` so
the page opens on Hosts. The `loaded` map is not required for Hosts because the
host file already arrives with the on-mount network fetch; the editor seeds its
text from `network.host_file` when the network resolves.

### Editor state mirrors the workbook editor pattern
Local state holds the editable text and the last-saved baseline:
- `hostsText` — current textarea value.
- `hostsSaved` — last persisted value (for Discard and dirty detection).
- `hostsSaving` / `hostsError` — in-flight and error feedback.
A "Save" button is enabled only when `hostsText !== hostsSaved`; "Discard"
resets `hostsText` to `hostsSaved`. On a successful PATCH, `hostsSaved` is
updated to the new value and the local `network` state's `host_file` is updated
so other tabs/views stay consistent.

## Risks / Trade-offs

- **Risk**: A user could save an inventory that is syntactically invalid for
  Ansible. *Mitigation*: out of scope — creation already accepts free-text host
  files, so this preserves the existing contract rather than regressing it.
- **Trade-off**: Seeding the editor from `network.host_file` couples the Hosts
  tab to the on-mount network fetch. This is acceptable and avoids a second
  request; if `network` is null the tab shows a loading state.

## Migration Plan

None. Purely additive frontend feature over an existing API.

## Open Questions

- Should an empty host file be disallowed on save? Deferred — the field is a
  required `TextField` at creation, but editing to empty is not blocked here;
  the backend serializer remains the authority.
