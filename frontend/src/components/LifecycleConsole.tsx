import { useEffect, useRef } from 'react'
import { stateLabel } from './lifecycle-stream'
import type { StreamState } from './lifecycle-stream'

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
