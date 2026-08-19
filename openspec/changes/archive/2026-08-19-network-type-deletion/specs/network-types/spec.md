## MODIFIED Requirements

### Requirement: Delete a Network Type
The system SHALL remove a network type via `DELETE /api/v1/network-types/{id}/`,
restricted to users with `role=power_user` or `role=admin` regardless of who
created the type (including types whose `created_by` is `NULL`). A regular `user`
SHALL receive `403`.

Deletion SHALL be refused with `409 Conflict` while any `CampusNetwork` still
references the type; the response SHALL name the blocking networks. This applies
to `admin` requesters as well as `power_user`. When deletion proceeds, the
`Action` rows belonging to the type SHALL be removed with it.

#### Scenario: Successful delete
- GIVEN a network type that no network references
- WHEN `DELETE /api/v1/network-types/{id}/` is called by a `power_user` or `admin`
- THEN a 204 No Content response is returned
- AND the type no longer appears in the list

#### Scenario: Power user deletes a type created by someone else
- GIVEN a network type created by a different user, referenced by no network
- WHEN a `power_user` calls `DELETE /api/v1/network-types/{id}/`
- THEN a 204 response is returned

#### Scenario: Power user deletes an orphaned type
- GIVEN a network type whose `created_by` is `NULL` (for example, seeded data or
  a type whose creator was deleted), referenced by no network
- WHEN a `power_user` calls `DELETE /api/v1/network-types/{id}/`
- THEN a 204 response is returned

#### Scenario: Delete blocked while networks use the type
- GIVEN a network type referenced by the networks `"user1-wan"` and `"power1-wan"`
- WHEN `DELETE /api/v1/network-types/{id}/` is called by a `power_user` or `admin`
- THEN a 409 response is returned listing `"user1-wan"` and `"power1-wan"`
- AND neither the type nor those networks are deleted

#### Scenario: Delete succeeds after blocking networks are removed
- GIVEN a network type whose referencing networks have all been deleted
- WHEN `DELETE /api/v1/network-types/{id}/` is called by a `power_user` or `admin`
- THEN a 204 response is returned

#### Scenario: Regular user cannot delete a network type
- GIVEN a user with `role=user`
- WHEN `DELETE /api/v1/network-types/{id}/` is called
- THEN a 403 response is returned

### Requirement: Network Type Upload/Delete Restricted to Power User and Admin
_Supersedes the former "Network Type Create/Update/Delete Restricted to Power User
and Admin" requirement, whose `PATCH`/`PUT` scenarios described endpoints that do
not exist (no `UpdateModelMixin`; such requests return 405)._

The system SHALL restrict the mutating network-type operations —
`POST /api/v1/network-types/upload/` and
`DELETE /api/v1/network-types/{id}/` — to users with `role=power_user` or
`role=admin`. A regular `user` SHALL receive `403` on any mutating request.
Reading (list and retrieve) remains available to any authenticated user. The
system does not expose create or update endpoints for network types; types are
created exclusively through the upload endpoint.

#### Scenario: Power user uploads a network type
- GIVEN a user with `role=power_user`
- WHEN `POST /api/v1/network-types/upload/` is called with a valid zip
- THEN the type is created and `created_by` is set to the requesting user

#### Scenario: Regular user cannot upload a network type
- GIVEN a user with `role=user`
- WHEN `POST /api/v1/network-types/upload/` is called
- THEN a 403 response is returned

#### Scenario: Any authenticated user can read network types
- GIVEN any authenticated user
- WHEN `GET /api/v1/network-types/` is called
- THEN a 200 response is returned

## ADDED Requirements

### Requirement: Audit Power-User Network Type Deletions
The system SHALL record an audit-log entry whenever a `power_user` deletes a
network type, capturing at least the acting user's id, the deleted type's id and
name, and a timestamp.

#### Scenario: Power-user deletion is audited
- GIVEN a `power_user` who deletes a network type that no network references
- WHEN the deletion succeeds
- THEN an audit-log entry is recorded identifying the acting power user, the
  deleted type, and the time of the deletion
