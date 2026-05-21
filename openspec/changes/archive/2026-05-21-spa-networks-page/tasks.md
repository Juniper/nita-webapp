## 1. NetworksPage component

- [x] 1.1 Create `frontend/src/pages/NetworksPage.tsx` with `Network` interface, `useEffect` fetch from `GET /api/v1/networks/`, and table with loading/error states
- [x] 1.2 Add "Add Network" toggle button + inline form panel with fields: name (text), description (text), network type (select, populated from `GET /api/v1/network-types/`), host_file (text, optional), dynamic_ansible_workspace (checkbox) — POST on submit, refresh + close on success
- [x] 1.3 Add per-row delete with inline confirmation → `DELETE /api/v1/networks/{id}/`, remove row on success
- [x] 1.4 Add "View" link per row navigating to `/networks/:id`

## 2. NetworkDetailPage stub

- [x] 2.1 Create `frontend/src/pages/NetworkDetailPage.tsx` — renders `AppLayout` with network id from `useParams`, shows "Network detail — coming soon" placeholder and a back link to `/networks`

## 3. Routing

- [x] 3.1 Add `/networks` and `/networks/:id` protected routes to `frontend/src/App.tsx`

## 4. Verification

- [x] 4.1 Run `cd frontend && npm run build` — confirm exit 0, no TypeScript errors
- [x] 4.2 Run full test suite (`pytest`) — all 95 tests must pass
