# Architecture

Contributor-facing overview of how the NITA webapp fits together. For install
and usage see [README.md](README.md); for image builds see [BUILD.md](BUILD.md).

## Request flow

Everything is served through a single NGINX endpoint on port 443.

```
                    ┌────────────────────────────────────────┐
   https://<host>/  │                NGINX                   │
   ─────────────────▶  (nginx/nginx.conf, TLS termination)   │
                    └───┬───────────────┬────────────────┬───┘
                        │               │                │
              /jenkins/ │               │ /api/v1/...    │ /  (+ SPA routes)
                        ▼               ▼                ▼
                  ┌──────────┐   ┌─────────────────────────────┐
                  │ Jenkins  │   │          Django             │
                  │  :8080   │   │  REST API  +  SPA index.html│
                  │ --prefix │   └──────────────┬──────────────┘
                  │ /jenkins │                  │
                  └──────────┘                  ▼
                                          ┌──────────┐
                                          │ MariaDB  │
                                          └──────────┘
```

Django serves the compiled SPA `index.html` for the root and an explicit
allowlist of client-side routes (`login`, `network-types`, `networks`, `users`,
`teams`, and their subpaths), so deep links and refreshes resolve correctly. All
other paths belong to the backend (`api/`, `admin/`, `assets/`, `jenkins/`,
`api/schema`, `api/docs`). Adding a new top-level SPA route means adding it to
that allowlist in `ngcn_workbench/urls.py` as well as to the React router.

Jenkins is **not** exposed on its own port. It runs with `--prefix=/jenkins` so
it emits correctly-prefixed URLs, and NGINX proxies `/jenkins/` to it. Backend
callers build Jenkins URLs from a single canonical prefixed base
(`jenkins_config.JENKINS_SERVER_URL`) — duplicating that string is what
previously caused action-history rows to stick at `Running`.

## Backend layout

```
build-and-test-webapp/nita-webapp/ngcn_workbench/
  ngcn_workbench/settings.py   settings, DRF + drf-spectacular config
  ngcn_workbench/urls.py       root routing, SPA fallback, token endpoint
  ngcn/models.py               User, Team, CampusType, CampusNetwork, Action, ...
  ngcn/api/urls.py             DefaultRouter under /api/v1/
  ngcn/api/views.py            viewsets and actions
  ngcn/api/serializers.py      serializers and field-level validation
  ngcn/api/permissions.py      role-based permission classes
  ngcn/api/schema_hooks.py     OpenAPI post-processing
  ngcn/jenkins_jobs.py         Jenkins invocation and log streaming
  tests/                       pytest suite
```

## Authentication

Two mechanisms share the same API:

- **Token** — `POST /api/v1/auth/token/` returns a DRF token for scripts/CLI,
  sent as `Authorization: Token <token>`.
- **Session** — the SPA uses `POST /api/v1/auth/login/` plus a CSRF token from
  `GET /api/v1/auth/csrf/`. `GET /api/v1/auth/me/` returns the caller's `role`
  and `teams`, which drives role-gated UI.

## Authorization

Access control is driven entirely by `User.role` (`user`, `power_user`,
`admin`). Django's `is_staff` / `is_superuser` flags gate the Django admin panel
only and are deliberately not consulted by the API.

Permission classes live in `ngcn/api/permissions.py`:

| Class | Grants |
|---|---|
| `IsAdminRole` | `role == admin` |
| `IsPowerUserOrAdmin` | `role in (power_user, admin)` |
| `IsOwnerOrAdmin` | object `owner`/`created_by` matches the caller, or admin |
| `IsOwnerOrTeamMemberOrAdmin` | networks: power_user/admin full; owner read+write; team member read-only |
| `IsAdminOrManagesNonAdminUser` | admin any user; power_user any **non-admin** user |

Viewsets select them per action via `get_permissions()`, and narrow the queryset
in `get_queryset()` (for example, a `power_user` listing users does not see
`admin` accounts). Two rules are enforced in view code rather than a permission
class because they depend on the request body or on aggregate state:

- a `power_user` may not set `role=admin`;
- an operation may not leave zero active administrators.

Destructive operations that would orphan or silently remove data return
`409 Conflict` with the blocking resources listed — deleting a user who still
owns networks/types, and deleting a network type still referenced by networks.

## API schema

`drf-spectacular` generates the OpenAPI document; `openapi.yaml` at the repo
root is committed and **must** be regenerated whenever the API surface changes:

```bash
cd build-and-test-webapp/nita-webapp/ngcn_workbench
DJANGO_SETTINGS_MODULE=ngcn_workbench.test_settings \
  python3 manage.py spectacular --file ../../../openapi.yaml
```

`tests/test_openapi_drift.py` fails if the committed file drifts from the live
schema. Post-processing hooks in `ngcn/api/schema_hooks.py` bound array sizes,
declare a document-level security requirement, and drop empty operation-level
`security` entries so the schema passes static analysis.

## Frontend

The SPA lives in `frontend/` and is built into the image by the Docker
`frontend-builder` stage. See [frontend/README.md](frontend/README.md) for its
structure and conventions.

## Testing and CI

```bash
pytest -q                      # backend suite (repo root)
cd frontend && npm run lint    # frontend lint (enforced in CI)
cd frontend && npm run build   # tsc -b && vite build
```

The pull-request workflow runs super-linter (Python Black plus legacy JS),
Microsoft Security DevOps, the Django pytest suite, the frontend ESLint gate,
and a container image build.

## Spec-driven workflow

Behaviour is specified before it is implemented. `openspec/specs/<capability>/`
holds the current requirements; a proposed change lives in
`openspec/changes/<name>/` (proposal, design, tasks, and spec deltas) and is
moved to `openspec/changes/archive/<date>-<name>/` once its deltas have been
merged back into the main specs. When changing behaviour, update the relevant
capability spec in the same change.
