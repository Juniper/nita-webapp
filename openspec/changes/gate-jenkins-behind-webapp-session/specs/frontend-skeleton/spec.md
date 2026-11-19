## MODIFIED Requirements

### Requirement: Login Page
The system SHALL provide a `LoginPage` component that renders a username/password form. On submission it calls `POST /api/v1/auth/login/` via the API client. On success it updates `AuthContext` and redirects to the `next` query parameter when that value is a same-origin relative path — it begins with a single `/`, does not begin with `//`, and contains no URL scheme — and to `/` otherwise. On failure it displays an error message.

The login page SHALL display the brand mark above its heading. Because the login
page renders without the application header, this is the only place the mark
appears before authentication, and it is the first screen every user sees. The
mark SHALL be decorative, as in the header: the heading beneath it provides the
accessible name.

#### Scenario: Login page shows the brand mark
- WHEN an unauthenticated user opens `/login`
- THEN the brand mark is displayed above the "NITA Webapp" heading
- AND the mark is legible against the login card background

#### Scenario: Login page brand mark is decorative
- WHEN a screen reader traverses the login page
- THEN the mark is not announced
- AND the heading is announced exactly once

#### Scenario: Successful login redirects to dashboard
- GIVEN valid credentials are entered and no `next` parameter is present
- WHEN the login form is submitted
- THEN the user is redirected to `/`
- AND the username is visible in the authenticated shell

#### Scenario: Failed login shows error
- GIVEN invalid credentials are entered
- WHEN the login form is submitted
- THEN an error message is displayed on the page

#### Scenario: Successful login follows a safe next target
- GIVEN the user opened `/login?next=/jenkins/job/test-robot-net1/`
- WHEN valid credentials are submitted
- THEN the browser navigates to `/jenkins/job/test-robot-net1/`

#### Scenario: Unsafe next targets are ignored
- GIVEN the user opened `/login?next=//evil.example/` or `/login?next=https://evil.example/`
- WHEN valid credentials are submitted
- THEN the browser navigates to `/`
