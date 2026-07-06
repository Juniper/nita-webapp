## ADDED Requirements

### Requirement: Action Jenkins job link
The network detail Actions tab SHALL display, for each action, a link that opens the action's Jenkins job page in a new browser tab. The link target SHALL be the reverse-proxied Jenkins job path `/jenkins/job/{jenkins_url}-{network_name}/`, where `jenkins_url` is the action's job-name prefix and `network_name` is the current network's name. The link SHALL open in a new tab with `rel="noopener"` and SHALL not interfere with the existing Run action.

#### Scenario: Action row shows a Jenkins link
- **WHEN** the user opens the Actions tab for a network
- **THEN** each action row shows a Jenkins link alongside its Run button
- **AND** the link points to `/jenkins/job/{jenkins_url}-{network_name}/` and opens in a new tab

#### Scenario: Jenkins link is routed by the proxy
- **WHEN** the user activates an action's Jenkins link
- **THEN** the request to `/jenkins/` is routed by the reverse proxy to the Jenkins service (not the SPA)
