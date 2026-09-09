## Context

There is exactly one place where an `ActionHistory` row is created — the trigger
action on `CampusNetworkViewSet` (views.py ~849):

```python
history = ActionHistory(
    action_id=action_obj,
    timestamp=timezone.now(),
    status="Running",
    jenkins_job_build_no=current_build_number,
    category_id=action_obj.action_category,
    campus_network_id=campus_network,
)
history.save()
```

`request.user` is in scope at that point. Nothing else in the codebase
constructs `ActionHistory`; `StatusUpdater` only mutates `status` on existing
rows. So capturing the actor is a single-site change.

The codebase already contains a precedent for the durable-string approach. The
`LifecycleRun` model stores `subject` as a plain string, documented as being
"stored independently of `ActionHistory` so that a run survives the deletion of
its network row… rather than a foreign key for the same reason."

Existing ownership fields resolve the delete question differently in different
places: `CampusNetwork.owner` is `PROTECT` (the users API refuses to delete a
user who owns networks), while `CampusType.created_by` is `SET_NULL` — which
produced the orphan dead-zone fixed by the `network-type-deletion` change.

`AbstractUser.username` is `max_length=150`.

## Goals / Non-Goals

**Goals:**
- Every new run records who triggered it.
- The record survives deletion or rename of the user.
- The History tab (and later the dashboard) can display the actor.

**Non-Goals:**
- Backfilling historic rows, filtering by actor, lifecycle-run attribution, or
  building an audit-log subsystem.

## Decisions

### Decision 1: A durable username string, not a foreign key

**Choice**: `triggered_by_username = models.CharField(max_length=150, blank=True,
default="")`, written once at trigger time.

**Rationale**: A `FK → User` forces a bad choice at user-deletion time:

| | `PROTECT` | `SET_NULL` | durable string |
|---|---|---|---|
| Delete a user who ever triggered a run | blocked forever | allowed | allowed |
| Attribution afterwards | preserved | **lost** | preserved |
| Matches an existing repo pattern | `CampusNetwork.owner` | `CampusType.created_by` | `LifecycleRun.subject` |

`PROTECT` would make any user who once clicked a button permanently
undeletable — a far harsher rule than the existing "owns a network" protection,
and one the users API would have to grow a new blocker for. `SET_NULL` silently
erases exactly the information this change exists to capture: history rows would
lose their actor at the moment the actor leaves.

The string keeps the record intact through both, and matches the reasoning
`LifecycleRun` already documents for surviving deletions. History is an
append-only record of what happened; a snapshot of the username at that instant
is the semantically correct value.

**Consequences (accepted)**:
- A later username change does **not** propagate to old rows. This is correct
  for an audit trail — the row records who acted under that name at that time —
  but it means the displayed name may differ from the user's current name.
- There is no referential integrity: the string may name a user who no longer
  exists. That is the intended trade.
- Filtering by actor would be a string match, not an id lookup. Explicitly out
  of scope, and revisitable by adding a nullable FK alongside the string later
  if a real need appears.

### Decision 2: Empty string for historic rows, rendered as `—`

**Choice**: `default=""` with `blank=True`; no data migration. The SPA renders an
empty value as `—`.

**Rationale**: The actor for pre-existing runs was never recorded and cannot be
recovered — Jenkins triggered these builds via a service account, so its build
metadata names the integration user, not the human. Inventing a value would be
worse than admitting the gap. Rendering `—` rather than an empty cell makes
"unknown" visibly deliberate instead of looking like a rendering bug.

Using `""` rather than `NULL` keeps the column non-nullable and avoids
`None`-vs-`""` branching in the serializer and the SPA.

### Decision 3: Capture at trigger time, from `request.user`

**Choice**: Set the field in the trigger action, at the existing construction
site, from `request.user.username`.

**Rationale**: It is the only write path, and the only moment at which the actor
is known — `StatusUpdater` later mutates the row from a background thread with
no request context, so capturing anywhere else is impossible.

### Decision 4: Denormalised read-only serializer field

**Choice**: Expose `triggered_by_username` directly on `ActionHistorySerializer`
as read-only.

**Rationale**: The serializer already denormalises `action_name`,
`category_name` and `network_name` explicitly so that "consumers can display
context without extra look-ups". This field needs no `source=` indirection at
all — it is a plain column — so it is the cheapest possible addition and it
follows the established shape of the payload.

## Risks / Trade-offs

- **Stale display names after a rename.** Mitigated by intent: this is a
  historical record, not a live reference. Worth a tooltip only if it confuses
  people in practice.
- **A gap in the column for all existing rows.** Every run predating the
  migration shows `—`. Unavoidable, and self-correcting as new runs accumulate.
- **No integrity guarantee.** A username string can name a deleted user. This is
  the accepted cost of durability, and matches `LifecycleRun`.
- **Attribution is only as trustworthy as the session.** The field records the
  authenticated user of the triggering request; it is not a cryptographic
  attestation and should not be treated as one.

## Migration Plan

One Django migration: `AddField` on `ActionHistory` with `default=""`,
`blank=True`, `max_length=150`. Non-nullable with a default, so it applies
without table rewrite concerns on the existing row volume and requires no
backfill step. Deploy order is unconstrained — the serializer field and SPA
column are additive, and an un-migrated database simply has no column, which the
migration adds before the new code reads it.

## Open Questions

- **Should `LifecycleRun` gain the same field?** It has an identical gap for
  network create/delete and type upload. Deliberately excluded to keep this
  change to one model and one write path, but the same argument applies.
- **Should the dashboard show `—` rows differently** (for example, de-emphasised)
  given they are all old? Cosmetic; deferred to the dashboard change.
