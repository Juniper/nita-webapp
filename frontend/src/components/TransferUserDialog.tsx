import { useMemo, useState } from 'react'
import { apiFetch } from '../api/client'

interface Recipient {
  id: number
  username: string
}

interface TransferUserDialogProps {
  /** The user whose resources must be transferred before deletion. */
  userId: number
  username: string
  /** Names of the blocking resources returned by the 409 response. */
  networks: string[]
  types: string[]
  /** Candidate recipients (all other users). */
  recipients: Recipient[]
  onCancel: () => void
  /** Called after a successful transfer so the caller can retry the delete. */
  onTransferred: () => void
}

export function TransferUserDialog({
  userId,
  username,
  networks,
  types,
  recipients,
  onCancel,
  onTransferred,
}: TransferUserDialogProps) {
  const candidates = useMemo(
    () => recipients.filter(r => r.id !== userId),
    [recipients, userId],
  )
  const [recipientId, setRecipientId] = useState<number | ''>(candidates[0]?.id ?? '')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleTransfer() {
    if (recipientId === '') {
      setError('Select a recipient user.')
      return
    }
    setBusy(true)
    setError(null)
    const body: { networks_to?: number; types_to?: number } = {}
    if (networks.length) body.networks_to = recipientId
    if (types.length) body.types_to = recipientId
    try {
      const res = await apiFetch(`/api/v1/users/${userId}/transfer/`, {
        method: 'POST',
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => null)
        throw new Error(data?.detail ?? `Transfer failed: ${res.status}`)
      }
      onTransferred()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Transfer failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-full max-w-lg flex flex-col">
        <div className="px-5 py-4 border-b border-gray-700">
          <h3 className="text-base font-semibold">Transfer ownership before deleting</h3>
          <p className="mt-1 text-sm text-gray-400">
            <span className="text-white font-medium">{username}</span> still owns resources.
            Reassign them to another user, then the account can be deleted.
          </p>
        </div>

        <div className="px-5 py-4 space-y-4 text-sm">
          {networks.length > 0 && (
            <div>
              <div className="text-gray-400 mb-1">Networks ({networks.length})</div>
              <div className="text-gray-300 font-mono text-xs break-words">{networks.join(', ')}</div>
            </div>
          )}
          {types.length > 0 && (
            <div>
              <div className="text-gray-400 mb-1">Network types ({types.length})</div>
              <div className="text-gray-300 font-mono text-xs break-words">{types.join(', ')}</div>
            </div>
          )}

          <div>
            <label className="block text-gray-400 mb-1">Transfer to</label>
            <select
              value={recipientId}
              onChange={e => setRecipientId(e.target.value === '' ? '' : Number(e.target.value))}
              disabled={busy || candidates.length === 0}
              className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-gray-200 disabled:opacity-40"
            >
              {candidates.length === 0 && <option value="">No other users available</option>}
              {candidates.map(r => (
                <option key={r.id} value={r.id}>{r.username}</option>
              ))}
            </select>
          </div>

          {error && (
            <div className="px-3 py-2 bg-red-900/40 border border-red-700 rounded text-red-300">
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
            onClick={handleTransfer}
            disabled={busy || recipientId === ''}
            className="px-3 py-1.5 text-sm bg-indigo-600 hover:bg-indigo-500 rounded transition-colors disabled:opacity-50"
          >
            {busy ? 'Transferring…' : 'Transfer & delete'}
          </button>
        </div>
      </div>
    </div>
  )
}
