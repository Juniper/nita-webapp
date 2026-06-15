## 1. Scaffold the Vite + React + TypeScript project

- [x] 1.1 From the repo root, create the `frontend/` directory using Vite's scaffolding:
  ```bash
  npm create vite@latest frontend -- --template react-ts
  ```
  Confirm `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, and `frontend/src/` exist.

- [x] 1.2 Install npm dependencies:
  ```bash
  cd frontend && npm install
  ```

- [x] 1.3 Install Tailwind CSS and its peer dependencies:
  ```bash
  cd frontend && npm install -D tailwindcss postcss autoprefixer && npx tailwindcss init -p
  ```

- [x] 1.4 Add `frontend/node_modules/` to the repo root `.gitignore` (without disturbing existing entries).

## 2. Configure Tailwind CSS

- [x] 2.1 Update `frontend/tailwind.config.ts` (or `.js`):
  - Set `darkMode: 'class'`.
  - Set `content` to `["./index.html", "./src/**/*.{ts,tsx}"]`.

- [x] 2.2 Replace `frontend/src/index.css` content with the three Tailwind directives:
  ```css
  @tailwind base;
  @tailwind components;
  @tailwind utilities;
  ```

- [x] 2.3 In `frontend/src/main.tsx`, add `document.documentElement.classList.add('dark')` before the `ReactDOM.createRoot(...)` call so dark mode is active by default.

## 3. Configure Vite dev proxy

- [x] 3.1 Update `frontend/vite.config.ts` to add a server proxy:
  ```ts
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  ```

## 4. Create the CSRF-aware API client

- [x] 4.1 Create `frontend/src/api/client.ts` that:
  - Maintains a module-level `csrfTokenCache: string | null`.
  - Exports an `async function apiFetch(path: string, options?: RequestInit): Promise<Response>` that:
    - Always includes `credentials: 'include'`.
    - For non-GET methods, calls `GET /api/v1/auth/csrf/` (once, caching the result) and attaches the value as the `X-CSRFToken` header.

## 5. Create AuthContext

- [x] 5.1 Create `frontend/src/context/AuthContext.tsx` that:
  - Defines a `User` interface: `{ id: number; username: string; is_superuser: boolean }`.
  - Exports an `AuthContext` with value type `{ user: User | null; loading: boolean; setUser: (u: User | null) => void; logout: () => Promise<void> }`.
  - Exports an `AuthProvider` component that on mount calls `GET /api/v1/auth/me/` via `apiFetch`. If 200, sets `user`; otherwise, sets `user = null`. The `logout()` method calls `POST /api/v1/auth/logout/` then sets `user = null`.
  - Exports a `useAuth()` hook: `useContext(AuthContext)`.

## 6. Create page components and routing

- [x] 6.1 Create `frontend/src/components/ProtectedRoute.tsx` — wraps a route, checks `useAuth().user`; if null and not loading, redirects to `/login`.

- [x] 6.2 Create `frontend/src/pages/LoginPage.tsx`:
  - Renders a centered dark-mode form with username and password fields and a submit button.
  - On submit, calls `POST /api/v1/auth/login/` via `apiFetch` with `{ username, password }`.
  - On 200, calls `setUser(data)` from `useAuth()` and navigates to `/`.
  - On error, displays the `detail` message from the response.

- [x] 6.3 Create `frontend/src/pages/DashboardPage.tsx`:
  - Renders the logged-in username and a "Log out" button.
  - Clicking logout calls `useAuth().logout()` then navigates to `/login`.

- [x] 6.4 Update `frontend/src/App.tsx` to:
  - Wrap the entire tree in `<AuthProvider>`.
  - Use `<BrowserRouter>` with `<Routes>`:
    - `<Route path="/login" element={<LoginPage />} />`
    - `<Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />`
  - Remove the Vite default content.

- [x] 6.5 Install `react-router-dom`:
  ```bash
  cd frontend && npm install react-router-dom
  ```

## 7. Verify the build

- [x] 7.1 Run a production build and confirm it succeeds with no TypeScript errors:
  ```bash
  cd /home/jcluser/nita-webapp/frontend && npm run build
  ```
  Confirm exit code 0 and `dist/index.html` exists.

- [x] 7.2 Confirm `frontend/dist/index.html` exists:
  ```bash
  ls /home/jcluser/nita-webapp/frontend/dist/index.html
  ```
