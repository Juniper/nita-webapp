## Context

`IsOwnerOrTeamMemberOrAdmin.has_object_permission` is the single gate for every
detail action on `CampusNetworkViewSet` (retrieve, update, hosts/workbook
actions, trigger, destroy). Today it returns `True` for a team member only when
`request.method` is safe. Jenkins' per-network `AuthorizationMatrixProperty`
(rendered by `network_template_mgr`) grants the `team-<id>` group `Job/Read`
only. The `gate-jenkins-behind-webapp-session` change introduced both of those
Jenkins pieces and is still open; this change narrows one rule on top of it.

## Goals / Non-Goals

**Goals**

- A `user`-role team member can do everything on a shared network that the
  owner can, except delete it or change who it is shared with.
- Jenkins enforces the same thing for the network's jobs.
- One decision point in the backend; the SPA only hides controls, it does not
  decide.

**Non-Goals**

- Per-member roles inside a team (e.g. "team admin"). A team is flat.
- Letting team members delete. Delete removes the project folder and the
  Jenkins jobs for everyone; it stays with the owner / power user / admin.
- Changing power user / admin semantics.

## Decisions

### Decision 1: Decide by view action, not HTTP method

**Choice:** In `IsOwnerOrTeamMemberOrAdmin`, a team member is allowed unless
`view.action == "destroy"` or the request body sets `team` to a different value
(the "re-share" case). Owner / power user / admin are unchanged.

**Rationale:** `workbook/clear` is an HTTP `DELETE` but is an *edit* (it empties
the workbook so values can be re-entered); `trigger` is a `POST`. Method-based
rules cannot express "edit yes, delete no". The view action is the stable,
already-named concept. Checking `team` in the request keeps "who sees this
network" an ownership decision without adding a second permission class.

**Rejected:** a separate `IsOwnerOrAdmin` only on `destroy` (two classes to
keep in sync and `get_permissions` branching); making `team` read-only for
non-owners in the serializer (returns 400 for what is really a permission
denial).

### Decision 1b: Sub-actions go through `get_object()`

**Choice:** `get_workbook`, `upload_workbook`, `save_workbook`,
`clear_workbook`, `download_workbook` and `trigger` call `self.get_object()`
first (and `trigger` uses the returned instance instead of a raw
`CampusNetwork.objects.get(pk=pk)`).

**Rationale:** Found while verifying: those actions looked up the network by
`pk` directly, so neither the role-scoped queryset nor the object permission
ran — any authenticated user could read/edit another user's workbook or
trigger their actions by id. With one gate in `has_object_permission` the
sub-actions must use it, otherwise the team rule is only half enforced.

### Decision 2: Team group gets Build/Cancel in Jenkins

**Choice:** `acl_property_xml` in `network_template_mgr` grants the team group
`Job/Read`, `Job/Build`, `Job/Cancel` — the same set as the owner.

**Rationale:** A member who may trigger from the webapp must be able to trigger
in Jenkins too (the webapp acts as that user, with their groups). Network
deletion is not a Jenkins permission on the per-network jobs at all — it is a
`network_template_mgr` build, which regular users cannot reach — so the matrix
needs no distinction between owner and member.

**Migration:** existing per-network jobs carry the old read-only team grant.
The deploy re-applies `operation=acl` for every network with a team (same
helper the team-change hook uses); new networks are correct on creation.

### Decision 3: The SPA hides Delete, nothing else

**Choice:** `NetworksPage` renders the Delete button only when
`n.owner_username === user.username || isPowerUser`. Hosts/workbook/trigger
controls are already shown to everyone who can see the network, and now work.

**Rationale:** The backend is authoritative; hiding Delete just avoids a
guaranteed 403. The list already has `owner_username`, so no new field.

## Risks / Trade-offs

- A member can edit a network another member is also editing; that is already
  true for owner + power user and the workbook save is last-write-wins. Out of
  scope.
- A member could trigger a destructive *action* (e.g. a teardown playbook) of
  the network type. That is the point of operating the network together; the
  owner controls sharing via the team assignment.
