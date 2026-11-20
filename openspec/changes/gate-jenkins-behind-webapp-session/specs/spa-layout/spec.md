## ADDED Requirements

### Requirement: Sidebar shortcut to the Jenkins home page
The sidebar SHALL end with a `Jenkins ↗` entry, placed after the role-gated
entries (Teams, User Management), linking to the proxied Jenkins home page
`/jenkins/`. Because that route is served by the reverse proxy outside the SPA,
the entry SHALL be a plain anchor (not a client-side route) that opens in a new
tab with `rel="noopener noreferrer"`, styled like the other sidebar entries. It
SHALL be shown to every authenticated role; Jenkins enforces per-role access
through the forwarded identity.

#### Scenario: Sidebar shows the Jenkins shortcut last
- **WHEN** an authenticated user views any protected page
- **THEN** the last sidebar entry is `Jenkins ↗` with `href="/jenkins/"`
- **AND** it opens in a new tab (`target="_blank"`, `rel="noopener noreferrer"`)

#### Scenario: Shortcut lands on Jenkins as the webapp user
- **GIVEN** a user is signed in to the webapp
- **WHEN** they follow the sidebar `Jenkins ↗` entry
- **THEN** the Jenkins dashboard loads through the proxy without a further login
- **AND** Jenkins identifies them by their webapp username and role
