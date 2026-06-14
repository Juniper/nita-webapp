import { useCallback, useEffect, useRef, useState } from 'react'

export type StreamState = 'idle' | 'streaming' | 'done' | 'error' | 'timeout'

/** Build the generic lifecycle console stream URL for a Jenkins job build. */
export function lifecycleStreamUrl(jobName: string, buildNo: number): string {
  return `/api/v1/jenkins/jobs/${encodeURIComponent(jobName)}/${buildNo}/stream/`
}

/**
 * Hook that manages an EventSource stream of a Jenkins job's console output.
 *
 * Mirrors the streaming behaviour used on the network detail page: named
 * `done`/`error`/`timeout` listeners plus the default `message` handler.
 */
export function useJenkinsStream() {
  const [lines, setLines] = useState<string[]>([])
  const [state, setState] = useState<StreamState>('idle')
  const esRef = useRef<EventSource | null>(null)

  const close = useCallback(() => {
    if (esRef.current) {
      esRef.current.close()
      esRef.current = null
    }
  }, [])

  const reset = useCallback(() => {
    close()
    setLines([])
    setState('idle')
  }, [close])

  const start = useCallback((jobName: string, buildNo: number) => {
    close()
    setLines([])
    setState('streaming')
    const es = new EventSource(lifecycleStreamUrl(jobName, buildNo))
    esRef.current = es
    es.onmessage = e => {
      if (e.data) setLines(prev => [...prev, e.data])
    }
    es.addEventListener('done', () => {
      setState('done')
      es.close()
      esRef.current = null
    })
    es.addEventListener('error', (e: MessageEvent) => {
      // A network-level error event carries no data; ignore it so the browser
      // can retry. A server-sent `error` event carries a message.
      if (!e.data) return
      setLines(prev => [...prev, e.data])
      setState('error')
      es.close()
      esRef.current = null
    })
    es.addEventListener('timeout', () => {
      setState('timeout')
      es.close()
      esRef.current = null
    })
    es.onerror = () => {
      // Connection dropped; if we never reached a terminator mark as error.
      setState(prev => (prev === 'streaming' ? 'error' : prev))
    }
  }, [close])

  // Clean up on unmount.
  useEffect(() => close, [close])

  return { lines, state, start, reset, close }
}

function stateLabel(state: StreamState): string {
  switch (state) {
    case 'streaming':
      return '(streaming…)'
    case 'timeout':
      return '(timed out)'
    case 'error':
      return '(error)'
    default:
      return '(done)'
  }
}

interface LifecycleConsolePanelProps {
  title?: string
  lines: string[]
  state: StreamState
  onClose: () => void
}

/** Live console panel rendered while a lifecycle job is streaming. */
export function LifecycleConsolePanel({
  title = 'Console',
  lines,
  state,
  onClose,
}: LifecycleConsolePanelProps) {
  const consoleRef = useRef<HTMLPreElement>(null)

  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight
    }
  }, [lines])

  return (
    <div className="mt-6">
      <div className="flex justify-between items-center mb-2">
        <span className="text-gray-300 text-sm font-medium">
          {title} {stateLabel(state)}
        </span>
        <button
          onClick={onClose}
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
        {lines.join('\n')}
      </pre>
    </div>
  )
}
