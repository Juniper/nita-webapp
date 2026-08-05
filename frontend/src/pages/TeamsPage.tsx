import { useEffect, useMemo, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { AppLayout } from '../components/AppLayout'
import { apiFetch } from '../api/client'
import { useIsPowerUser } from '../context/AuthContext'

interface Team {
  id: number
  name: string
  description: string | null
  created_by: number | null
  members: number[]
}

interface Paginated<T> {
  results: T[]
}

export function TeamsPage() {
  const isPowerUser = useIsPowerUser()
  const [teams, setTeams] = useState<Team[]>([])
  const [directory, setDirectory] = useState<{ id: number; username: string }[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null)

  const [newName, setNewName] = useState('')
  const [newDesc, setNewDesc] = useState('')
  const [creating, setCreating] = useState(false)

  const [memberSelect, setMemberSelect] = useState<Record<number, number | ''>>({})

  async function fetchTeams() {
    setLoading(true)
    setError(null)
    try {
      const res = await apiFetch('/api/v1/teams/')
      if (!res.ok) throw new Error(`Failed to load teams: ${res.status}`)
      const data: Paginated<Team> = await res.json()
      setTeams(data.results)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  // id+username roster used for the member picker and member-name display.
  async function fetchDirectory() {
    try {
      const res = await apiFetch('/api/v1/users/directory/')
      if (!res.ok) return
      const data: { id: number; username: string }[] = await res.json()
      setDirectory(data)
    } catch {
      // ignore — fall back to raw ids
    }
  }

  useEffect(() => {
    if (isPowerUser) {
      fetchTeams()
      fetchDirectory()
    }
  }, [isPowerUser])

  const userNames = useMemo(
    () => Object.fromEntries(directory.map(u => [u.id, u.username])) as Record<number, string>,
    [directory],
  )
  const nameFor = useMemo(
    () => (id: number) => userNames[id] ?? `#${id}`,
    [userNames],
  )

  async function createTeam(e: React.FormEvent) {
    e.preventDefault()
    if (!newName.trim()) return
    setCreating(true)
    setError(null)
    try {
      const res = await apiFetch('/api/v1/teams/', {
        method: 'POST',
        body: JSON.stringify({ name: newName.trim(), description: newDesc.trim() || null }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => null)
        const detail = data?.name?.[0] ?? data?.detail ?? `Create failed: ${res.status}`
        throw new Error(detail)
      }
      setNewName('')
      setNewDesc('')
      await fetchTeams()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Create failed')
    } finally {
      setCreating(false)
    }
  }

  async function deleteTeam(id: number) {
    if (confirmDeleteId !== id) {
      setConfirmDeleteId(id)
      return
    }
    setConfirmDeleteId(null)
    setBusyId(id)
    setError(null)
    try {
      const res = await apiFetch(`/api/v1/teams/${id}/`, { method: 'DELETE' })
      if (!res.ok && res.status !== 204) throw new Error(`Delete failed: ${res.status}`)
      setTeams(prev => prev.filter(t => t.id !== id))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Delete failed')
    } finally {
      setBusyId(null)
    }
  }

  async function addMember(teamId: number) {
    const userId = memberSelect[teamId]
    if (userId === '' || userId === undefined) {
      setError('Select a user to add.')
      return
    }
    setBusyId(teamId)
    setError(null)
    try {
      const res = await apiFetch(`/api/v1/teams/${teamId}/members/`, {
        method: 'POST',
        body: JSON.stringify({ user_id: userId }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => null)
        throw new Error(data?.detail ?? `Add member failed: ${res.status}`)
      }
      const updated: Team = await res.json()
      setTeams(prev => prev.map(t => (t.id === teamId ? updated : t)))
      setMemberSelect(prev => ({ ...prev, [teamId]: '' }))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Add member failed')
    } finally {
      setBusyId(null)
    }
  }

  async function removeMember(teamId: number, userId: number) {
    setBusyId(teamId)
    setError(null)
    try {
      const res = await apiFetch(`/api/v1/teams/${teamId}/members/${userId}/`, { method: 'DELETE' })
      if (!res.ok && res.status !== 204) throw new Error(`Remove failed: ${res.status}`)
      setTeams(prev =>
        prev.map(t => (t.id === teamId ? { ...t, members: t.members.filter(m => m !== userId) } : t)),
      )
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Remove failed')
    } finally {
      setBusyId(null)
    }
  }

  if (!isPowerUser) return <Navigate to="/" replace />

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">Teams</h2>
        <button
          onClick={fetchTeams}
          className="px-4 py-2 text-sm bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-4 px-4 py-3 bg-red-900/40 border border-red-700 rounded-lg text-sm text-red-300">
          {error}
        </div>
      )}

      <form onSubmit={createTeam} className="mb-6 flex flex-wrap items-end gap-2">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Name</label>
          <input
            value={newName}
            onChange={e => setNewName(e.target.value)}
            placeholder="Team name"
            className="px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Description (optional)</label>
          <input
            value={newDesc}
            onChange={e => setNewDesc(e.target.value)}
            placeholder="Description"
            className="px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
          />
        </div>
        <button
          type="submit"
          disabled={creating || !newName.trim()}
          className="px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg transition-colors"
        >
          {creating ? 'Creating…' : 'Create team'}
        </button>
      </form>

      {loading ? (
        <p className="text-gray-400 text-sm">Loading…</p>
      ) : teams.length === 0 ? (
        <p className="text-gray-400 text-sm">No teams yet. Create one above.</p>
      ) : (
        <div className="space-y-3">
          {teams.map(t => (
            <div key={t.id} className="border border-gray-800 rounded-lg p-4 bg-gray-900/40">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="font-medium">{t.name}</div>
                  {t.description && <div className="text-sm text-gray-400">{t.description}</div>}
                </div>
                {confirmDeleteId === t.id ? (
                  <span className="flex items-center gap-2">
                    <button
                      onClick={() => deleteTeam(t.id)}
                      disabled={busyId === t.id}
                      className="px-2.5 py-1 text-xs bg-red-700 hover:bg-red-600 rounded transition-colors disabled:opacity-50"
                    >
                      Confirm?
                    </button>
                    <button
                      onClick={() => setConfirmDeleteId(null)}
                      className="px-2.5 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors"
                    >
                      Cancel
                    </button>
                  </span>
                ) : (
                  <button
                    onClick={() => deleteTeam(t.id)}
                    disabled={busyId === t.id}
                    className="px-2.5 py-1 text-xs bg-gray-700 hover:bg-red-700 rounded transition-colors disabled:opacity-50"
                  >
                    Delete team
                  </button>
                )}
              </div>

              <div className="mt-3">
                <div className="text-xs text-gray-400 mb-1">Members ({t.members.length})</div>
                <div className="flex flex-wrap gap-2">
                  {t.members.map(m => (
                    <span
                      key={m}
                      className="inline-flex items-center gap-1.5 px-2 py-1 text-xs bg-gray-800 border border-gray-700 rounded"
                    >
                      {nameFor(m)}
                      <button
                        onClick={() => removeMember(t.id, m)}
                        disabled={busyId === t.id}
                        title="Remove member"
                        className="text-gray-400 hover:text-red-400 disabled:opacity-50"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                  {t.members.length === 0 && <span className="text-xs text-gray-500">None</span>}
                </div>
                <div className="mt-2 flex items-center gap-2">
                  <select
                    value={memberSelect[t.id] ?? ''}
                    onChange={e =>
                      setMemberSelect(prev => ({
                        ...prev,
                        [t.id]: e.target.value === '' ? '' : Number(e.target.value),
                      }))
                    }
                    className="w-48 px-2 py-1 text-xs bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="">Add member…</option>
                    {directory
                      .filter(u => !t.members.includes(u.id))
                      .map(u => (
                        <option key={u.id} value={u.id}>{u.username}</option>
                      ))}
                  </select>
                  <button
                    onClick={() => addMember(t.id)}
                    disabled={busyId === t.id || (memberSelect[t.id] ?? '') === ''}
                    className="px-2.5 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors disabled:opacity-50"
                  >
                    Add member
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </AppLayout>
  )
}
