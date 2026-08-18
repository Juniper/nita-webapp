## Context

`CampusNetwork` has `owner = FK(User)` and `team = FK(Team, null=True,
SET_NULL)`. `User.teams` is the reverse M2M of `Team.members`.

Current network access (in `CampusNetworkViewSet`):
- `get_queryset`: `admin` → all; everyone else →
  `Q(owner=user) | Q(team__members=user)`.
- edit/delete (object permission): owner or `admin`.
- team assignment: `PATCH team=<id>` allowed for owner or `admin`; no check that
  the owner belongs to the target team.

Current team read access (in `TeamViewSet`): list/detail gated by
`IsPowerUserOrAdmin`; `power_user` sees only teams they created, `admin` all,
`role=user` → `403`. `GET /api/v1/auth/me/` returns `teams` as a list of IDs
only.

The contradiction: the write path (owner assigns team) has no matching read path
for `role=user`, and `power_user` — the sharing curator — has no broader network
reach than a plain user.

## Goals / Non-Goals

**Goals:**
- Any authenticated user can discover the teams they belong to (id + name) to
  make a sensible team assignment.
- A non-privileged owner can only share into teams they are a member of.
- `power_user` has full network reach (view, run, edit, delete) like `admin`.

**Non-Goals:**
- Changing team creation/membership rules, onboarding, or the SPA UI.
- Exposing the full team roster to regular users (only their own memberships).

## Decisions

### Decision 1: Power user gains full network reach (Reading 2)

**Choice**: Treat `power_user` like `admin` for networks. `get_queryset` returns
all networks when `role in {admin, power_user}`; object-level edit/delete permits
`owner OR role in {power_user, admin}`. Because lifecycle actions, history, and
streaming key off network visibility/access, `power_user` inherits "run on any
network" automatically.

**Rationale**: `power_user` is the role that organises sharing (teams,
membership); it should see and operate on the networks it organises. The user
explicitly chose full control over a view-and-run-only variant.

**Consequence (accepted)**: `power_user` is now a network super-admin (can delete
any network). This is a deliberate blast-radius increase; the alternative
(view + run only, edit/delete owner-locked) was considered and rejected by the
requester.

### Decision 2: `GET /api/v1/teams/mine/` — membership-scoped, any authenticated user

**Choice**: Add a `mine` read returning `[{id, name}]` for teams the caller is a
member of (`request.user.teams.all()`), permission `IsAuthenticated` only. The
full `GET /api/v1/teams/` stays `IsPowerUserOrAdmin`.

**Rationale**: This unlocks exactly the read a regular owner needs to pick a
valid team, without exposing the full roster or team internals. Membership-scoped
(not creator-scoped) because the use-case is "teams I can share into."

**Alternatives considered**:
- Add team **names** to `GET /auth/me/` — rejected: overloads the identity
  endpoint and still returns a flat list rather than a purpose-built resource.
- Relax the full `/teams/` list for regular users — rejected: leaks teams they
  are not part of.

### Decision 3: Constrain non-privileged owner assignment to their memberships

**Choice**: On `PATCH /api/v1/networks/{id}/` with a `team`, if the requester is
the owner but not `power_user`/`admin`, the target team MUST be one the requester
is a member of; otherwise reject (`400`). `power_user`/`admin` may assign any
network to any team. `team=null` (unassign) remains allowed for owner/
power_user/admin.

**Rationale**: Prevents a regular user from sharing a network into a team they
cannot see or belong to. Keeps the write path coherent with the new read path
(`/teams/mine/`).

## Risks / Trade-offs

- **Power_user blast radius** (delete any network) → accepted per Reading 2;
  covered by tests asserting the widened capability is intentional.
- **My-teams leakage** → strictly `request.user.teams`; test asserts other teams
  never appear and that `role=user` is allowed.
- **Assignment constraint false-blocks** → only applies to non-privileged
  owners; power_user/admin bypass; unassign always allowed.
- **Downstream visibility coupling** → lifecycle/history/streaming rely on the
  same network access; verify power_user reach flows through consistently.

## Migration Plan

No schema changes. Behavioural widening (power_user) + one additive endpoint
(`/teams/mine/`) + one validation. Regenerate `openapi.yaml`; keep the drift test
green. No data migration.

## Open Questions

- Should `/teams/mine/` for a `power_user` include teams they **created** but are
  not a member of? Proposed: no — strictly membership, since the endpoint's job
  is "teams I can share into" (power_users already have the full `/teams/` list).
- Should unassigning (`team=null`) by a non-owner power_user be audited? Out of
  scope here; note for a future audit-log change.
