## Why

The SPA wears another project's identity. Every image under `frontend/` was
template scaffold, none of it referenced from `frontend/src`:

| File | What it actually was |
|---|---|
| `public/favicon.svg` | React Router v7 logo (purple `#863bff` mark) |
| `public/icons.svg` | sprite of bluesky / discord / github / x / documentation icons |
| `src/assets/hero.png` | React Router hero illustration |
| `src/assets/react.svg`, `vite.svg` | Vite scaffold |

So the browser tab showed a **React Router logo** beside the title
**"frontend"**, and the application header showed a bare wordmark with no mark at
all. A network-automation tool was also shipping Discord and Bluesky icons.

There is precedent for a mark having existed: the legacy Django admin template
still references `{% static 'images/juniper.png' %}`, a file that does not exist
anywhere in the repo or on disk — a dangling favicon reference.

## What Changes

- **A NITA mark appears in the application header**, before the "NITA Webapp"
  wordmark: a gear flanked by two network devices. It is **decorative** (the
  wordmark carries the accessible name) and **not a link** (the sidebar already
  routes to `/`).
- **The mark is rendered inline** as a `Logo` component using
  `stroke="currentColor"`, so it inherits the surrounding text colour.
- **The mark also appears on the login page**, centred above the "NITA Webapp"
  heading. The login page renders without layout chrome by design, so the header
  mark does not reach it — and it is the first screen every user sees.
- **The favicon is replaced** with the same mark, standalone.
- **The document title becomes "NITA Webapp"** instead of `frontend`.
- **The scaffold assets are deleted** — all four were verified to have zero
  references in `frontend/src` and `index.html`.

## Capabilities

### Modified Capabilities

- `spa-layout`: the header displays a decorative brand mark before the brand
  name.

### Added Capabilities

- `frontend-skeleton`: a document identity requirement covering the page title
  and favicon.

## Impact

- **Frontend**: new `src/components/Logo.tsx`; `AppLayout` header gains a flex
  wrapper and the mark; `LoginPage` gains the mark above its heading;
  `public/favicon.svg` replaced; `index.html` title changed; four scaffold files
  deleted.
- **Backend / API / specs of other capabilities**: none.
- **Bundle**: the mark is inline SVG, so no extra HTTP request. Net CSS/JS change
  is negligible; deleting `icons.svg` and `hero.png` removes ~18 KB from the
  image payload that was being copied into `dist/` on every build.
- **Tests**: the existing 30 frontend tests continue to pass. The mark is
  `aria-hidden`, so it does not appear in accessibility queries and does not
  affect the dashboard's link assertions.

### Out of Scope

- **The legacy Django admin `images/juniper.png` reference.** A different UI
  surface whose future is unclear; fixing it means deciding whether that surface
  still matters.
- **Any wider visual redesign** — colours, spacing, typography are untouched.
