## Why

The Ansible host inventory (`host_file`) is the per-network INI file that
defines which devices a build targets. It is captured once at network-creation
time via the Add Network form, but the SPA gives the user no way to view or
change it afterwards. Editing the inventory currently requires recreating the
network or going around the UI. Users need to inspect and amend the host file
in place, the same way they already edit the workbook.

The Network Detail page already presents network data as tabs (Workbook,
Actions, History). Adding the host file as the **first** tab places the most
fundamental input — "what am I building against?" — front and centre, before
the workbook configuration.

## What Changes

- **Network Detail page**: Add a new **Hosts** tab as the **first** tab (before
  Workbook), shifting the tab order to Hosts → Workbook → Actions → History.
- The Hosts tab SHALL display the network's `host_file` contents in an editable
  multi-line text editor (monospace), pre-populated from the network record.
- Provide **Save** and **Discard** controls: Save persists the edited text via
  `PATCH /api/v1/networks/{id}/` with `{ host_file }`; Discard reverts the
  editor to the last saved value.
- Reflect save success/failure and unsaved-edit state to the user, consistent
  with the existing workbook editor affordances.

No backend changes are required: `CampusNetworkSerializer` already exposes
`host_file` as a writable field and the viewset's default `update`/`partial_update`
handles the PATCH.

## Capabilities

### Added Capabilities

- `network-hosts-editor`: View and edit a network's Ansible host inventory
  (`host_file`) from a Hosts tab on the Network Detail page, persisted via PATCH.

## Impact

- **Frontend** (`frontend/src/pages/NetworkDetailPage.tsx`): new tab, editor
  state, save/discard handlers; the `activeTab` union and tab-bar list gain a
  `hosts` member ordered first.
- **API**: reuses existing `PATCH /api/v1/networks/{id}/`; no new endpoint, no
  schema change.
- No database, nginx, or backend code changes.
