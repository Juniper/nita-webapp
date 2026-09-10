## Context

The supplied assets are Inkscape exports of a `nita.png`: a wide lockup
(`148 × 66.667`, gear plus two flanking network devices) and a square mark
(`66.667 × 66.667`, the gear alone). Both are **pure line art** — every path and
the circle are `fill:none; stroke:#1a1a1a; stroke-width:3`. There are no fills,
gradients or embedded raster data. The `#999999` / `#d1d1d1` / `#ffffff` values
present in the files are Inkscape editor chrome (`pagecolor`, `deskcolor`,
`export-bgcolor`), not artwork.

The application header is `bg-gray-900` (`#111827`) with `text-white`.

## Goals / Non-Goals

**Goals:**
- The application shows its own mark in the header, legibly.
- The login page — the first screen every user sees — carries the same mark.
- The browser tab shows the same mark and a real title.
- The template scaffold stops shipping.

**Non-Goals:**
- The legacy Django admin surface, any wider redesign.

## Decisions

### Decision 1: Recolour the artwork to `currentColor`

**Choice**: Replace `stroke:#1a1a1a` with `stroke="currentColor"` throughout the
header mark.

**Rationale**: `#1a1a1a` on `#111827` is near-black on near-black. Rendered
against the real header colour the mark is effectively invisible — not subtly
low-contrast, but absent. Because the artwork is stroke-only in a single colour,
`currentColor` is a one-token substitution: the mark inherits the header's white
text colour today, and would follow automatically if a light theme ever arrives,
with no second asset and no `prefers-color-scheme` handling in the component.

**Consequence (accepted)**: this modifies artwork that was supplied rather than
authored here. If `#1a1a1a` is specified by a brand kit, the correct fix is a
light-on-dark variant from the brand owner instead, and this decision should be
revisited. Reverting is a one-token change. **Confirmed acceptable by the asset's
provider.**

### Decision 2: Inline SVG component, not `<img>`

**Choice**: `src/components/Logo.tsx` returning inline JSX SVG, rather than
importing `logo.svg` as a URL.

**Rationale**: **`currentColor` does not work through `<img>`.** An SVG loaded as
an image renders in an isolated document with no access to the host page's
cascade, so `currentColor` would resolve to the SVG's own initial colour — black
— reintroducing exactly the invisibility problem Decision 1 exists to solve. Only
an inline SVG inherits `color` from its parent.

Rejected alternatives: `vite-plugin-svgr` (a build-time dependency for one icon);
CSS `mask-image` with `bg-current` (works, but obscure for the next reader).

**Consequence**: the mark's path data lives in a `.tsx` file, and the standalone
`logo.svg` is not kept — one source of truth rather than two that can drift. The
favicon necessarily remains a separate file, so the gear geometry does exist in
two places; that duplication is unavoidable.

### Decision 3: The favicon carries explicit colours with a dark-mode variant

**Choice**: `public/favicon.svg` keeps real colour values and adds an internal
`prefers-color-scheme` block (`#1a1a1a` light, `#f3f4f6` dark).

**Rationale**: a favicon has no surrounding cascade, so `currentColor` has
nothing to inherit and would resolve to black. Browser tab strips follow the OS
theme, so a fixed near-black mark disappears for dark-mode users — the same class
of defect as Decision 1, on a different surface. A media query inside the SVG is
four lines and handles both.

### Decision 4: Decorative and unlinked

**Choice**: `aria-hidden="true"` and `focusable="false"` on the SVG; no `<Link>`
wrapper.

**Rationale**: the visible text "NITA Webapp" sits immediately beside the mark
and already provides the accessible name — announcing both would make screen
readers say the brand twice. And the sidebar already has a Dashboard entry
pointing at `/`; a second route to the same place inches away adds a focus stop
and a hover affordance for no navigational gain.

### Decision 5: Delete the scaffold in the same change

**Choice**: remove `react.svg`, `vite.svg`, `hero.png` and `icons.svg` here
rather than as separate cleanup.

**Rationale**: normally unrelated deletions do not belong in a feature change,
but all four were verified to have **zero references** in `frontend/src` and
`index.html`, so they add nothing for a reviewer to evaluate. They are also the
same story: the app stops wearing the template's identity. Leaving them would
mean the repo still contains a React Router hero image and a Discord icon.

### Decision 6: The wide lockup in the header, not the square mark

**Choice**: the gear-plus-devices lockup beside the wordmark.

**Rationale**: the devices-and-links motif says "network automation"; a lone gear
says "settings". Confirmed by rendering that it contains **no wordmark**, so it
does not duplicate the adjacent "NITA Webapp" text. At `h-6` it occupies roughly
53 px of header width, which is plentiful.

### Decision 7: The login page carries the mark above its heading

**Choice**: the same `Logo` component, centred at `h-12` above the existing
"NITA Webapp" heading inside the login card.

**Rationale**: the login page renders without header or sidebar by design, so the
header mark can never reach it — yet it is the only screen every user sees, and
the one where identity matters most. Stacking the mark above a centred heading is
the conventional login lockup and needs no layout change: the card is already
centre-aligned.

`h-12` (48 px, ~107 px wide at the lockup's 2.2:1 ratio) sits comfortably inside
the card's 320 px content width and balances the `text-2xl` heading — larger than
the header's `h-6`, because a login screen has room and no competing chrome.

The mark stays decorative here for the same reason as in the header: the heading
directly beneath it already says "NITA Webapp".

## Risks / Trade-offs

- **Artwork modified downstream of its author** — see Decision 1.
- **Geometry duplicated** between `Logo.tsx` and `favicon.svg`. If the mark is
  ever redrawn, both need updating. Unavoidable given the favicon must be a file.
- **Path data in a component file** is unpleasant to diff. Accepted as the cost
  of `currentColor`.

## Migration Plan

Purely additive plus deletions of unreferenced files. No API, schema or backend
impact. The favicon path (`/favicon.svg`) is unchanged, so `index.html` needs no
change beyond the title.

## Open Questions

- **Which brand is this?** The repo is simultaneously Juniper
  (`ghcr.io/juniper/nita-webapp`, `LABEL net.juniper.framework="NITA"`) and HPE
  (every copyright header). The mark supplied is neutral, which sidesteps the
  question rather than answering it.
- **Should the legacy Django admin surface be branded too**, or is it on its way
  out?
