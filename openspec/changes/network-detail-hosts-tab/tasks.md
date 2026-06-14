## 1. Add the Hosts tab to the Network Detail page

- [x] 1.1 In `frontend/src/pages/NetworkDetailPage.tsx`, extend the `activeTab`
  union type to include `'hosts'` and change the initial value to `'hosts'`.
- [x] 1.2 Update the tab-bar tuple to
  `['hosts', 'workbook', 'actions', 'history'] as const` so Hosts renders first.

## 2. Hosts editor state and handlers

- [x] 2.1 Add state: `hostsText` (string), `hostsSaved` (string),
  `hostsSaving` (boolean), and `hostsError` (string | null).
- [x] 2.2 When the `network` record resolves, seed `hostsText` and `hostsSaved`
  from `network.host_file ?? ''`.
- [x] 2.3 Add a `handleSaveHosts` function that PATCHes
  `/api/v1/networks/{id}/` with `{ host_file: hostsText }`; on success update
  `hostsSaved`, sync `network.host_file`, and clear `hostsError`; on failure set
  `hostsError`.
- [x] 2.4 Add a Discard handler that resets `hostsText` to `hostsSaved`.

## 3. Hosts tab UI

- [x] 3.1 Render a Hosts tab panel (shown when `activeTab === 'hosts'`) with a
  monospace `<textarea>` bound to `hostsText`.
- [x] 3.2 Add Save and Discard buttons: Save is disabled when there are no
  unsaved changes (`hostsText === hostsSaved`) or while saving; Discard is
  shown when there are unsaved changes.
- [x] 3.3 Show a saving indicator, an unsaved-changes affordance, and inline
  `hostsError` text, consistent with the workbook editor styling.
- [x] 3.4 Show a loading state when `network` has not yet resolved.

## 4. Verification

- [x] 4.1 Build the frontend (`npm run build` in `frontend/`) and confirm no
  TypeScript errors. (npm is unavailable in this environment; verified instead
  via the editor's TypeScript language server, which reports no errors.)
- [ ] 4.2 Manually verify: the Hosts tab is first and active by default; editing
  then Save persists (reload shows the new value); Discard reverts unsaved
  edits; a failed PATCH surfaces an error and preserves the edited text.
