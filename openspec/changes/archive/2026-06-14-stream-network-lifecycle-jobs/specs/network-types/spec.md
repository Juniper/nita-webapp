## MODIFIED Requirements

### Requirement: Upload a Network Type
The system SHALL register a new network type from a zip archive via
POST /api/v1/network-types/upload/.

Loading a network type SHALL be non-blocking. The system SHALL invoke the
`network_type_validator` Jenkins job through the shared invocation library and
return without waiting for the validation/load build to complete. The response
SHALL include a streaming handle (`job_name` and `build_no`) so the SPA can
watch the live console of the load job. If no file is supplied the system SHALL
return `400` with `result: failure` and a reason. If the Jenkins service is
unreachable the system SHALL return `503 Service Unavailable` with a failure
reason.

#### Scenario: Successful upload starts the job and streams
- GIVEN a valid project zip with project.yaml and ansible.cfg
- WHEN the zip is posted as multipart/form-data with field name `app_zip_file`
- THEN the `network_type_validator` job is invoked
- AND a `202` response is returned with `result`, `name`, and a streaming handle
  (`job_name`, `build_no`) without waiting for the build to finish

#### Scenario: Missing file
- GIVEN no file is included in the POST body
- WHEN POST /api/v1/network-types/upload/ is called
- THEN a 400 response with `result: failure` and a reason is returned

#### Scenario: Jenkins unreachable on load
- GIVEN the Jenkins service is not reachable from the Django container
- WHEN POST /api/v1/network-types/upload/ is called with a valid zip
- THEN a 503 response is returned with a failure reason
