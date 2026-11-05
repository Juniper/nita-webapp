## 1. Backend permission

- [x] 1.1 `IsOwnerOrTeamMemberOrAdmin`: team members pass for every detail action except `destroy`, and except `update`/`partial_update` bodies that change `team`; owner / power user / admin unchanged
- [x] 1.3 Every network sub-action (`workbook`, `workbook/upload|save|clear|download`, `trigger`) now calls `self.get_object()` so queryset scoping and the object permission apply (previously they bypassed both); `workbook/save` reads `request.data`
- [x] 1.2 Tests in `test_user_management.py`: team member PATCH description → 200, `workbook/save` → 200, trigger → 202 with `triggered_by_username`, DELETE → 403, PATCH `team` → 403; non-member → 404 (replaces `test_team_member_cannot_modify_shared_network`)

## 2. Jenkins mirror

- [x] 2.1 `network_template_mgr.xml` `acl_property_xml` (create and `acl` blocks): team group gets `Job/Read`, `Job/Build`, `Job/Cancel`
- [x] 2.2 Amend the open `gate-jenkins-behind-webapp-session` requirement *Per-network Jenkins jobs mirror the webapp access model* (team read → read/build/cancel; team-member build scenario)
- [x] 2.3 After deploy, re-apply `operation=acl` to every existing network with a team

## 3. SPA

- [x] 3.1 `NetworksPage`: render Delete only for `owner_username === user.username || isPowerUser`
- [x] 3.2 Frontend test: Delete hidden for a non-owner `user`, shown for owner and for `power_user`

## 4. Validation

- [x] 4.1 `pytest`, `vitest`, lint green; `openspec validate let-team-members-operate-shared-networks --strict` passes
- [x] 4.2 Live on Kubernetes: member edits hosts/workbook and triggers a shared network's action (Jenkins build *Started by user <member>*); member DELETE → 403 and PATCH `team` → 403; member can build/abort the job in the Jenkins UI; non-member unchanged (404)
- [x] 4.3 Update `README.md` release notes
