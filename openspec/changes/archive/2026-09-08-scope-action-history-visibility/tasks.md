## 1. Backend — scope the queryset

- [x] 1.1 In `ActionHistoryViewSet.get_queryset()`, apply the network visibility
  filter before the query-parameter filters: admins and power users see all;
  otherwise filter on
  `Q(campus_network_id__owner=user) | Q(campus_network_id__team__members=user)`
- [x] 1.2 Add `.distinct()` to the filtered branch (many-to-many team join)
- [x] 1.3 Confirm the existing `?campus_network_id=` and `?action_category_id=`
  filters still apply on top of the scoped queryset

## 2. Backend — tests

- [x] 2.1 A `role=user` listing `/api/v1/action-history/` sees only entries for
  networks they own or share via a team
- [x] 2.2 A `role=user` passing `?campus_network_id=<another user's network>`
  receives an empty result set (not 403, not that network's rows)
- [x] 2.3 A `role=user` receives 404 on `/{id}/`, `/{id}/console/`,
  `/{id}/stream/` and `/{id}/robot-summary/` for an out-of-scope entry
- [x] 2.4 A team member sees history for a team-shared network they do not own
- [x] 2.5 `power_user` and `admin` still see all entries
- [x] 2.6 Invariant test: every `network_name` in a user's action-history
  response also appears in that user's `GET /api/v1/networks/` response
- [x] 2.7 No duplicate rows are returned for a user in a multi-member team

## 3. OpenAPI

- [x] 3.1 Document the 404 response on the action-history detail routes for
  entries outside the caller's scope; regenerate `openapi.yaml`; keep the drift
  test green

## 4. Verify

- [x] 4.1 Backend `pytest` suite green
- [ ] 4.2 Manual check: as a `role=user`, `GET /api/v1/action-history/` returns
  only that user's networks; the History tab on an owned network is unchanged

## Verification notes

Work is in `tests/test_action_history_scoping.py` (13 tests) plus the queryset
change and schema annotations in `ngcn/api/views.py`.

**Full suite: 198 passed** (185 before this change, 13 added). The OpenAPI drift
test is green against the regenerated `openapi.yaml`. The one remaining schema
generation error (`logout_view`: unable to guess serializer) is pre-existing and
unrelated to this change.

**The tests were confirmed to fail without the fix.** Reverting only the
`get_queryset` change makes 7 of the 13 fail — most importantly all three
sub-routes returned **200** rather than 404 for another user's network:

```
FAILED ...::test_out_of_scope_subroutes_return_404[console]        assert 200 == 404
FAILED ...::test_out_of_scope_subroutes_return_404[stream]         assert 200 == 404
FAILED ...::test_out_of_scope_subroutes_return_404[robot-summary]  assert 200 == 404
FAILED ...::test_user_sees_history_only_for_own_networks
FAILED ...::test_network_filter_cannot_widen_scope
FAILED ...::test_history_networks_are_subset_of_visible_networks
FAILED ...::test_out_of_scope_retrieve_returns_404
```

confirming the Jenkins console-output disclosure described in `proposal.md` was
reachable in practice, not merely theoretical.

Two tests beyond the task list were added: one pinning that `?action_category_id=`
still narrows correctly within the scoped queryset (task 1.3), and one confirming
an owner can still retrieve their own entry — so the change is shown to restrict
without over-restricting.

Task 4.2 requires a running deployment and has not been performed.
