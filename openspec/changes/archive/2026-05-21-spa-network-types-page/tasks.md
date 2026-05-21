## 1. NetworkTypesPage component

- [x] 1.1 Create `frontend/src/pages/NetworkTypesPage.tsx` with `NetworkType` interface, `useEffect` fetch from `GET /api/v1/network-types/`, and table rendering with loading/error states
- [x] 1.2 Add upload button with hidden `<input type="file" accept=".zip">` ref — on file selection POST to `POST /api/v1/network-types/upload/` as `multipart/form-data`, refresh list on success, show error on failure
- [x] 1.3 Add per-row delete with inline confirmation (`confirmDeleteId` state) — on confirm DELETE `/api/v1/network-types/{id}/`, remove row on success

## 2. Routing

- [x] 2.1 Add `/network-types` protected route to `frontend/src/App.tsx` rendering `NetworkTypesPage`

## 3. Verification

- [x] 3.1 Run `cd frontend && npm run build` — confirm exit 0, no TypeScript errors
- [x] 3.2 Run full test suite (`pytest`) — all 95 tests must pass
