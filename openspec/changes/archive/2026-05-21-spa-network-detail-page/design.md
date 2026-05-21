# Design: spa-network-detail-page

## Page Structure

```
/app/networks/:id
├── Back link  "← Networks"
├── Network header  (name · type · status badge)
├── Tab bar  [ Workbook | Actions | History ]
└── Tab panels
    ├── Workbook panel
    ├── Actions panel
    └── History panel
```

## Data Sources

| Resource | Endpoint | Method |
|---|---|---|
| Network detail | `GET /api/v1/networks/{id}/` | on mount |
| Workbook data | `GET /api/v1/networks/{id}/workbook/` | on Workbook tab open |
| Upload workbook | `POST /api/v1/networks/{id}/workbook/upload/` | user action |
| Save workbook | `POST /api/v1/networks/{id}/workbook/save/` | (future) |
| Clear workbook | `DELETE /api/v1/networks/{id}/workbook/clear/` | user action |
| Download workbook | `GET /api/v1/networks/{id}/workbook/download/` | user action |
| Actions list | `GET /api/v1/actions/?campus_type_id={campus_type}` | on Actions tab open |
| Trigger action | `POST /api/v1/networks/{id}/trigger/{action_id}/` | user action |
| Action history | `GET /api/v1/action-history/?campus_network_id={id}` | on History tab open |
| SSE stream | `GET /api/v1/action-history/{history_id}/stream/` | after trigger |

## Component Layout (single file)

All logic stays in `NetworkDetailPage.tsx` — no sub-components needed.  State is managed with `useState` + `useEffect` hooks.

```
NetworkDetailPage
  ├── Header section  (network fetch on mount)
  ├── TabBar  (activeTab state: 'workbook' | 'actions' | 'history')
  ├── WorkbookPanel
  │   ├── Upload button  (file input ref)
  │   ├── Sheet list     (name + row count if data is array)
  │   ├── Download button
  │   └── Clear button   (inline confirm)
  ├── ActionsPanel
  │   ├── Action groups  (grouped by category_name)
  │   │   └── Trigger button per action
  │   └── Console pane   (fixed-height <pre>, visible when streaming)
  └── HistoryPanel
      └── Table (action_name, category_name, timestamp, status)
```

## Key Design Decisions

### SSE Streaming
Use `EventSource` — the browser API for SSE — rather than `fetch` + `ReadableStream`. `EventSource` automatically attaches cookies (session auth), makes same-origin streaming trivial, and handles reconnect. Append each `event.data` line to a `consoleLines` state array. On stream close (`onmessage` fires an empty/done event, or `onerror` fires after server closes), mark streaming as complete.

Lifecycle:
1. User clicks Trigger → POST → get `action_history_id`
2. Open `new EventSource(url)` → `consoleLines = []`
3. `onmessage`: append `event.data` to lines
4. `onerror` with `eventSource.readyState === EventSource.CLOSED`: mark done
5. Cleanup on unmount: `eventSource.close()`

### Workbook Display
The workbook response is `{ status, workbook: [{ name, data }] }` where `data` can be `object | array | string`. Display a summary card per sheet showing the sheet name and, when `data` is an array, the row count. Full grid editing is out of scope.

### Download
`GET /api/v1/networks/{id}/workbook/download/` streams a binary `.xlsx`. Trigger it via `window.location.assign(url)` — simplest approach that respects session cookies and prompts the browser's download dialog.

### Actions Grouping
Actions have `action_category: { id, category_name }`. Group by `category_name` using a `Map` built once after fetch.

### Tab Loading
Each tab loads its data lazily on first activation, tracked with `loaded.workbook / loaded.actions / loaded.history` flags to avoid redundant fetches.

## State Shape

```ts
network: CampusNetwork | null       // header
workbook: WorkbookSheet[] | null    // workbook tab
actions: Action[] | null            // actions tab
history: ActionHistory[] | null     // history tab
activeTab: 'workbook' | 'actions' | 'history'
loaded: { workbook: boolean; actions: boolean; history: boolean }
uploading: boolean
uploadError: string | null
clearConfirm: boolean
clearing: boolean
triggerLoading: number | null       // action_id being triggered
consoleLines: string[]
streaming: boolean
consoleHistoryId: number | null
```

## Types

```ts
interface WorkbookSheet { name: string; data: unknown }
interface Action {
  id: number
  action_name: string
  action_category: { id: number; category_name: string }
  action_property: { id: number; shell_command: string; output_path: string | null; custom_workspace: string | null }
  jenkins_url: string
}
interface ActionHistory {
  id: number
  action_name: string
  category_name: string
  network_name: string
  timestamp: string
  status: string
  action_id: number
  category_id: number
  campus_network_id: number
  jenkins_job_build_no: number
}
```
