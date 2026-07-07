import { useEffect, useRef, useState } from 'react'
import { apiFetch } from '../api/client'
import { useJenkinsStream, stateLabel } from './LifecycleConsole'

export interface LifecycleRun {
  id: string
  kind: string
  subject: string
  job_name: string
  build_no: number
  timestamp: string
  status: string
}

interface PaginatedLifecycleRuns {
  count: number
  next: string | null
  previous: string | null
  results: LifecycleRun[]
}

const KIND_LABELS: Record<string, string> = {
  network_create: 'Create',
  network_delete: 'Delete',
  network_type_load: 'Load',
}

interface LifecycleHistoryModalProps {
  title: string
  /** Lifecycle kinds to display (e.g. ['network_create', 'network_delete']). */
  kinds: string[]
  onClose: () => void
}

/**
 * Modal listing lifecycle job runs with a per-run live console viewer.
 *
 * Fetches `GET /api/v1/lifecycle-runs/` (one request per kind, merged and
 * sorted newest-first) and, on demand, opens a live SSE stream of the run's
 * Jenkins console via `GET /api/v1/jenkins/jobs/{job_name}/{build_no}/stream/`
 * (which replays a finished build's full log and then completes).
 */
export function LifecycleHistoryModal({ title, kinds, onClose }: LifecycleHistoryModalProps) {
  const [runs, setRuns] = useState<LifecycleRun[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [consoleRun, setConsoleRun] = useState<LifecycleRun | null>(null)
  const {
    lines: consoleLines,
    state: consoleState,
    start: startConsoleStream,
    reset: resetConsoleStream,
  } = useJenkinsStream()
  const consoleRef = useRef<HTMLPreElement>(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const responses = await Promise.all(
          kinds.map(k =>
            apiFetch(`/api/v1/lifecycle-runs/?kind=${encodeURIComponent(k)}`).then(res => {
              if (!res.ok) throw new Error(`Failed to load history: ${res.status}`)
              return res.json() as Promise<PaginatedLifecycleRuns | LifecycleRun[]>
            })
          )
        )
        if (cancelled) return
        const merged = responses
          .flatMap(r => (Array.isArray(r) ? r : r.results))
          .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
        setRuns(merged)
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load history')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [kinds])

  function viewConsole(run: LifecycleRun) {
    setConsoleRun(run)
    startConsoleStream(run.job_name, run.build_no)
  }

  function closeConsole() {
    resetConsoleStream()
    setConsoleRun(null)
  }

  // Auto-scroll the console viewer as lines stream in.
  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight
    }
  }, [consoleLines])

  function handleClose() {
    resetConsoleStream()
    onClose()
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      onClick={handleClose}
    >
      <div
        className="bg-gray-900 border border-gray-700 rounded-lg w-full max-w-4xl max-h-[85vh] flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex justify-between items-center px-4 py-3 border-b border-gray-700">
          <span className="text-white font-medium text-sm">{title}</span>
          <button onClick={handleClose} className="text-gray-400 hover:text-white text-sm">
            Close
          </button>
        </div>
        <div className="p-4 overflow-y-auto">
          {consoleRun ? (
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-white text-sm font-medium">
                  Console — {consoleRun.subject} #{consoleRun.build_no} {stateLabel(consoleState)}
                </span>
                <button
                  onClick={closeConsole}
                  className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white text-xs rounded"
                >
                  Back
                </button>
              </div>
              {consoleState === 'error' ? (
                <p className="text-red-400 text-sm">Failed to load console output</p>
              ) : consoleState === 'timeout' ? (
                <p className="text-yellow-400 text-sm">Console stream timed out.</p>
              ) : consoleLines.length === 0 && consoleState === 'streaming' ? (
                <p className="text-gray-400 text-sm">Loading console output…</p>
              ) : consoleLines.length === 0 ? (
                <p className="text-gray-400 text-sm">No console output available.</p>
              ) : (
                <pre
                  ref={consoleRef}
                  className="bg-black text-green-400 font-mono text-sm p-4 rounded whitespace-pre-wrap overflow-y-auto"
                  style={{ maxHeight: '60vh' }}
                >
                  {consoleLines.join('\n')}
                </pre>
              )}
            </div>
          ) : loading ? (
            <p className="text-gray-400 text-sm">Loading history…</p>
          ) : error ? (
            <p className="text-red-400 text-sm">{error}</p>
          ) : runs && runs.length === 0 ? (
            <p className="text-gray-500 text-sm">No history available.</p>
          ) : runs ? (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-400 text-left border-b border-gray-700">
                  <th className="pb-2 pr-4">Subject</th>
                  <th className="pb-2 pr-4">Action</th>
                  <th className="pb-2 pr-4">Status</th>
                  <th className="pb-2 pr-4">Date</th>
                  <th className="pb-2"></th>
                </tr>
              </thead>
              <tbody>
                {runs.map(r => (
                  <tr key={r.id} className="border-b border-gray-800 text-white">
                    <td className="py-2 pr-4">{r.subject}</td>
                    <td className="py-2 pr-4 text-gray-400">{KIND_LABELS[r.kind] ?? r.kind}</td>
                    <td className="py-2 pr-4 text-gray-400">{r.status}</td>
                    <td className="py-2 pr-4 text-gray-400">
                      {new Date(r.timestamp).toLocaleString()}
                    </td>
                    <td className="py-2 text-right">
                      <button
                        onClick={() => viewConsole(r)}
                        className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white text-xs rounded"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
        </div>
      </div>
    </div>
  )
}
