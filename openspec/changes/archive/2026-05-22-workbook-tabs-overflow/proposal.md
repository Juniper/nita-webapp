## Why

The `WorkbookGrid` component renders a horizontal tab bar for multi-sheet workbooks. When a workbook has more sheets than fit in the available width the tabs overflow silently off the right edge of the viewport, making extra sheets unreachable. This is a usability bug introduced with the initial WorkbookGrid implementation.

## What Changes

- The tab bar in `WorkbookGrid` is updated so tabs wrap onto additional rows (or scroll) rather than overflowing off-screen.
- Excess sheets are always reachable regardless of how many sheets a workbook contains or how narrow the container is.

## Capabilities

### New Capabilities

- `workbook-tab-overflow`: Tab bar in the workbook grid handles sheet overflow gracefully — tabs wrap to multiple rows so all sheets remain accessible.

### Modified Capabilities

<!-- none -->

## Impact

- `frontend/src/components/WorkbookGrid.tsx` — tab bar CSS classes updated
- No new dependencies, no API changes, no backend changes
