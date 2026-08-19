## 1. Immediate fix: unstick ActionHistory status updates

- [x] 1.1 Update the ActionHistory updater Jenkins base URL construction to use the canonical internal prefixed path (`/jenkins`).
- [x] 1.2 Verify updater lookups for known completed builds return terminal Jenkins results instead of `job does not exist`.
- [x] 1.3 Confirm `Running` ActionHistory rows transition to `Success`/`Failed` after one polling interval.

## 2. Consistency cleanup: remove URL drift risk

- [x] 2.1 Inventory backend modules that construct Jenkins base URLs directly.
- [x] 2.2 Refactor those modules to consume a single shared Jenkins base URL source.
- [x] 2.3 Add/update unit tests that would fail if the `/jenkins` prefix is dropped in synchronization paths.

## 3. Risk and validation checklist

- [x] 3.1 Regression risk: ensure action trigger submission still succeeds after URL unification.
- [x] 3.2 Regression risk: ensure network create/delete lifecycle Jenkins interactions still work.
- [x] 3.3 Data risk: ensure status transitions only mutate rows currently in `Running` state.
- [x] 3.4 Runtime risk: ensure updater thread remains singleton-per-process and does not spawn duplicates.
- [x] 3.5 Verification: compare `/api/v1/action-history/?campus_network_id=<id>` statuses against Jenkins build API (`result`, `building`) for at least one success and one failure case.
