## Context

Two viewsets that describe the same underlying data disagree about who may see
it.

`CampusNetworkViewSet.get_queryset()` (views.py ~478):

```python
qs = CampusNetwork.objects.all()
user = self.request.user
if getattr(user, "role", None) not in (User.ROLE_ADMIN, User.ROLE_POWER_USER):
    qs = qs.filter(Q(owner=user) | Q(team__members=user)).distinct()
```

`ActionHistoryViewSet.get_queryset()` (views.py ~947):

```python
qs = super().get_queryset()      # ActionHistory.objects.all().order_by("-timestamp")
# optional ?campus_network_id= / ?action_category_id= filters only
```

`ActionHistory` reaches its network through `campus_network_id`
(`FK → CampusNetwork`, `CASCADE`), so the visibility question is fully
determined by the network. Nothing about a run is independently owned.

The detail routes all resolve through `self.get_object()`, which DRF derives
from `get_queryset()`:

```
console        views.py:969   history = self.get_object()
stream         views.py:1000  history = self.get_object()
robot-summary  views.py:1029  history = self.get_object()
```

so a single queryset fix closes the list endpoint *and* all three detail
endpoints, including the two that return Jenkins console output.

## Goals / Non-Goals

**Goals:**
- Action history is visible exactly when its network is visible.
- The rule is expressed once and is testable as "these two viewsets agree".
- Detail routes (including console and stream) are closed by the same change.

**Non-Goals:**
- Re-litigating power-user reach.
- Scoping `lifecycle-runs`, `actions`, or `action-categories`.
- Any change to permission classes, serializers, routes or the SPA.

## Decisions

### Decision 1: Reuse the network visibility rule verbatim

**Choice**: `role=admin` / `role=power_user` see all history;
everyone else is filtered to
`Q(campus_network_id__owner=user) | Q(campus_network_id__team__members=user)`,
with `.distinct()`.

**Rationale**: Action history has no independent ownership, so any rule other
than "inherit the network's" would be inventing a second, divergent notion of
who owns a run — which is exactly the bug being fixed. Mirroring the network
rule also makes the invariant expressible as a test: for any user, the set of
networks appearing in their action history is a subset of the networks returned
by `GET /api/v1/networks/`.

**Note**: `.distinct()` is required. `team__members` is a many-to-many join, so
a user in a team with several members would otherwise get duplicate rows — the
same reason `CampusNetworkViewSet` already calls it.

### Decision 2: Out-of-scope detail lookups return 404, not 403

**Choice**: Fix `get_queryset()` and let `get_object()` raise `Http404`
naturally. Do not add an object-level permission class returning 403.

**Rationale**: This matches `GET /api/v1/networks/{id}/`, which already returns
404 for a network the caller cannot see (an existing scenario in the
`network-ownership` spec). It also avoids leaking existence: a 403 confirms the
id is real, a 404 does not. And it requires no new permission class — the fix is
one filter.

### Decision 3: Filters compose with the scope

**Choice**: Apply the visibility filter first, then the `campus_network_id` /
`action_category_id` query parameters on top.

**Rationale**: The filters are conveniences for narrowing a result set, not an
authorization mechanism. Passing another user's network id must produce an empty
list — not an error, and certainly not their data. Ordering the filter first
makes that automatic.

### Decision 4: Power users keep global reach

**Choice**: `power_user` sees all action history, as they see all networks.

**Rationale**: Consistency with networks is the whole point of Decision 1;
special-casing history would reintroduce drift. This does mean a power user's
future dashboard feed is the noisiest one — accepted, and adjustable later
without touching this rule.

## Risks / Trade-offs

- **Join cost.** The filter adds a join to `CampusNetwork` (and, for team
  membership, to the team members table) on a list endpoint that is about to be
  called on every dashboard load. `campus_network_id` is already an indexed FK
  and the result set is paginated at 50, so this is expected to be negligible;
  worth a look if history volume grows.
- **Behaviour change for API clients.** Any script relying on the unscoped list
  under a `role=user` account will see fewer rows. Given the endpoint is
  read-only and the SPA never used it unfiltered, the blast radius is limited to
  ad-hoc scripts.
- **Deleted networks.** `ActionHistory.campus_network_id` is `CASCADE`, so a
  deleted network takes its history with it; there is no orphan case where a row
  survives with no network to derive visibility from. (`LifecycleRun` was
  deliberately built the other way, storing `subject` as a plain string so runs
  outlive their network — a reminder that the two models have different
  lifetimes.)
- **Not a complete audit of read paths.** This change fixes action history only.
  `lifecycle-runs` is untouched (see Open Questions).

## Migration Plan

No schema or data migration. A single queryset change plus tests, then
regenerate `openapi.yaml` for the documented 404s.

## Open Questions

- **Does `/api/v1/lifecycle-runs/` need the same treatment?** It is a
  `viewsets.ViewSet` that builds its rows from Jenkins job data rather than a
  Django queryset, and it reports network create/delete/type-load runs by
  `subject` name. It may expose other users' network names by the same logic.
  Deliberately **not** included here — this change stays a one-line fix with a
  clean test story. Worth raising as its own change.
- **Should the invariant be enforced structurally?** A shared helper
  (`visible_networks(user)`) used by both viewsets would make drift impossible,
  rather than merely tested against. Cheap, but it touches
  `CampusNetworkViewSet` too, so it is left out of a security fix that should
  stay minimal and easy to review.
