## Why

`ActionHistoryViewSet.get_queryset()` applies **no visibility scoping**. It
returns `ActionHistory.objects.all()` to every authenticated user, narrowed only
by the optional `?campus_network_id=` and `?action_category_id=` filters:

```python
def get_queryset(self):
    qs = super().get_queryset()          # ActionHistory.objects.all()
    campus_network_id = self.request.query_params.get("campus_network_id")
    if campus_network_id:
        qs = qs.filter(campus_network_id=campus_network_id)
    ...
    return qs                             # no owner/team filter
```

This diverges from `CampusNetworkViewSet.get_queryset()`, which restricts a
`role=user` to networks they own or share via a team. The result is that action
history is a side channel around network visibility scoping:

- `GET /api/v1/action-history/` enumerates **every** run in the system —
  `network_name`, `action_name`, `category_name`, `jenkins_job_name`, status and
  timestamp — for networks the caller cannot otherwise see.
- `?campus_network_id=<someone else's network>` returns that network's runs.
- Because `get_object()` derives from `get_queryset()`, the detail routes are
  affected too: `/{id}/`, `/{id}/console/`, `/{id}/stream/` and
  `/{id}/robot-summary/` all resolve for out-of-scope entries. `console` and
  `stream` return **Jenkins console output**, which is the most sensitive of
  these — build logs for another user's network.

The gap is currently latent in the UI (the SPA only ever calls the list endpoint
with the `campus_network_id` of a network the user is already viewing), but it
is directly reachable by any authenticated client. It also blocks the planned
dashboard recent-activity feed, which necessarily calls the list endpoint
*unfiltered*.

## What Changes

- **`ActionHistoryViewSet` scopes its queryset by network visibility**, applying
  the same rule already used by `CampusNetworkViewSet`:
  - `role=admin` or `role=power_user` see all entries;
  - `role=user` sees only entries whose `campus_network_id` they own
    (`campus_network_id__owner=request.user`) or share through a team
    (`campus_network_id__team__members=request.user`).
- **Detail routes inherit the scoping for free.** `get_object()` resolves from
  `get_queryset()`, so `/{id}/`, `/{id}/console/`, `/{id}/stream/` and
  `/{id}/robot-summary/` return **404** for an out-of-scope entry, matching the
  existing behaviour of `GET /api/v1/networks/{id}/` for an invisible network.
- **Filters compose with the scope rather than bypassing it.** Passing
  `?campus_network_id=<invisible network>` yields an empty result set, not that
  network's history.

## Capabilities

### Modified Capabilities

- `actions`: the action-history list endpoint is scoped to networks visible to
  the requesting user; out-of-scope detail lookups return 404.

### Added Capabilities

- `network-ownership`: a new requirement stating that action-history visibility
  derives from network visibility, so the two rules cannot drift apart.

## Impact

- **Backend**: `ActionHistoryViewSet.get_queryset()` gains the owner/team filter
  (with `.distinct()`, since `team__members` is a many-to-many join). No change
  to permissions classes, serializers or routes.
- **Frontend**: none. The SPA already filters by a network the user can see, so
  its results are unchanged.
- **OpenAPI**: document 404 on the action-history detail routes for entries
  outside the caller's scope; regenerate `openapi.yaml` and keep the drift test
  green.
- **Tests**: regular user cannot list another user's history; cannot bypass via
  `?campus_network_id=`; receives 404 on retrieve/console/stream/robot-summary
  for an out-of-scope entry; still sees history for owned and team-shared
  networks; power user and admin continue to see everything.

### Out of Scope

- **`LifecycleRunViewSet`** (`/api/v1/lifecycle-runs/`) is a plain
  `viewsets.ViewSet` that derives its rows from Jenkins rather than a queryset,
  so it is not fixed by this change. Whether it needs equivalent scoping is
  recorded as an open question in `design.md`.
- `GET /api/v1/actions/` and `/api/v1/action-categories/` remain readable by any
  authenticated user; they describe a network **type**, not a user's data.
- Changing power-user reach. Power users see all networks today; mirroring that
  for history keeps the two consistent. Narrowing it is a separate discussion.
- The generic Jenkins stream `/api/v1/jenkins/jobs/{job}/{build}/stream/`, which
  is keyed by job name rather than by an `ActionHistory` row.
