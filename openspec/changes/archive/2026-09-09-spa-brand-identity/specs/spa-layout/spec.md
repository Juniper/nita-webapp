## MODIFIED Requirements

### Requirement: AppLayout provides persistent application chrome
The SPA SHALL have an `AppLayout` component that renders a top header and left sidebar around its `children`. All authenticated pages SHALL use `AppLayout` as their outermost wrapper.

The header SHALL display a brand mark immediately before the brand name. The mark
SHALL be decorative: it SHALL be hidden from assistive technology
(`aria-hidden`), SHALL NOT be focusable, and SHALL NOT be a link — the adjacent
brand name provides the accessible name, and the sidebar already provides
navigation to `/`. The mark SHALL be rendered inline so that it inherits the
header's text colour, so that it remains legible against the header background
and follows any future change of theme.

#### Scenario: Header shows brand and user
- **WHEN** an authenticated user views any protected page
- **THEN** the header SHALL display the application brand name on the left and the signed-in username on the right

#### Scenario: Header shows the brand mark before the name
- **WHEN** an authenticated user views any protected page
- **THEN** a brand mark SHALL be displayed immediately before the brand name

#### Scenario: Brand mark is legible against the header
- **WHEN** the header is rendered
- **THEN** the mark SHALL be drawn in the header's text colour rather than a
  fixed colour, so it is not rendered dark-on-dark

#### Scenario: Brand mark is decorative
- **WHEN** a screen reader traverses the header
- **THEN** the mark SHALL NOT be announced
- **AND** the brand name SHALL be announced exactly once

#### Scenario: Brand mark is not interactive
- **WHEN** the user tabs through the header
- **THEN** the mark SHALL NOT receive focus
- **AND** activating it SHALL NOT navigate

#### Scenario: Header provides logout
- **WHEN** the user clicks the logout button in the header
- **THEN** the session SHALL be cleared and the user SHALL be redirected to `/login`

#### Scenario: Sidebar shows navigation links
- **WHEN** an authenticated user views any protected page
- **THEN** the sidebar SHALL display navigation links for: Dashboard (`/`), Network Types (`/network-types`), Networks (`/networks`)

#### Scenario: Active nav link is highlighted
- **WHEN** the current route matches a sidebar link
- **THEN** that link SHALL appear visually distinct (highlighted) from the inactive links

#### Scenario: Login page has no layout chrome
- **WHEN** the user views the login page
- **THEN** the header and sidebar SHALL NOT be rendered
