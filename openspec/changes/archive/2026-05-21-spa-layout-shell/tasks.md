## 1. AppLayout component

- [x] 1.1 Create `frontend/src/components/AppLayout.tsx` with header (brand + user info + logout) and sidebar (nav links: Dashboard, Network Types, Networks)
- [x] 1.2 Sidebar links use `NavLink` from react-router-dom with active styling

## 2. Update DashboardPage

- [x] 2.1 Rewrite `frontend/src/pages/DashboardPage.tsx` to use `AppLayout` — remove inline header and logout logic, show a welcome panel as content

## 3. Verification

- [x] 3.1 Run `cd frontend && npm run build` — confirm exit 0, no TypeScript errors
- [x] 3.2 Run full test suite (`pytest`) — all 95 tests must pass
