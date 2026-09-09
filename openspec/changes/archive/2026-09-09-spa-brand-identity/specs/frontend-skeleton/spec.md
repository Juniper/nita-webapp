## MODIFIED Requirements

### Requirement: Login Page
The system SHALL provide a `LoginPage` component that renders a username/password form. On submission it calls `POST /api/v1/auth/login/` via the API client. On success it updates `AuthContext` and redirects to `/`. On failure it displays an error message.

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
- GIVEN valid credentials are entered
- WHEN the login form is submitted
- THEN the user is redirected to `/`
- AND the username is visible in the authenticated shell

#### Scenario: Failed login shows error
- GIVEN invalid credentials are entered
- WHEN the login form is submitted
- THEN an error message is displayed on the page
- AND the user remains on `/login`

## ADDED Requirements

### Requirement: Document Identity
The SPA's HTML document SHALL identify the application rather than the project
template it was scaffolded from. The document title SHALL be `NITA Webapp`, and
the favicon SHALL be the NITA brand mark served from `/favicon.svg`.

Because a favicon is rendered without a surrounding colour context, it SHALL
carry explicit colour values rather than relying on inheritance, and SHALL remain
legible on both light and dark browser tab strips.

The `frontend/` tree SHALL NOT contain unreferenced scaffold assets from the
project template.

#### Scenario: Browser tab shows the application title
- WHEN a user opens any page of the SPA
- THEN the browser tab displays `NITA Webapp`

#### Scenario: Browser tab shows the NITA mark
- WHEN a user opens any page of the SPA
- THEN the favicon requested from `/favicon.svg` is the NITA brand mark

#### Scenario: Favicon is legible in a dark tab strip
- GIVEN the operating system is set to a dark colour scheme
- WHEN the browser renders the favicon
- THEN the mark is drawn in a light colour rather than near-black

#### Scenario: No template scaffold assets remain
- WHEN the `frontend/` tree is inspected
- THEN it contains no unreferenced images carried over from the project template
