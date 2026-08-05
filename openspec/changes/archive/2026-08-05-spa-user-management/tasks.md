## 1. SPA Auth Model

- [x] 1.1 Extend the `User` type in `frontend/src/context/AuthContext.tsx` with `role?: string` and `teams?: number[]`
- [x] 1.2 Add a small `useIsAdmin()` / `useIsPowerUser()` helper (or inline checks) driven by `role`/`is_superuser`

## 2. Users View (Admin)

- [x] 2.1 Add `frontend/src/pages/UsersPage.tsx` listing users (`GET /api/v1/users/`) with username, email, role, status
- [x] 2.2 Inline role change via `PATCH /api/v1/users/{id}/` (role select), gated so a user cannot change their own row
- [x] 2.3 Activate/Deactivate via `PATCH /api/v1/users/{id}/` (`is_active`)
- [x] 2.4 Delete with confirm via `DELETE /api/v1/users/{id}/`; surface 400 (self) inline
- [x] 2.5 Make row actions always visible (not hover-gated) to match expected discoverability
- [x] 2.6 Add client-side search/filter and pagination controls for the user list

## 3. Ownership-Transfer Dialog

- [x] 3.1 Add a transfer modal component that opens when `DELETE` returns 409, listing the blocking networks/types from the response body
- [x] 3.2 Let the admin choose a recipient user and call `POST /api/v1/users/{id}/transfer/` with `networks_to`/`types_to`
- [x] 3.3 On successful transfer, retry the delete and update the list; handle transfer 400 (invalid recipient) inline

## 4. Teams View (Power User / Admin)

- [x] 4.1 Add `frontend/src/pages/TeamsPage.tsx` listing teams (`GET /api/v1/teams/`), scoped per role by the API
- [x] 4.2 Create a team (`POST /api/v1/teams/`) and delete a team (`DELETE /api/v1/teams/{id}/`)
- [x] 4.3 Add/remove members (`POST /api/v1/teams/{id}/members/`, `DELETE /api/v1/teams/{id}/members/{user_id}/`)
- [x] 4.4 Handle 403 for regular users gracefully (route guard prevents access)

## 5. Navigation, Routing & Guards

- [x] 5.1 Add an admin-only **User Management** sidebar entry in `AppLayout.tsx` linking to the in-SPA `/users` route
- [x] 5.2 Add a power-user/admin **Teams** sidebar entry linking to `/teams`
- [x] 5.3 Register the `/users` route in `App.tsx`
- [x] 5.4 Register the `/teams` route in `App.tsx`
- [x] 5.5 Add client-side role guards (redirect non-permitted users to `/`) for the new routes
- [x] 5.6 Extend the SPA route allowlist regex in `ngcn_workbench/urls.py` with `users`
- [x] 5.7 Extend the SPA route allowlist regex with `teams`

## 6. Tests & Build

- [x] 6.1 Add `/users` to `SPA_ROUTES` in `tests/test_spa_routing.py`
- [x] 6.2 Add `/teams` to `SPA_ROUTES` in `tests/test_spa_routing.py`
- [x] 6.3 Verify `tsc -b && vite build` compiles cleanly with the new pages/components
- [x] 6.4 Run the backend test suite (SPA routing parity) and confirm green

## 7. Member Picker & Network↔Team Sharing

- [x] 7.1 Add a read-only `GET /api/v1/users/directory/` action (id+username, `IsPowerUserOrAdmin`) so power users can pick members by name
- [x] 7.2 Teams page: replace the raw user-id input with a name select backed by the directory; resolve member ids→names from it
- [x] 7.3 Add read-only `owner_username` and `team_name` fields to `CampusNetworkSerializer`
- [x] 7.4 Networks list: show Owner and Team columns
- [x] 7.5 Network detail: add a team selector (owner/admin/power-user) that PATCHes `team`; degrade gracefully to read-only for users who cannot list teams
- [x] 7.6 Tests: directory endpoint (power-user 200 / regular 403), serializer owner/team fields; regenerate `openapi.yaml`
