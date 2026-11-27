## Why

Sharing a network with a team currently gives team members read access only:
they can open the network, look at the hosts file, workbook and history, but
every write — editing hosts or workbook values, triggering an action — is
rejected with `403`, and Jenkins mirrors that with a read-only grant on the
network's jobs. That makes teams a viewing feature. The intent of a team is
collaboration: members operate the network together, while deleting it — a
destructive, ownership-level decision — stays with the owner (or a power user /
admin).

## What Changes

- **Team members can operate shared networks.** For a network shared with a
  team they belong to, `user`-role members may update it (`PATCH`/`PUT`), edit
  and clear its hosts/workbook, upload a workbook, and trigger actions. The
  owner, `power_user` and `admin` keep full access.
- **Team members cannot delete or re-share.** `DELETE /api/v1/networks/{id}/`
  and changing the `team` field remain owner / power user / admin only. A
  member attempting either gets `403`.
- **Jenkins mirrors the new rule.** The per-network job matrix grants the
  `team-<id>` group `Job/Read`, `Job/Build` and `Job/Cancel` (previously
  `Job/Read`), so a member can also start/abort the network's jobs from the
  Jenkins UI; the management job that deletes a network stays admin/power-user
  only.
- **The SPA hides what the user cannot do.** The network list shows the
  *Delete* control only to the owner, power users and admins.

## Capabilities

### Modified Capabilities

- `network-ownership`: the edit/delete requirement is split — edit is owner,
  team member, power user or admin; delete is owner, power user or admin; the
  team field is owner / power user / admin.
- `jenkins-trigger-security`: per-network Jenkins jobs grant the team group
  read/build/cancel.
- `spa-networks`: the delete control is shown only when the caller may delete.

## Impact

- **Backend:** `IsOwnerOrTeamMemberOrAdmin` (permissions.py) — team members
  pass for every detail action except `destroy` and except updates that change
  `team`. The workbook/hosts/trigger sub-actions are routed through
  `get_object()` so that gate (and the visibility queryset) actually applies to
  them. `network_template_mgr.xml` ACL rendering gains Build/Cancel for the
  team group. Existing networks need one `operation=acl` re-apply (done by the
  deploy, see tasks).
- **Frontend:** `NetworksPage` gates the Delete button on
  `owner_username === me || isPowerUser`.
- **Tests:** replace `test_team_member_cannot_modify_shared_network` with the
  new matrix (edit OK, trigger OK, delete 403, team change 403); add a frontend
  test for the hidden Delete control.
- No API shape change; no migration.
