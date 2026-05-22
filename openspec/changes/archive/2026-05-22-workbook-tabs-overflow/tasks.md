## 1. Fix Tab Bar Overflow

- [x] 1.1 In `frontend/src/components/WorkbookGrid.tsx`, add `flex-wrap` to the tab bar container class list: change `className="flex gap-1 border-b border-gray-700 pb-0"` to `className="flex flex-wrap gap-1 border-b border-gray-700 pb-0"`

## 2. Verification

- [x] 2.1 Build the frontend (`npm run build` inside `frontend/`) and confirm zero TypeScript/lint errors
- [x] 2.2 Visually verify that a workbook with many sheets shows all tabs (wrapping to multiple rows) with none clipped or hidden
- [x] 2.3 Confirm that clicking a tab on a wrapped row correctly activates that sheet
