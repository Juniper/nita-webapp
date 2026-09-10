## Why

`ActionHistory` records **what** ran and **where**, but never **who** ran it:

```
ActionHistory
  ├── timestamp                 DateTimeField
  ├── status                    CharField
  ├── jenkins_job_build_no      IntegerField
  ├── action_id            FK → Action
  ├── campus_network_id    FK → CampusNetwork
  └── category_id          FK → ActionCategory
                                  (no user reference)
```

Networks are shared — a network has an `owner` and an optional `team` whose
members can all trigger actions on it. So on any shared network the history is a
list of events with no actor. "Who deployed this?" and "who aborted that run?"
are unanswerable from the data, and the History tab on the network detail page
cannot show it because it does not exist.

This also blocks the planned dashboard recent-activity feed, whose whole value on
a team network is telling colleagues' runs apart from your own.

## What Changes

- **`ActionHistory` gains `triggered_by_username`**, a `CharField(max_length=150,
  blank=True, default="")` holding the username of the user who triggered the
  run, captured at trigger time. It is a **durable string snapshot, not a foreign
  key** — see `design.md` for the rationale.
- **The trigger endpoint populates it.** `POST /api/v1/networks/{id}/trigger/
  {action_id}/` sets `triggered_by_username=request.user.username` on the
  `ActionHistory` row it creates.
- **The API exposes it.** `ActionHistorySerializer` includes
  `triggered_by_username` as a read-only field, alongside the existing
  denormalised `action_name` / `category_name` / `network_name` fields.
- **Existing rows keep an empty value.** Historic runs predate the field and have
  no recoverable actor; they store `""` and SHALL be rendered as `—` rather than
  as a blank cell, so "unknown" is visibly distinct from "not loaded".
- **The History tab shows a "Triggered by" column** on the network detail page.

## Capabilities

### Modified Capabilities

- `actions`: action-history entries record and expose the triggering user's
  username; the trigger endpoint captures it.
- `spa-networks`: the History tab displays who triggered each run.

## Impact

- **Backend**: one field on `ActionHistory` in `models.py`; one generated
  migration (`AddField`, `default=""`, no data migration); one extra kwarg at the
  single `ActionHistory(...)` construction site in the trigger action of
  `CampusNetworkViewSet`; one field on `ActionHistorySerializer`.
- **Frontend**: a column in the History tab table on `NetworkDetailPage`, and the
  `ActionHistory` TypeScript interface gains the field.
- **OpenAPI**: the new response field; regenerate `openapi.yaml` and keep the
  drift test green.
- **Tests**: triggering records the requesting user's username; the field is
  returned by list and retrieve; pre-existing rows serialize as `""`; the value
  is unaffected by a later username change or by deleting the user.

### Out of Scope

- **Backfilling historic rows.** The actor was never recorded and cannot be
  recovered from Jenkins reliably; `""` is the honest value.
- **Filtering history by user** (`?triggered_by=`). No consumer needs it yet, and
  a string column makes it a fuzzy match rather than an id lookup.
- **Attribution for lifecycle runs** (network create/delete, type upload). The
  `LifecycleRun` model has the same gap, but it is a separate model with a
  separate write path.
- **A general audit-log facility.** This is one field on one model, not an audit
  subsystem.
