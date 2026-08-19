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

  const startUrl = useCallback((url: string) => {
    close()
    setLines([])
    setState('streaming')
    const es = new EventSource(url)
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

  const start = useCallback((jobName: string, buildNo: number) => {
    startUrl(lifecycleStreamUrl(jobName, buildNo))
  }, [startUrl])

  // Clean up on unmount.
  useEffect(() => close, [close])

  return { lines, state, start, startUrl, reset, close }
}

export function stateLabel(state: StreamState): string {
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
