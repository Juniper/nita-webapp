import { useState } from 'react'
import { apiFetch } from '../api/client'
import { PasswordField } from './PasswordField'

interface SetPasswordDialogProps {
  userId: number
  username: string
  onCancel: () => void
  onDone: () => void
}

/** Flatten a DRF validation error body into a single readable string. */
function formatErrors(data: unknown): string {
  if (data && typeof data === 'object') {
    const parts: string[] = []
    for (const [field, val] of Object.entries(data as Record<string, unknown>)) {
      const msg = Array.isArray(val) ? val.join(' ') : String(val)
      parts.push(field === 'detail' ? msg : `${field}: ${msg}`)
    }
    if (parts.length) return parts.join('\n')
  }
  return 'Reset failed.'
}

export function SetPasswordDialog({ userId, username, onCancel, onDone }: SetPasswordDialogProps) {
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  async function handleSubmit() {
    if (!password) {
      setError('Password is required.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      const res = await apiFetch(`/api/v1/users/${userId}/set_password/`, {
        method: 'POST',
        body: JSON.stringify({ password }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => null)
        throw new Error(formatErrors(data))
      }
      setDone(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Reset failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-full max-w-lg flex flex-col">
        <div className="px-5 py-4 border-b border-gray-700">
          <h3 className="text-base font-semibold">Reset password</h3>
          <p className="mt-1 text-sm text-gray-400">
            Set a new password for <span className="text-white font-medium">{username}</span>.
            Copy it now — it is not stored anywhere else.
          </p>
        </div>

        <div className="px-5 py-4 space-y-4 text-sm">
          {done ? (
            <div className="px-3 py-2 bg-emerald-900/40 border border-emerald-700 rounded text-emerald-300">
              Password updated for {username}.
            </div>
          ) : (
            <>
              <div>
                <label className="block text-gray-400 mb-1" htmlFor="sp-password">New password</label>
                <PasswordField id="sp-password" value={password} onChange={setPassword} disabled={busy} />
              </div>
              {error && (
                <div className="px-3 py-2 bg-red-900/40 border border-red-700 rounded text-red-300 whitespace-pre-line">
                  {error}
                </div>
              )}
            </>
          )}
        </div>

        <div className="px-5 py-4 border-t border-gray-700 flex justify-end gap-2">
          {done ? (
            <button
              onClick={onDone}
              className="px-3 py-1.5 text-sm bg-indigo-600 hover:bg-indigo-500 rounded transition-colors"
            >
              Done
            </button>
          ) : (
            <>
              <button
                onClick={onCancel}
                disabled={busy}
                className="px-3 py-1.5 text-sm bg-gray-700 hover:bg-gray-600 rounded transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={busy}
                className="px-3 py-1.5 text-sm bg-indigo-600 hover:bg-indigo-500 rounded transition-colors disabled:opacity-50"
              >
                {busy ? 'Saving…' : 'Set password'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
