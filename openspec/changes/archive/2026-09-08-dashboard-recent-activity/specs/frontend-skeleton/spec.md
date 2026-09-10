## MODIFIED Requirements

### Requirement: Dashboard Renders for Authenticated Users
_Supersedes the former "Dashboard Shell Placeholder" requirement, which described
a welcome screen showing the username and a logout button. The logout control
lives in the application header (see the `spa-layout` capability), and the page
body is now the recent-activity feed defined by the `spa-dashboard` capability._

The system SHALL provide a `DashboardPage` component that renders at `/` when the
user is authenticated, wrapped in `AppLayout`. Its content SHALL be the recent
activity feed specified by the `spa-dashboard` capability. Unauthenticated access
to `/` SHALL continue to redirect to `/login`.

#### Scenario: Authenticated root access renders the dashboard
- GIVEN the user is authenticated
- WHEN the user navigates to `/`
- THEN `DashboardPage` is rendered inside `AppLayout` showing the recent activity
  feed

#### Scenario: Unauthenticated root access redirects to login
- GIVEN the user is not authenticated
- WHEN the user navigates to `/`
- THEN the user is redirected to `/login`

#### Scenario: Logout from the dashboard
- GIVEN the user is on the dashboard
- WHEN the logout button in the header is clicked
- THEN the user is redirected to `/login`
- AND subsequent navigation to `/` redirects back to `/login`
