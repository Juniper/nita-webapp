## ADDED Requirements

### Requirement: Dashboard presents a recent activity feed
The dashboard page at `/` SHALL present a **Recent activity** feed of
action-history entries in place of static welcome text. The page SHALL issue a
single `GET /api/v1/action-history/` request on mount and SHALL display at most
**ten** entries. The page SHALL NOT display counters, totals or other aggregate
figures.

The feed SHALL show, for each entry, its status, the action name, the network
name, the triggering user and the time of the run.

#### Scenario: Dashboard renders recent activity
- **GIVEN** an authenticated user with action-history entries in scope
- **WHEN** the user opens `/`
- **THEN** a Recent activity list is rendered showing status, action name,
  network name, triggering user and run time for each entry

#### Scenario: At most ten entries are shown
- **GIVEN** more than ten action-history entries are in scope
- **WHEN** the dashboard renders
- **THEN** exactly ten entries are displayed

#### Scenario: No aggregate figures are displayed
- **WHEN** the dashboard renders
- **THEN** no counts, totals or percentages of runs are shown

### Requirement: Recent activity is ordered by attention then recency
The feed SHALL order entries by three groups, and newest-first within each group:

1. **In progress** — `status` equal to `Running`
2. **Needs attention** — `status` equal to `Failure`, `Failed`, `Aborted` or
   `Unstable`
3. **All other entries**

Status comparison SHALL be case-insensitive. An entry whose status matches none
of the listed values SHALL fall into group 3 and SHALL still be displayed. In
progress and needs-attention entries SHALL be visually distinguishable from the
rest.

Because in-progress entries sort first, an in-progress run SHALL NOT be displaced
from the feed by more recent completed runs.

#### Scenario: In-progress runs sort first
- **GIVEN** entries with statuses `Running`, `Failure` and `Success`
- **WHEN** the dashboard renders
- **THEN** the `Running` entry appears above the `Failure` entry, which appears
  above the `Success` entry

#### Scenario: Newest first within a group
- **GIVEN** two entries with status `Success` and different timestamps
- **WHEN** the dashboard renders
- **THEN** the more recent entry appears first

#### Scenario: Unstable is treated as needing attention
- **GIVEN** an entry with status `Unstable` and an entry with status `Success`
- **WHEN** the dashboard renders
- **THEN** the `Unstable` entry appears above the `Success` entry

#### Scenario: In-progress run is not displaced by newer completed runs
- **GIVEN** one `Running` entry and fifteen more recent completed entries
- **WHEN** the dashboard renders
- **THEN** the `Running` entry is displayed

#### Scenario: Unrecognised status is displayed, not hidden
- **GIVEN** an entry whose status is a value not listed above
- **WHEN** the dashboard renders
- **THEN** the entry is displayed among the other entries without attention
  styling

### Requirement: Recent activity rows deep-link to the network history
Each row in the feed SHALL link to the History tab of the run's network at
`/networks/{campus_network_id}?tab=history`, so that the console output, Jenkins
build link and test summary for that run are one click away.

#### Scenario: Row links to its own network's history
- **GIVEN** a feed row for a run on the network with id `7`
- **WHEN** the user activates that row
- **THEN** the SPA navigates to `/networks/7?tab=history`

### Requirement: Recent activity shows the triggering user
Each row SHALL display the `triggered_by_username` of its entry. When that value
is empty, the row SHALL display an em dash (`—`).

#### Scenario: Triggering user is shown
- **GIVEN** a feed row whose entry has `triggered_by_username` of `"alice"`
- **WHEN** the dashboard renders
- **THEN** the row displays `alice`

#### Scenario: Unknown actor is shown as an em dash
- **GIVEN** a feed row whose entry has an empty `triggered_by_username`
- **WHEN** the dashboard renders
- **THEN** the row displays `—`

### Requirement: Recent activity refreshes while work is in progress
While at least one displayed entry has `status = "Running"`, the dashboard SHALL
re-fetch the action-history list every 15 seconds, using the same polling
behaviour as the network detail History tab. When no displayed entry is
`Running`, no interval request SHALL be issued. Refreshes SHALL keep existing
rows visible and SHALL NOT show a loading indicator. The interval SHALL stop when
no in-progress entry remains and when the page unmounts.

#### Scenario: In-progress run refreshes without interaction
- **GIVEN** the dashboard displays an entry with `status = "Running"`
- **WHEN** 15 seconds elapse without user interaction
- **THEN** a fresh `GET /api/v1/action-history/` is issued and the displayed
  status reflects the latest server value

#### Scenario: No polling when nothing is in progress
- **GIVEN** the dashboard displays no entry with `status = "Running"`
- **WHEN** time elapses without user interaction
- **THEN** no further action-history requests are issued

#### Scenario: Polling stops when the page is left
- **GIVEN** the dashboard is polling because an entry is `Running`
- **WHEN** the user navigates away
- **THEN** the interval is cleared and no further requests are issued

### Requirement: Recent activity reflects the user's visibility scope
The feed SHALL display only the action-history entries the requesting user is
permitted to see. Scoping SHALL be enforced by the action-history API rather than
by client-side filtering: a `role=user` sees runs for networks they own or share
through a team, while `power_user` and `admin` see all runs, consistent with
network visibility.

#### Scenario: Regular user sees only their own scope
- **GIVEN** Alice (role=user) owns one network and Bob owns another, both with
  recent runs
- **WHEN** Alice opens the dashboard
- **THEN** only runs for Alice's network are displayed

#### Scenario: Admin sees all activity
- **GIVEN** recent runs exist across networks owned by several users
- **WHEN** an admin opens the dashboard
- **THEN** runs from all of those networks may be displayed

### Requirement: Dashboard handles empty and error states
When the action-history response contains no entries, the dashboard SHALL render
an empty state indicating there is no recent activity, rather than an empty list
or a blank page. When the request fails, the dashboard SHALL render an error
message and SHALL remain navigable.

#### Scenario: No activity yet
- **GIVEN** an authenticated user with no action-history entries in scope
- **WHEN** the user opens the dashboard
- **THEN** an empty state indicating no recent activity is displayed

#### Scenario: Request failure is surfaced
- **GIVEN** the action-history request fails
- **WHEN** the dashboard renders
- **THEN** an error message is displayed and the layout chrome remains usable
