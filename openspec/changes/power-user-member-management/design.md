## Context

`UserViewSet` uses `permission_classes = [IsAuthenticated, IsAdminRole]` for every
action except `directory` (which is `IsPowerUserOrAdmin`). Teams are scoped by
`Team.created_by`; membership is the `Team.members` M2M (reverse `User.teams`).
The `user-roles` invariant **"Role Assignment Restricted to Admin"** holds, and
`user-management` carries the last-active-admin guard and self-action guards.

Onboarding today: an admin creates accounts (or self-registration is enabled),
and a power user adds existing users to their teams. What a power user cannot do
is help those members with credentials, or view their profile — both require an
admin.

## Goals / Non-Goals

**Goals:**
- A power user can reset the password of, and view, a `role=user` member of a
  team they created — and nothing more.
- Preserve the role ladder and every escalation guard.

**Non-Goals:**
- Role changes, account create/deactivate/delete by power users.
- Team-visibility widening; a global user list for power users.
- Hard membership isolation (constraining who a power user can add to a team) —
  noted as future hardening (see Decision 5).

## Decisions

### Decision 1: One authority predicate, applied to exactly two actions

**Choice**: Add
`_manages_member(requester, target) = requester.role == power_user AND
target.role == user AND Team.objects.filter(created_by=requester, members=target)
.exists()`. Apply it to the **`set_password`** and **`retrieve`** actions
(admins remain allowed by role). No other action changes.

**Rationale**: Minimal surface. The predicate encodes all three escalation guards
at once — a `role=user` target can never be an admin or another power user; no
role field is touched; and authority is scoped to the requester's own teams.

### Decision 2: Password reset is the only account action delegated

**Choice**: Delegate **password reset** only. Deactivate/delete stay admin-only;
create and role-change stay admin-only.

**Rationale**: Reset is the least destructive account action — the member simply
gets new credentials and keeps all their access. Its cross-team effect is benign
(the user re-authenticates everywhere). Deactivate/delete carry a cross-team
"shared member" blast radius (deactivating a user who is also in another power
user's or admin's team kills that access too), so account lifecycle stays with
admins. Create/role-change stay admin-only to preserve the ladder.

### Decision 3: Scoped retrieve, not a scoped list

**Choice**: Give power users `GET /api/v1/users/{id}/` for members they manage,
but **not** the full `GET /api/v1/users/` list (stays admin-only). Power users
already discover members via `/api/v1/users/directory/` and their team member
lists.

**Rationale**: The reset UI needs to show *who* is being reset, but exposing the
whole admin roster to power users is unnecessary and leakier. The scoped retrieve
reuses `UserSerializer` (id, username, email, role, is_active), read-only.

### Decision 4: UX on the Teams screen; the admin Users screen is untouched

**Choice**: The reset action appears **per-member on `/teams`** (power_user/admin),
reusing the existing `SetPasswordDialog`. The `/users` admin screen and its guards
are unchanged.

**Rationale**: A team lead already works on the Teams screen; that is where
resetting *their* member's password belongs. Keeps the full user-admin surface
admin-only (recommendation Q2, confirmed).

### Decision 5: Membership scoping is intentionally soft — bound it with an audit log

**Choice**: Keep the team-membership clause in the predicate, but treat it as a
**soft** boundary and record an **audit-log entry** on every power-user password
reset (actor, target, timestamp). The scoped retrieve returns the full
`UserSerializer` read-only (resolves the profile-shape question — the scoping, not
field-narrowing, is the control).

**Rationale (the porousness finding)**: A power user can already add **any**
`role=user` (by id) to a team they created via `POST /teams/{id}/members/`. So
"member of a team I created" is freely satisfiable — a power user could add a
target, reset, and remove them. The membership clause therefore expresses intent
and keeps the UI honest (the action only surfaces for current members), but the
**effective reach is "reset any `role=user`'s password."** That is acceptable
here because the action is non-destructive (new credentials, no access change) and
hard-capped at `role=user` (never power users or admins) — but it MUST be
observable, hence the audit log.

**Alternatives**:
- *Simplify* the predicate to just `target.role == user` (drop the membership
  clause) — honest and simpler, but abandons the "team lead" framing.
- *Make scoping real* by constraining who a power user may add to a team — true
  isolation, but it changes the `teams` capability and is out of scope here. This
  is the recorded **future hardening** path if isolation is ever required.

## Risks / Trade-offs

- **Scoping bug lets a power user reset someone they shouldn't** → single predicate
  + tests for non-member, elevated-target, and another power user's team member.
- **An admin who is also a power user's team member** → the predicate's
  `target.role == user` clause blocks resetting them. ✓
- **Reset as a griefing vector** (a power user repeatedly resets a member) → low
  impact; the target is a `role=user`; an admin can intervene; **audited**.
- **Membership gate is porous** (a power user can add any `role=user` to their
  team, so effective reach = any regular user) → accepted for this change because
  reset is non-destructive and `role=user`-capped; mitigated by the audit log and
  recorded as future hardening (Decision 5). Never reaches power users or admins.
- **`user-roles` invariant** → untouched: no role assignment path is added, so
  "Role Assignment Restricted to Admin" still holds.

## Migration Plan

No schema or model changes. Object-permission widening on two actions plus one
frontend affordance. Regenerate `openapi.yaml`; keep the drift test green. No data
migration.

## Open Questions

_Both prior open questions are now resolved (see Decisions 3 and 5):_
- **Retrieve shape** → full `UserSerializer` read-only.
- **Membership scope** → membership in any team the requester created qualifies;
  the boundary is intentionally soft and covered by an audit log, with real
  isolation deferred to a future `teams`-capability change.
