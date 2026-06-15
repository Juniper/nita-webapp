# Spec: spa-network-detail-page

## NetworkDetailPage Component

**File**: `frontend/src/pages/NetworkDetailPage.tsx`

### Props / Route

Receives `id` via `useParams<{ id: string }>()`.

### Behaviour

#### On mount
- Fetch `GET /api/v1/networks/{id}/` → set `network`; on error set `error`

#### Tab switching
- `activeTab` defaults to `'workbook'`
- On first activation of each tab, fetch its data (lazy, tracked via `loaded` flags)

#### Workbook tab

**Upload**
- Hidden `<input type="file" accept=".xlsx,.xls">` with a ref
- "Upload Workbook" button clicks the ref
- On file selected: `POST /api/v1/networks/{id}/workbook/upload/` as `FormData` with field `file`; `apiFetch` with `method:'POST', body: formData` (no `Content-Type` header — let browser set multipart boundary)
- On success: reload workbook data (`loaded.workbook = false`, re-fetch)
- Show `uploading` spinner on button; show `uploadError` below if failed

**Display**
- If `workbook` is null and not loaded: show spinner
- If `workbook.length === 0`: show "No workbook data. Upload an Excel file to get started."
- Otherwise: a card list — each sheet shows `name` and, if `data` is an array, `{data.length} rows`

**Download**
- "Download" button: call `window.location.assign('/api/v1/networks/{id}/workbook/download/')` — browser handles binary download

**Clear**
- "Clear" button → set `clearConfirm = true` → inline confirm renders "Confirm clear" and "Cancel" buttons
- On confirm: `DELETE /api/v1/networks/{id}/workbook/clear/` → set `workbook = []`, `clearConfirm = false`

#### Actions tab

**Load**
- Fetch `GET /api/v1/actions/?campus_type_id={network.campus_type}` → set `actions`
- Group by `action_category.category_name`

**Display**
- One section per category (sorted alphabetically by category name)
- Each action: name in text, "Run" button on the right
- While `triggerLoading === action.id`: button shows "Running…" and is disabled

**Trigger**
- POST `apiFetch('/api/v1/networks/{id}/trigger/{action_id}/', { method:'POST' })`
- On 202 response: set `consoleHistoryId = action_history_id`, `consoleLines = []`, `streaming = true`
- Open `new EventSource('/api/v1/action-history/{action_history_id}/stream/')`
- `onmessage`: append `e.data` to `consoleLines`
- `onerror` (when `es.readyState === EventSource.CLOSED`): set `streaming = false`, close
- Console pane: `<pre>` with `overflow-y: auto`, max height 400px; auto-scrolls to bottom on new lines (via `ref` + `scrollTop = scrollHeight`)
- Console pane visible whenever `consoleHistoryId !== null`
- "Close console" button clears `consoleHistoryId` and `consoleLines`

#### History tab

**Load**
- Fetch `GET /api/v1/action-history/?campus_network_id={id}`
- Paginated response — use `.results` array

**Display**
- Table columns: Action | Category | Status | Date
- `timestamp` formatted with `new Date(ts).toLocaleString()`
- `status` shown as a badge: green for `SUCCESS`, red for `FAILED`, yellow for `RUNNING`/`PENDING`, grey for others
- Empty state: "No actions have been run for this network."

#### Error states
- Network fetch fails → show error message with "Back to Networks" link
- Individual tab fetches fail → show inline error within the tab

### Styling
- Dark mode (Tailwind dark: prefix with class strategy already configured)
- Header: `text-2xl font-bold text-white`; status badge: `px-2 py-0.5 rounded text-xs font-semibold`
- Tab bar: `flex border-b border-gray-700`; active tab: `border-b-2 border-indigo-500 text-white`
- Console pane: `bg-black text-green-400 font-mono text-sm p-4 rounded overflow-y-auto`
