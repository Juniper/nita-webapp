## Context

ActionHistory rows are created in `Running` state when an action trigger succeeds, and the UI simply displays whatever the API returns. In the current deployment, Jenkins completes builds but the persisted ActionHistory rows remain `Running` because the status updater cannot resolve completed builds reliably.

The root cause identified during exploration is a base URL mismatch. The status updater constructs Jenkins requests against `http://jenkins:8080`, while the deployed Jenkins instance is served under the `/jenkins` context path. That mismatch makes build lookups fail with `job[...] number[...] does not exist`, so no terminal status is written back to the database.

This change affects backend Jenkins synchronization paths only. The frontend is not expected to change, since it already reflects the API state.

## Goals / Non-Goals

**Goals:**
- Make ActionHistory status synchronization resolve finished Jenkins builds correctly.
- Ensure terminal Jenkins results are persisted back to ActionHistory rows.
- Remove the URL drift that caused the updater to look in the wrong Jenkins location.
- Keep existing trigger, polling, and UI contracts stable.

**Non-Goals:**
- Redesigning the status polling model or replacing the background updater.
- Changing the ActionHistory API shape or the history table UI.
- Introducing a new storage model for job state.
- Fixing unrelated Jenkins integration paths unless they share the same URL source.

## Decisions

1. **Use the canonical prefixed internal Jenkins base URL for status synchronization.**
   The updater should target the same internal Jenkins base URL convention used by the rest of the backend: the Jenkins service under `/jenkins`. This is the smallest correction that fixes the lookup failure without changing the polling logic itself.

   Alternative considered: keep the updater on the root Jenkins URL and compensate by adding aliases or redirects. That would preserve the mismatch and rely on server-side behavior that is already inconsistent in production.

2. **Preserve the existing background updater architecture.**
   The current threading and periodic polling model already exists and is validated by tests. The bug is not that the updater is missing; it is that it is querying the wrong endpoint. Keeping the service shape stable minimizes regression risk and makes the fix narrowly targeted.

   Alternative considered: derive terminal status live in the ActionHistory API response. That would avoid stale persistence, but it would be a broader behavior change and would not address existing rows or the background sync contract.

3. **Align related backend Jenkins URL constructors to the same source of truth.**
   The status updater is the immediate failure point, but other legacy helpers still build Jenkins URLs independently. Reusing one canonical URL source reduces the chance that this bug reappears in adjacent code paths.

   Alternative considered: fix only `statusupdater.py`. That would unblock the immediate issue, but leaves the repo with multiple URL construction patterns that can drift again.

4. **Validate with real Jenkins result states rather than only unit tests.**
   Because the failure mode is a production deployment mismatch, the change should be checked against actual completed builds and the live ActionHistory API to confirm terminal status updates propagate as expected.

## Risks / Trade-offs

- [Broad URL refactor may touch more callers than expected] -> Keep the first change minimal and reuse shared Jenkins configuration where possible; only expand scope if a caller is proven to be inconsistent.
- [Updater thread behavior could mask the real issue if it is not running] -> Confirm the updater service still starts and only change URL handling unless evidence shows a lifecycle defect.
- [Existing `Running` rows may take one polling interval to recover] -> Communicate that the fix is asynchronous; the next updater cycle should update rows once lookups succeed.
- [Different Jenkins job types may map statuses differently] -> Preserve the existing `buildStatus.title()` mapping so the change does not alter established status labels beyond making them reachable.

## Migration Plan

1. Update the ActionHistory status updater to use the canonical prefixed Jenkins base URL.
2. Align other backend Jenkins callers that still construct a root-path URL.
3. Validate against at least one completed success and one completed failure build.
4. Confirm the ActionHistory API changes from `Running` to terminal states after the updater cycle.
5. Roll back by restoring the prior Jenkins base URL construction if the updater begins failing to resolve builds for any reason.

## Open Questions

- Should all backend Jenkins helpers be unified in the same change, or only the ones involved in ActionHistory synchronization?
- Is there value in adding a lightweight health check or alert when the updater sees repeated Jenkins lookup failures?
- Do we want the API to optionally expose live Jenkins state as a fallback, or is persisted status sufficient once the updater is fixed?
