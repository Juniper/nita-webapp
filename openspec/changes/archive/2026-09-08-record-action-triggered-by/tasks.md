## 1. Backend — model and migration

- [x] 1.1 Add `triggered_by_username = models.CharField(max_length=150,
  blank=True, default="")` to `ActionHistory` in `ngcn/models.py`
- [x] 1.2 Generate the migration (`AddField`, no data migration) and confirm it
  applies cleanly against a database containing existing history rows

## 2. Backend — capture the actor

- [x] 2.1 In the trigger action of `CampusNetworkViewSet`, pass
  `triggered_by_username=request.user.username` to the `ActionHistory(...)`
  construction
- [x] 2.2 Confirm no other code path creates `ActionHistory` rows (`StatusUpdater`
  only mutates `status` on existing rows)

## 3. Backend — expose the field

- [x] 3.1 Add `triggered_by_username` as a read-only field on
  `ActionHistorySerializer`
- [x] 3.2 Confirm it is returned by both list and retrieve

## 4. Backend — tests

- [x] 4.1 Triggering an action records the requesting user's username
- [x] 4.2 A second user triggering on the same network records their own username
- [x] 4.3 Rows created before the migration serialize as `""`
- [x] 4.4 The recorded value is unchanged after the user is renamed
- [x] 4.5 The recorded value survives deletion of the user, and the deletion is
  not blocked by the presence of history rows

## 5. OpenAPI

- [x] 5.1 Document the new `triggered_by_username` response field; regenerate
  `openapi.yaml`; keep the drift test green

## 6. Frontend — History tab

- [x] 6.1 Add `triggered_by_username` to the `ActionHistory` interface in
  `NetworkDetailPage.tsx`
- [x] 6.2 Add a **Triggered by** column to the History tab table, rendering an
  empty value as `—`
- [x] 6.3 `npm run lint` and `npm run build` green

## 7. Verify

- [x] 7.1 Backend `pytest` suite green
- [ ] 7.2 Manual check: trigger an action, confirm the History tab names the
  triggering user; confirm older rows show `—`

## Verification notes

Backend work is in `ngcn/models.py`, `ngcn/api/views.py`,
`ngcn/api/serializers.py`, migration
`0007_actionhistory_triggered_by_username.py`, and
`tests/test_action_triggered_by.py` (6 tests). **Full suite: 204 passed.**
Frontend `npm run lint` and `npm run build` both green.

**Task 1.2 was verified against a populated database**, not just by generating the
file. A scratch SQLite database was migrated to `0006`, a history row inserted
via raw SQL using only the pre-migration columns (the ORM could not be used, as
the model already declares the new field), then `0007` applied:

```
Applying ngcn.0007_actionhistory_triggered_by_username... OK
legacy row triggered_by_username: ''
```

confirming the empty-string default reaches pre-existing rows as designed.

**Task 2.2** was confirmed by search: `ActionHistory(` / `ActionHistory.objects.create`
appears once in application code (`views.py:846`); every other occurrence is in
tests. `StatusUpdater` only assigns `historyObj.status`.

**Migration scope.** `makemigrations` also wanted to emit four unrelated
`AlterField` operations (`verbose_name` changes on `CampusNetwork.campus_type`,
`CampusNetwork.name`, `CampusType.name`, `Workbook.campus_network_id`). These are
pre-existing model/migration drift, are display-only, and do not alter the
database schema. They were **excluded** so this migration contains only the
`AddField`. The drift remains and will reappear on the next `makemigrations` —
worth cleaning up as its own change.

Task 7.2 requires a running deployment and has not been performed.
