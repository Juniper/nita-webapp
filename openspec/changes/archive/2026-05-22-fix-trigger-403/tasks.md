## 1. Backend: LabSessionAuthentication

- [x] 1.1 Create `build-and-test-webapp/nita-webapp/ngcn_workbench/ngcn/api/authentication.py` with `LabSessionAuthentication` that subclasses `rest_framework.authentication.SessionAuthentication` and overrides `enforce_csrf` to use `LabCsrfMiddleware` via an inner `_LabCSRFCheck` class
- [x] 1.2 Update `DEFAULT_AUTHENTICATION_CLASSES` in `build-and-test-webapp/nita-webapp/ngcn_workbench/ngcn_workbench/settings.py` to reference `ngcn.api.authentication.LabSessionAuthentication`

## 2. Backend: SSE Generator 404 Retry

- [x] 2.1 In `build-and-test-webapp/nita-webapp/ngcn_workbench/ngcn/api/views.py`, add `queued_polls` counter (max 60) to `_jenkins_progressive_text_generator`; on `urllib.error.HTTPError` with `code == 404` increment counter, sleep 1 s, and `continue`; after 60 retries fall through to the existing `event: error` yield

## 3. Frontend: Remove CSRF Token Cache

- [x] 3.1 In `frontend/src/api/client.ts`, replace the `csrfTokenCache` in-memory variable with a `readCsrfCookie()` helper that reads `csrftoken` directly from `document.cookie`; update `getCsrfToken()` to call `readCsrfCookie()` first and only fetch `/api/v1/auth/csrf/` as a fallback when the cookie is absent
- [x] 3.2 Make `clearCsrfCache()` a no-op (keep the export for backward compatibility with call sites in `NetworkDetailPage.tsx`)

## 4. Verification

- [x] 4.1 Run `npm run build` inside `frontend/` and confirm no TypeScript errors
- [x] 4.2 Build and load the webapp container image, confirm Django starts without import errors (`LabSessionAuthentication` loads successfully)
- [x] 4.3 Confirm Jenkins `basic-security.groovy` logs "NITA Jenkins security configured: Unsecured strategy, CSRF disabled" on pod start (Jenkins CSRF is disabled — prerequisite for trigger requests)
- [ ] 4.4 Log in to the SPA, trigger a job, and confirm the console panel streams live output and reaches the `done` state; verify no 403 is returned on the trigger POST
- [ ] 4.5 Confirm triggering a second job immediately after login (without page reload) also succeeds — validating the no-stale-cache fix
