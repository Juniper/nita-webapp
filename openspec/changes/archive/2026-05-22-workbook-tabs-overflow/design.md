## Context

`WorkbookGrid` (introduced in the `close-webapp-gaps` change) renders a tab bar for multi-sheet workbooks using a `<div className="flex gap-1 border-b border-gray-700 pb-0">` container. Because `flex` with no wrap directive defaults to `flex-nowrap`, extra tabs simply overflow the container and are clipped or extend beyond the visible viewport. This is a pure CSS/Tailwind issue — no logic change is required.

## Goals / Non-Goals

**Goals:**
- All sheet tabs are reachable regardless of workbook width or number of sheets
- Fix is self-contained to `WorkbookGrid.tsx` — no API, backend, or state changes

**Non-Goals:**
- Horizontal scrolling tab bar (a scrollable strip is acceptable but wrapping is simpler and preferred)
- Virtualised or collapsed tab menus
- Any change to how sheet data is fetched or rendered

## Decisions

### D1 — Use `flex-wrap` (wrapping rows) over horizontal scroll

Alternatives considered:
- **`overflow-x-auto` scroll strip** — common pattern but requires fixed height and hides the overflow behind a scroll affordance that isn't obvious to users.
- **`flex-wrap`** — tabs simply reflow onto the next row. Works at all viewport sizes with zero JS. Chosen for simplicity and accessibility.

Change: replace `flex gap-1` on the tab container with `flex flex-wrap gap-1`.

## Risks / Trade-offs

- Multi-row tab bars take more vertical space when many sheets are present — acceptable given the fix is purely presentational and the alternative (hidden tabs) is worse.
- No migration or rollback needed; it is a one-line CSS class change.
