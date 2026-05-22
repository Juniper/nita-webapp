import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { AppLayout } from '../components/AppLayout'
import { WorkbookGrid, WorkbookSheet } from '../components/WorkbookGrid'
import { apiFetch } from '../api/client'
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
interface CampusNetwork {
  id: number
  name: string
  description: string
  status: string
  campus_type: number
  campus_type_name: string
  host_file: string | null
  dynamic_ansible_workspace: boolean
}

function statusBadge(status: string): string {
  const base = 'px-2 py-0.5 rounded text-xs font-semibold uppercase'
  if (status === 'SUCCESS') return `${base} bg-green-800 text-green-200`
  if (status === 'FAILED' || status === 'FAILURE') return `${base} bg-red-800 text-red-200`
  if (status === 'RUNNING' || status === 'PENDING') return `${base} bg-yellow-800 text-yellow-200`
  return `${base} bg-gray-700 text-gray-300`
}

export function NetworkDetailPage() {
  const { id } = useParams<{ id: string }>()

  const [network, setNetwork] = useState<CampusNetwork | null>(null)
  const [networkError, setNetworkError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'workbook' | 'actions' | 'history'>('workbook')
  const [loaded, setLoaded] = useState({ workbook: false, actions: false, history: false })

  // Workbook tab
  const [workbook, setWorkbook] = useState<WorkbookSheet[] | null>(null)
  const [workbookLoading, setWorkbookLoading] = useState(false)
  const [workbookError, setWorkbookError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [clearConfirm, setClearConfirm] = useState(false)
  const [clearing, setClearing] = useState(false)
  const uploadRef = useRef<HTMLInputElement>(null)

  // Actions tab
  const [actions, setActions] = useState<Action[] | null>(null)
  const [actionsLoading, setActionsLoading] = useState(false)
  const [actionsError, setActionsError] = useState<string | null>(null)
  const [triggerLoading, setTriggerLoading] = useState<number | null>(null)
  const [consoleLines, setConsoleLines] = useState<string[]>([])
  // Streaming state: 'idle' | 'streaming' | 'done' | 'error' | 'timeout'
  const [streamState, setStreamState] = useState<'idle' | 'streaming' | 'done' | 'error' | 'timeout'>('idle')
  const [consoleHistoryId, setConsoleHistoryId] = useState<number | null>(null)
  const consoleRef = useRef<HTMLPreElement>(null)

  // History tab
  const [history, setHistory] = useState<ActionHistory[] | null>(null)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyError, setHistoryError] = useState<string | null>(null)

  // Network fetch on mount
  useEffect(() => {
    apiFetch(`/api/v1/networks/${id}/`)
      .then(r => r.json())
      .then(setNetwork)
      .catch(() => setNetworkError('Failed to load network'))
  }, [id])

  // Tab data loading
  useEffect(() => {
    if (activeTab === 'workbook' && !loaded.workbook) {
      setWorkbookLoading(true)
      setWorkbookError(null)
      apiFetch(`/api/v1/networks/${id}/workbook/`)
        .then(r => r.json())
        .then(d => { setWorkbook(d.workbook); setLoaded(l => ({ ...l, workbook: true })) })
        .catch(() => setWorkbookError('Failed to load workbook'))
        .finally(() => setWorkbookLoading(false))
    }
    if (activeTab === 'actions' && !loaded.actions && network) {
      setActionsLoading(true)
      setActionsError(null)
      apiFetch(`/api/v1/actions/?campus_type_id=${network.campus_type}`)
        .then(r => r.json())
        .then(d => { setActions(d.results ?? d); setLoaded(l => ({ ...l, actions: true })) })
        .catch(() => setActionsError('Failed to load actions'))
        .finally(() => setActionsLoading(false))
    }
    if (activeTab === 'history' && !loaded.history) {
      setHistoryLoading(true)
      setHistoryError(null)
      apiFetch(`/api/v1/action-history/?campus_network_id=${id}`)
        .then(r => r.json())
        .then(d => { setHistory(d.results ?? d); setLoaded(l => ({ ...l, history: true })) })
        .catch(() => setHistoryError('Failed to load history'))
        .finally(() => setHistoryLoading(false))
    }
  }, [activeTab, loaded, id, network])

  // Auto-scroll console
  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight
    }
  }, [consoleLines])

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setUploadError(null)
    const fd = new FormData()
    fd.append('file', file)
    apiFetch(`/api/v1/networks/${id}/workbook/upload/`, { method: 'POST', body: fd })
      .then(r => { if (!r.ok) throw new Error(); return r.json() })
      .then(() => setLoaded(l => ({ ...l, workbook: false })))
      .catch(() => setUploadError('Upload failed'))
      .finally(() => {
        setUploading(false)
        if (uploadRef.current) uploadRef.current.value = ''
      })
  }

  const handleClear = () => {
    setClearing(true)
    apiFetch(`/api/v1/networks/${id}/workbook/clear/`, { method: 'DELETE' })
      .then(() => { setWorkbook([]); setClearConfirm(false) })
      .catch(() => {})
      .finally(() => setClearing(false))
  }

  const handleTrigger = (action: Action) => {
    setTriggerLoading(action.id)
    apiFetch(`/api/v1/networks/${id}/trigger/${action.id}/`, { method: 'POST' })
      .then(r => r.json())
      .then((d: { action_history_id: number; status: string }) => {
        const histId = d.action_history_id
        setConsoleHistoryId(histId)
        setConsoleLines([])
        setStreamState('streaming')
        const es = new EventSource(`/api/v1/action-history/${histId}/stream/`)
        es.onmessage = (e) => {
          setConsoleLines(prev => [...prev, e.data])
        }
        // Named event listeners for clean termination (per SSE spec)
        es.addEventListener('done', () => {
          setStreamState('done')
          es.close()
          setLoaded(l => ({ ...l, history: false }))
        })
        es.addEventListener('error', (e) => {
          setStreamState('error')
          setConsoleLines(prev => [...prev, `[error] ${(e as MessageEvent).data ?? 'stream error'}`])
          es.close()
          setLoaded(l => ({ ...l, history: false }))
        })
        es.addEventListener('timeout', () => {
          setStreamState('timeout')
          setConsoleLines(prev => [...prev, '[timeout] Build stream timed out after 30 minutes.'])
          es.close()
          setLoaded(l => ({ ...l, history: false }))
        })
        // Fallback: network-level error before stream starts
        es.onerror = () => {
          if (es.readyState === EventSource.CLOSED) {
            setStreamState(s => s === 'streaming' ? 'error' : s)
            es.close()
            setLoaded(l => ({ ...l, history: false }))
          }
        }
      })
      .catch(() => {})
      .finally(() => setTriggerLoading(null))
  }

  return (
    <AppLayout>
      <div className="p-6 max-w-6xl mx-auto">
        <Link to="/networks" className="text-indigo-400 hover:text-indigo-300 text-sm mb-4 inline-block">
          ← Networks
        </Link>

        {networkError ? (
          <p className="text-red-400">{networkError}</p>
        ) : !network ? (
          <p className="text-gray-400">Loading…</p>
        ) : (
          <>
            <div className="flex items-center gap-4 mb-6">
              <h1 className="text-2xl font-bold text-white">{network.name}</h1>
              <span className={statusBadge(network.status)}>{network.status}</span>
              <span className="text-gray-400 text-sm">{network.campus_type_name}</span>
            </div>

            {/* Tab bar */}
            <div className="flex border-b border-gray-700 mb-6">
              {(['workbook', 'actions', 'history'] as const).map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2 text-sm font-medium capitalize ${
                    activeTab === tab
                      ? 'border-b-2 border-indigo-500 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* Workbook tab */}
            {activeTab === 'workbook' && (
              <div>
                <div className="flex gap-3 mb-4 flex-wrap">
                  <input
                    ref={uploadRef}
                    type="file"
                    accept=".xlsx,.xls"
                    className="hidden"
                    onChange={handleUpload}
                  />
                  <button
                    onClick={() => uploadRef.current?.click()}
                    disabled={uploading}
                    className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm rounded"
                  >
                    {uploading ? 'Uploading…' : 'Upload Workbook'}
                  </button>
                  <button
                    onClick={() => window.location.assign(`/api/v1/networks/${id}/workbook/download/`)}
                    className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded"
                  >
                    Download
                  </button>
                  {!clearConfirm ? (
                    <button
                      onClick={() => setClearConfirm(true)}
                      className="px-3 py-1.5 bg-red-700 hover:bg-red-600 text-white text-sm rounded"
                    >
                      Clear
                    </button>
                  ) : (
                    <>
                      <button
                        onClick={handleClear}
                        disabled={clearing}
                        className="px-3 py-1.5 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm rounded"
                      >
                        {clearing ? 'Clearing…' : 'Confirm clear'}
                      </button>
                      <button
                        onClick={() => setClearConfirm(false)}
                        className="px-3 py-1.5 bg-gray-600 hover:bg-gray-500 text-white text-sm rounded"
                      >
                        Cancel
                      </button>
                    </>
                  )}
                </div>
                {uploadError && <p className="text-red-400 text-sm mb-3">{uploadError}</p>}
                {workbookLoading ? (
                  <p className="text-gray-400">Loading workbook…</p>
                ) : workbookError ? (
                  <p className="text-red-400">{workbookError}</p>
                ) : workbook && workbook.length === 0 ? (
                  <p className="text-gray-500">No workbook data. Upload an Excel file to get started.</p>
                ) : workbook ? (
                  <WorkbookGrid
                    sheets={workbook}
                    networkId={id!}
                    onSaved={setWorkbook}
                  />
                ) : null}
              </div>
            )}

            {/* Actions tab */}
            {activeTab === 'actions' && (
              <div>
                {actionsLoading ? (
                  <p className="text-gray-400">Loading actions…</p>
                ) : actionsError ? (
                  <p className="text-red-400">{actionsError}</p>
                ) : actions && actions.length === 0 ? (
                  <p className="text-gray-500">No actions defined for this network type.</p>
                ) : actions ? (
                  <>
                    {Array.from(
                      actions.reduce((map, a) => {
                        const cat = a.action_category.category_name
                        if (!map.has(cat)) map.set(cat, [])
                        map.get(cat)!.push(a)
                        return map
                      }, new Map<string, Action[]>())
                    ).sort(([a], [b]) => a.localeCompare(b)).map(([cat, acts]) => (
                      <div key={cat} className="mb-6">
                        <h3 className="text-gray-300 font-semibold text-sm uppercase tracking-wide mb-2">{cat}</h3>
                        <div className="space-y-2">
                          {acts.map(action => (
                            <div key={action.id} className="bg-gray-800 rounded p-3 flex justify-between items-center">
                              <span className="text-white">{action.action_name}</span>
                              <button
                                onClick={() => handleTrigger(action)}
                                disabled={triggerLoading === action.id || streamState === 'streaming'}
                                className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm rounded"
                              >
                                {triggerLoading === action.id ? 'Running…' : 'Run'}
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </>
                ) : null}

                {/* Console pane */}
                {consoleHistoryId !== null && (
                  <div className="mt-6">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-300 text-sm font-medium">
                        Console {streamState === 'streaming' ? '(streaming…)' : streamState === 'timeout' ? '(timed out)' : streamState === 'error' ? '(error)' : '(done)'}
                      </span>
                      <button
                        onClick={() => { setConsoleHistoryId(null); setConsoleLines([]) }}
                        className="text-gray-500 hover:text-white text-xs"
                      >
                        Close
                      </button>
                    </div>
                    <pre
                      ref={consoleRef}
                      className="bg-black text-green-400 font-mono text-sm p-4 rounded overflow-y-auto"
                      style={{ maxHeight: 400 }}
                    >
                      {consoleLines.join('\n')}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {/* History tab */}
            {activeTab === 'history' && (
              <div>
                {historyLoading ? (
                  <p className="text-gray-400">Loading history…</p>
                ) : historyError ? (
                  <p className="text-red-400">{historyError}</p>
                ) : history && history.length === 0 ? (
                  <p className="text-gray-500">No actions have been run for this network.</p>
                ) : history ? (
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-gray-400 text-left border-b border-gray-700">
                        <th className="pb-2 pr-4">Action</th>
                        <th className="pb-2 pr-4">Category</th>
                        <th className="pb-2 pr-4">Status</th>
                        <th className="pb-2">Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.map(h => (
                        <tr key={h.id} className="border-b border-gray-800 text-white">
                          <td className="py-2 pr-4">{h.action_name}</td>
                          <td className="py-2 pr-4 text-gray-400">{h.category_name}</td>
                          <td className="py-2 pr-4"><span className={statusBadge(h.status)}>{h.status}</span></td>
                          <td className="py-2 text-gray-400">{new Date(h.timestamp).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : null}
              </div>
            )}
          </>
        )}
      </div>
    </AppLayout>
  )
}
