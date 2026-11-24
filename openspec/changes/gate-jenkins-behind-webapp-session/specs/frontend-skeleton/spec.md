## MODIFIED Requirements

### Requirement: Login Page
The `LoginPage` SHALL submit its username/password form to
`POST /api/v1/auth/login/` via the API client and update `AuthContext` on
success. It SHALL follow a safe same-origin `next` path or fall back to `/`;
on failure it SHALL display an error and remain on the login page. It SHALL
show a decorative brand mark above its heading.

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
- AND only paths beginning with a single `/`, without a URL scheme, are accepted
