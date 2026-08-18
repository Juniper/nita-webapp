## Why

The network-sharing model contains a shipped contradiction. The **write** side
lets any owner assign their network to a team
(`PATCH /api/v1/networks/{id}/` with a `team` field is allowed for the owner),
but the **read** side starves a regular user of the information needed to do it:
`GET /api/v1/teams/` returns `403` for `role=user`, and `GET /api/v1/auth/me/`
returns only bare team **IDs** (integers, no names). A regular user can therefore
write `network.team = 7` but has no supported way to discover what team `7` is.

Separately, `power_user` — the role that curates teams and membership — has the
**same** narrow network visibility as a regular user (own + team only); only
`admin` sees everything. That leaves the role responsible for organising sharing
unable to see or operate on the networks it is meant to organise.

This change resolves both: it feeds the read side to match the write side
(Option A — owners, including regular users, assign their networks to teams they
belong to, with a read view to make that possible), and it promotes `power_user`
to full network reach.

## What Changes

- Add **My Teams** read: `GET /api/v1/teams/mine/`, available to **any**
  authenticated user (including `role=user`), returning `id` + `name` for the
  teams the caller is a member of. The full `GET /api/v1/teams/` list stays
  restricted to `power_user`/`admin`.
- **Constrain owner team-assignment**: a non-privileged owner MAY assign their
  network only to a team they are a **member** of; `power_user`/`admin` may
  assign any network to any team.
- **Power user sees and controls all networks** (Reading 2 — full control):
  `power_user` gains the same network reach as `admin` — list/detail of all
  networks, running lifecycle actions on any network, and **edit/delete** of any
  network — regardless of owner or team.

## Capabilities

### Modified Capabilities

- `network-ownership`: visibility scoping now includes `power_user` (sees all);
  edit/delete extends to `power_user`; team-assignment gains a membership
  constraint for non-privileged owners and explicit `power_user` reach.
- `teams`: adds a membership-scoped **My Teams** read available to any
  authenticated user.

## Impact

- **Backend**: `CampusNetworkViewSet.get_queryset` treats `power_user` like
  `admin` (all networks); object-level edit/delete permission widens to
  `owner | power_user | admin`; team-assignment validation restricts a
  non-privileged owner to their own memberships; new `mine` action on
  `TeamViewSet` (or a lightweight view) with `IsAuthenticated` only.
- **OpenAPI**: new `GET /api/v1/teams/mine/` operation; updated
  permission/visibility descriptions; regenerate `openapi.yaml` (drift test).
- **Tests**: power_user sees/edits/deletes/runs on others' networks; my-teams
  (regular user sees id+name, no leakage, empty when none); owner assign
  constrained to own memberships; power_user/admin assign anything.

### Out of Scope

- A signup/self-service or onboarding change (parked this session).
- Frontend wiring for these endpoints — the SPA affordances (a team picker fed
  by `/teams/mine/`, power_user network views) are follow-up UI work, tracked
  separately from this API-level change.
- Any change to team creation/membership management rules themselves.
