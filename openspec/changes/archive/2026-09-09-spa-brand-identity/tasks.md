## 1. Assets

- [x] 1.1 Move the supplied assets out of `frontend/dist/assets/` (build output,
  gitignored, wiped by the next build) into tracked locations
- [x] 1.2 Strip Inkscape editor metadata (`sodipodi:*`, `inkscape:*`,
  `namedview`) from both files
- [x] 1.3 Replace `public/favicon.svg` (React Router logo) with the NITA mark,
  including a `prefers-color-scheme` block for dark tab strips

## 2. Header mark

- [x] 2.1 Add `src/components/Logo.tsx` rendering the lockup inline with
  `stroke="currentColor"`
- [x] 2.2 Mark it `aria-hidden="true"` and `focusable="false"` (decorative — the
  wordmark carries the accessible name)
- [x] 2.3 Wrap the mark and the wordmark in a flex container in `AppLayout`;
  no link, no hover or focus affordance
- [x] 2.4 Size it `h-6 w-auto` so it matches the wordmark's optical height

## 3. Login page mark

- [x] 3.1 Render the same `Logo` centred above the "NITA Webapp" heading inside
  the login card
- [x] 3.2 Size it `h-12 w-auto mx-auto`, decorative as in the header

## 4. Document identity

- [x] 4.1 Change `<title>frontend</title>` to `NITA Webapp` in `index.html`

## 5. Remove scaffold

- [x] 5.1 Verify zero references to `react.svg`, `vite.svg`, `hero.png` and
  `icons.svg` in `frontend/src` and `index.html`
- [x] 5.2 Delete all four

## 6. Tests

- [x] 6.1 `AppLayout.test.tsx` — mark present in the header, before the brand
  name, `aria-hidden` and `focusable="false"`, not wrapped in a link or button,
  brand name announced exactly once
- [x] 6.2 `LoginPage.test.tsx` — same assertions for the login card, plus the
  mark precedes the heading
- [x] 6.3 Confirm the decorative assertions fail when `aria-hidden` is removed

## 7. Verify

- [x] 7.1 `npm test` green (41 tests)
- [x] 7.2 `npm run lint` green
- [x] 7.3 `npm run build` green
- [x] 7.4 Render the mark against the real header colour and confirm it is
  legible
- [x] 7.5 Deploy to the local cluster and confirm the title, bundle and favicon
  are served
- [x] 7.6 Visual check of the deployed login page in a browser
- [x] 7.7 Visual check of the authenticated header by a signed-in user

## Verification notes

**The `#1a1a1a` problem was confirmed visually, not assumed.** Both assets were
rendered on white and on `#111827` before any code was written: on white they are
crisp, on the header background they are effectively invisible. That render is
what motivated Decision 1.

**A bug in the first implementation was caught before building.** The header mark
was initially added as `<img src={logoUrl}>`. That would have shipped an
invisible logo, because `currentColor` cannot resolve through `<img>` — the SVG
renders in an isolated context. Switched to an inline component and re-verified
by rendering a replica of the real header.

**Both deployed surfaces were checked in a browser**, not merely by HTTP status:

- `/login` — mark centred above the heading on the card, correctly proportioned
  against the `text-2xl` title.
- Authenticated header — signed in and confirmed the mark renders white and
  legible before the wordmark, at `h-6`.

**The favicon renders**, at 16 / 32 / 64 px, and its `prefers-color-scheme` block
is applied. Only the dark branch was actually exercised: the host OS is in dark
mode, and a favicon follows the tab-strip theme rather than any page background,
so the light branch could not be triggered from a test harness.

**The tests were confirmed to catch regressions.** Removing `aria-hidden` from
`Logo` turns exactly the two decorative assertions red:

```
× hides the mark from assistive technology   (AppLayout)
× hides the mark from assistive technology   (LoginPage)
Tests  2 failed | 39 passed (41)
```

## Observed but out of scope

Signing in surfaced a pre-existing accessibility defect in the header, unrelated
to this change: the admin badge is separated from the username by `ml-2` only, so
the accessibility tree reads **"Signed in as vagrantadmin"**. It needs whitespace
or an `aria-label`, and belongs in its own change.
