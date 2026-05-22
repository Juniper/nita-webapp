# Workbook Tab Overflow Specification

## Purpose
The `WorkbookGrid` component renders a tab bar so users can switch between
sheets. This spec covers the layout behaviour of that tab bar when the number
of sheets exceeds the available horizontal space.

## Requirements

### Requirement: Workbook tab bar wraps on overflow
The tab bar in the `WorkbookGrid` component SHALL wrap onto additional rows when
the total width of all tabs exceeds the available container width, so that every
sheet tab is visible and clickable without horizontal scrolling or clipping.

#### Scenario: All tabs visible when many sheets present
- WHEN a workbook contains more sheets than fit on a single row at the current
  viewport width
- THEN the tab bar wraps to show all tabs across multiple rows, with no tab
  hidden or clipped

#### Scenario: Single-row tab bar unchanged for few sheets
- WHEN a workbook contains few enough sheets to fit on one row
- THEN the tab bar renders on a single row as before, with no visible change

#### Scenario: Active tab remains selectable after wrap
- WHEN the active tab is on the second or subsequent wrapped row
- THEN clicking it still selects the corresponding sheet and renders its grid
