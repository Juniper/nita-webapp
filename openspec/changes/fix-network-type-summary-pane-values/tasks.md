## 1. Render the selected network type

- [x] 1.1 Update the campus type detail view to load the selected CampusType for the requested id.
- [x] 1.2 Render the selected type's name, application zip, and description in the detail template without leaving the summary pane blank on first paint.
- [x] 1.3 Keep the existing client-side refresh path aligned with the rendered values and preserve the current element ids.

## 2. Add regression coverage

- [x] 2.1 Add a targeted test that the campus type detail page includes the selected type's summary values.
- [x] 2.2 Add a second selection case so the detail pane is verified to update when a different network type is chosen.

## 3. Validate the change

- [x] 3.1 Run the focused pytest slice covering the campus type detail view and related network-type coverage.