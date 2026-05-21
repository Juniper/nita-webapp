## 1. Implement the SSE streaming generator

- [x] 1.1 In `ngcn/api/views.py`, add a module-level helper function `_jenkins_progressive_text_generator(job_url, build_no)` that:
  - Imports `urllib.request`, `base64`, `time`, `re`, and the ANSI-escape pattern already used in the existing `console` action.
  - Imports `JENKINS_SERVER_URL`, `JENKINS_SERVER_USER`, `JENKINS_SERVER_PASS` from `ngcn.views`.
  - Constructs the Jenkins progressive text URL: `{JENKINS_SERVER_URL}/job/{job_url}/{build_no}/logText/progressiveText`.
  - Loops up to 1800 times (30-minute cap), polling with `?start=<offset>`:
    - Builds a `urllib.request.Request` with Basic Auth header (`base64`-encoded `user:pass`).
    - Opens the request; reads the response body.
    - Strips ANSI codes from the chunk.
    - `yield`s each non-empty line as `f"data: {line}\n\n"`.
    - Reads `X-Text-Size` header to advance the byte offset.
    - If `X-More-Data` header is absent or `"false"`, `yield "event: done\ndata: \n\n"` and `return`.
    - Otherwise `time.sleep(1)` and continue.
  - After the loop limit: `yield "event: timeout\ndata: \n\n"`.
  - Wraps the entire loop body in `try/except Exception`: on error, `yield f"event: error\ndata: {str(exc)}\n\n"` and `return`.

- [x] 1.2 Add a `stream` `@action` to `ActionHistoryViewSet` in `ngcn/api/views.py`:
  ```python
  @extend_schema(
      responses={(200, "text/event-stream"): OpenApiResponse(
          response=OpenApiTypes.STR,
          description="SSE stream of Jenkins console output lines. "
                      "Events: data (log line), done (build finished), "
                      "error (Jenkins unreachable), timeout (30-min cap reached).",
      )},
  )
  @action(detail=True, methods=["get"], url_path="stream")
  def stream(self, request, pk=None):
      """Stream Jenkins console output as Server-Sent Events."""
      history = self.get_object()
      job_url = history.action_id.jenkins_url + "-" + history.campus_network_id.name
      build_no = history.jenkins_job_build_no
      response = StreamingHttpResponse(
          _jenkins_progressive_text_generator(job_url, build_no),
          content_type="text/event-stream",
      )
      response["Cache-Control"] = "no-cache"
      response["X-Accel-Buffering"] = "no"
      return response
  ```
  Add `from django.http import StreamingHttpResponse` to the imports at the top of `ngcn/api/views.py`.

## 2. Regenerate openapi.yaml

- [x] 2.1 From `build-and-test-webapp/nita-webapp/ngcn_workbench/`, run:
  ```
  DJANGO_SETTINGS_MODULE=ngcn_workbench.test_settings python3 manage.py spectacular --file /path/to/repo/openapi.yaml
  ```
  (Use the absolute path to `openapi.yaml` at the repo root.)
- [x] 2.2 Confirm the regenerated `openapi.yaml` contains a path entry for `/api/v1/action-history/{id}/stream/` with `text/event-stream` in its response content types.

## 3. Write tests for the stream action

- [x] 3.1 Create `tests/test_api_streaming.py`. Write a test `test_stream_yields_sse_events_and_done` that:
  - Patches `ngcn.api.views._jenkins_progressive_text_generator` to return a simple list of two SSE data lines followed by the done event: `["data: line one\n\n", "data: line two\n\n", "event: done\ndata: \n\n"]`.
  - Calls `GET /api/v1/action-history/{id}/stream/` with an authenticated client.
  - Asserts the response status is 200.
  - Asserts `Content-Type` contains `text/event-stream`.
  - Collects the streamed content (iterate `response.streaming_content`) and asserts it contains `b"data: line one"` and `b"event: done"`.

- [x] 3.2 Write a test `test_stream_requires_authentication` that:
  - Calls `GET /api/v1/action-history/{id}/stream/` with an unauthenticated `APIClient`.
  - Asserts the response status is 403 (or 401).

- [x] 3.3 Write a unit test `test_generator_emits_error_event_on_jenkins_failure` that:
  - Calls `_jenkins_progressive_text_generator("job-url", 1)` directly (not via the view).
  - Patches `urllib.request.urlopen` to raise `urllib.error.URLError("connection refused")`.
  - Collects all yielded strings into a list.
  - Asserts the list contains exactly one item starting with `"event: error"`.

- [x] 3.4 Run `pytest tests/test_api_streaming.py -v` and confirm all three tests pass.

## 4. Full suite validation

- [x] 4.1 Run the full test suite with `pytest` from the repo root and confirm all existing tests still pass alongside the new ones. The `test_openapi_drift` test must pass (i.e. `openapi.yaml` was regenerated in task 2.1 before running).
