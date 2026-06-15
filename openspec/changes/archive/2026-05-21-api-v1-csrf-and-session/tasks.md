## 1. Implement the four auth views

- [x] 1.1 In `ngcn/api/views.py`, add the CSRF endpoint:
  ```python
  from django.middleware.csrf import get_token
  from rest_framework.decorators import api_view, permission_classes
  from rest_framework.permissions import AllowAny

  @extend_schema(
      responses={200: {"type": "object", "properties": {"csrfToken": {"type": "string"}}}},
      auth=[],
  )
  @api_view(["GET"])
  @permission_classes([AllowAny])
  def csrf_view(request):
      """Return the CSRF token. No authentication required."""
      return Response({"csrfToken": get_token(request)})
  ```

- [x] 1.2 In `ngcn/api/views.py`, add the login endpoint:
  ```python
  from django.contrib.auth import authenticate, login as auth_login

  @extend_schema(
      request={"application/json": {"type": "object", "properties": {
          "username": {"type": "string"},
          "password": {"type": "string"},
      }, "required": ["username", "password"]}},
      responses={
          200: {"type": "object", "properties": {
              "id": {"type": "integer"},
              "username": {"type": "string"},
              "is_superuser": {"type": "boolean"},
          }},
          400: OpenApiResponse(description="Invalid credentials"),
      },
      auth=[],
  )
  @api_view(["POST"])
  @permission_classes([AllowAny])
  def login_view(request):
      """Authenticate and open a Django session."""
      username = request.data.get("username", "")
      password = request.data.get("password", "")
      user = authenticate(request, username=username, password=password)
      if user is None:
          return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)
      auth_login(request, user)
      return Response({"id": user.pk, "username": user.username, "is_superuser": user.is_superuser})
  ```

- [x] 1.3 In `ngcn/api/views.py`, add the logout endpoint:
  ```python
  from django.contrib.auth import logout as auth_logout

  @extend_schema(responses={204: None})
  @api_view(["POST"])
  def logout_view(request):
      """Destroy the current session. Authentication required."""
      auth_logout(request)
      return Response(status=status.HTTP_204_NO_CONTENT)
  ```

- [x] 1.4 In `ngcn/api/views.py`, add the me endpoint:
  ```python
  @extend_schema(
      responses={200: {"type": "object", "properties": {
          "id": {"type": "integer"},
          "username": {"type": "string"},
          "is_superuser": {"type": "boolean"},
      }}}
  )
  @api_view(["GET"])
  def me_view(request):
      """Return the authenticated user's info."""
      user = request.user
      return Response({"id": user.pk, "username": user.username, "is_superuser": user.is_superuser})
  ```

## 2. Wire up URL routing

- [x] 2.1 In `ngcn/api/urls.py`, import the four new views and add explicit URL paths for them:
  ```python
  from django.urls import path
  from .views import csrf_view, login_view, logout_view, me_view

  urlpatterns = router.urls + [
      path("auth/csrf/", csrf_view, name="auth-csrf"),
      path("auth/login/", login_view, name="auth-login"),
      path("auth/logout/", logout_view, name="auth-logout"),
      path("auth/me/", me_view, name="auth-me"),
  ]
  ```
  Confirm that `POST /api/v1/auth/login/` and `POST /api/v1/auth/logout/` are served independently of the existing `POST /api/v1/auth/token/` in `ngcn_workbench/urls.py`.

## 3. Regenerate openapi.yaml

- [x] 3.1 From `build-and-test-webapp/nita-webapp/ngcn_workbench/`, run:
  ```
  DJANGO_SETTINGS_MODULE=ngcn_workbench.test_settings python3 manage.py spectacular --file /home/jcluser/nita-webapp/openapi.yaml
  ```
- [x] 3.2 Confirm the regenerated `openapi.yaml` contains paths for all four new endpoints:
  - `/api/v1/auth/csrf/`
  - `/api/v1/auth/login/`
  - `/api/v1/auth/logout/`
  - `/api/v1/auth/me/`

## 4. Write tests

- [x] 4.1 Create `tests/test_api_session_auth.py` with:
  - `test_csrf_endpoint_returns_token` — GET `/api/v1/auth/csrf/` without auth → 200, response has non-empty `csrfToken`.
  - `test_login_valid_credentials_returns_user` — POST `/api/v1/auth/login/` with valid credentials and CSRF header → 200, response contains `id`, `username`, `is_superuser`.
  - `test_login_invalid_credentials_returns_400` — POST with bad password → 400.
  - `test_logout_authenticated_returns_204` — authenticated POST `/api/v1/auth/logout/` → 204.
  - `test_logout_unauthenticated_returns_403` — unauthenticated POST `/api/v1/auth/logout/` → 403.
  - `test_me_authenticated_returns_user` — authenticated GET `/api/v1/auth/me/` → 200, contains `id`, `username`, `is_superuser`.
  - `test_me_unauthenticated_returns_403` — unauthenticated GET `/api/v1/auth/me/` → 403.

- [x] 4.2 Run `pytest tests/test_api_session_auth.py -v` and confirm all 7 tests pass.

## 5. Full suite validation

- [x] 5.1 Run the full test suite:
  ```
  cd /home/jcluser/nita-webapp && DJANGO_SETTINGS_MODULE=ngcn_workbench.test_settings pytest -v
  ```
  Confirm all existing tests still pass alongside the new ones. The `test_openapi_drift` test must pass (openapi.yaml was regenerated in task 3.1).
