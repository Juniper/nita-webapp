## 1. Add `?action_category_id=` filter to ActionViewSet

- [x] 1.1 In `ngcn/api/views.py`, extend `ActionViewSet.get_queryset()` to read `?action_category_id=` from `self.request.query_params` and apply `.filter(action_category_id=action_category_id)` when present, following the identical pattern used for `?campus_type_id=` in the same viewset.
- [x] 1.2 Add an `OpenApiParameter` entry for `action_category_id` to the `@extend_schema_view(list=extend_schema(...))` decorator on `ActionViewSet`, mirroring the existing `campus_type_id` parameter declaration.

## 2. Add `?action_category_id=` filter to ActionHistoryViewSet

- [x] 2.1 In `ngcn/api/views.py`, extend `ActionHistoryViewSet.get_queryset()` to read `?action_category_id=` from `self.request.query_params` and apply `.filter(category_id=action_category_id)` when present (note: the model field is `category_id`, not `action_category_id`).
- [x] 2.2 Add an `OpenApiParameter` entry for `action_category_id` to the `@extend_schema_view(list=extend_schema(...))` decorator on `ActionHistoryViewSet`.

## 3. Regenerate openapi.yaml

- [x] 3.1 Run `python manage.py spectacular --file openapi.yaml` from the `build-and-test-webapp/nita-webapp/ngcn_workbench/` directory to regenerate the committed schema so it includes the new parameters.
- [x] 3.2 Confirm the regenerated `openapi.yaml` contains `action_category_id` under `parameters` in both the `/api/v1/actions/` and `/api/v1/action-history/` list endpoint entries.

## 4. Write DRF tests for the new filters

- [x] 4.1 In `ngcn/tests/test_api_action_filters.py` (create file), write a test class `ActionCategoryFilterTests(APITestCase)` with:
  - `test_filter_actions_by_category` — creates two ActionCategory objects and two Actions belonging to each, calls `GET /api/v1/actions/?action_category_id=<id>`, asserts only the matching action is returned.
  - `test_filter_actions_combined` — calls `GET /api/v1/actions/?campus_type_id=<id>&action_category_id=<id>`, asserts intersection filtering is correct.
- [x] 4.2 In the same file, write a test class `ActionHistoryCategoryFilterTests(APITestCase)` with:
  - `test_filter_history_by_category` — creates two ActionHistory entries with different categories, calls `GET /api/v1/action-history/?action_category_id=<id>`, asserts only the matching entry is returned.
  - `test_filter_history_combined` — calls with both `campus_network_id` and `action_category_id`, asserts intersection filtering is correct.
- [x] 4.3 Run `pytest ngcn/tests/test_api_action_filters.py` and confirm all four tests pass.

## 5. Write OpenAPI drift test

- [x] 5.1 Create `ngcn/tests/test_openapi_drift.py` containing a single test `test_openapi_schema_matches_committed` that:
  1. Locates the committed `openapi.yaml` at the repo root (two levels up from the Django app).
  2. Shells out to `manage.py spectacular --file -` via `subprocess.run`, capturing stdout.
  3. Parses both the captured output and the committed file as YAML using `yaml.safe_load`.
  4. Strips the top-level `info.version` key from both before comparing (it may contain a build-time value).
  5. Asserts the two dicts are equal, with a failure message of `"openapi.yaml is out of sync — run: python manage.py spectacular --file openapi.yaml"`.
- [x] 5.2 Run `pytest ngcn/tests/test_openapi_drift.py` and confirm it passes against the freshly regenerated `openapi.yaml` from step 3.1.

## 6. Full test suite validation

- [x] 6.1 Run the full test suite with `pytest` from `build-and-test-webapp/nita-webapp/ngcn_workbench/` and confirm all existing tests still pass alongside the new ones.
- [x] 6.2 Verify no regressions: the two modified `get_queryset` methods behave identically to before when `action_category_id` is absent from the query string.
