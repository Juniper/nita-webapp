import { useState } from 'react'
import { apiFetch } from '../api/client'
import { PasswordField } from './PasswordField'

export interface CreatedUser {
  id: number
  username: string
  email: string
  role: 'user' | 'power_user' | 'admin'
  is_active: boolean
}

interface CreateUserDialogProps {
  onCancel: () => void
  onCreated: (user: CreatedUser) => void
}

const ROLE_OPTIONS: CreatedUser['role'][] = ['user', 'power_user', 'admin']
const ROLE_LABELS: Record<CreatedUser['role'], string> = {
  user: 'User',
  power_user: 'Power user',
  admin: 'Admin',
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
  return 'Create failed.'
}

export function CreateUserDialog({ onCancel, onCreated }: CreateUserDialogProps) {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<CreatedUser['role']>('user')
  const [password, setPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleCreate() {
    if (!username.trim()) {
      setError('Username is required.')
      return
    }
    if (!password) {
      setError('Password is required.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      const res = await apiFetch('/api/v1/users/', {
        method: 'POST',
        body: JSON.stringify({
          username: username.trim(),
          email: email.trim(),
          role,
          password,
        }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => null)
        throw new Error(formatErrors(data))
      }
      const created: CreatedUser = await res.json()
      onCreated(created)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Create failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-full max-w-lg flex flex-col">
        <div className="px-5 py-4 border-b border-gray-700">
          <h3 className="text-base font-semibold">Create user</h3>
          <p className="mt-1 text-sm text-gray-400">
            Choose a role and set an initial password. The password is not stored
            anywhere else — copy it now if you need to share it.
          </p>
        </div>

        <div className="px-5 py-4 space-y-4 text-sm">
          <div>
            <label className="block text-gray-400 mb-1" htmlFor="cu-username">Username</label>
            <input
              id="cu-username"
              value={username}
              onChange={e => setUsername(e.target.value)}
              disabled={busy}
              autoComplete="off"
              className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-gray-200 disabled:opacity-40 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-gray-400 mb-1" htmlFor="cu-email">Email (optional)</label>
            <input
              id="cu-email"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              disabled={busy}
              autoComplete="off"
              className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-gray-200 disabled:opacity-40 focus:outline-none focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-gray-400 mb-1" htmlFor="cu-role">Role</label>
            <select
              id="cu-role"
              value={role}
              onChange={e => setRole(e.target.value as CreatedUser['role'])}
              disabled={busy}
              className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-gray-200 disabled:opacity-40"
            >
              {ROLE_OPTIONS.map(r => (
                <option key={r} value={r}>{ROLE_LABELS[r]}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-gray-400 mb-1" htmlFor="cu-password">Password</label>
            <PasswordField id="cu-password" value={password} onChange={setPassword} disabled={busy} />
          </div>

          {error && (
            <div className="px-3 py-2 bg-red-900/40 border border-red-700 rounded text-red-300 whitespace-pre-line">
              {error}
            </div>
          )}
        </div>

        <div className="px-5 py-4 border-t border-gray-700 flex justify-end gap-2">
          <button
            onClick={onCancel}
            disabled={busy}
            className="px-3 py-1.5 text-sm bg-gray-700 hover:bg-gray-600 rounded transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={busy}
            className="px-3 py-1.5 text-sm bg-indigo-600 hover:bg-indigo-500 rounded transition-colors disabled:opacity-50"
          >
            {busy ? 'Creating…' : 'Create user'}
          </button>
        </div>
      </div>
    </div>
  )
}
