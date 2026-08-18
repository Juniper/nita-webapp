import { useMemo, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { AppLayout } from '../components/AppLayout'
import { apiFetch } from '../api/client'
import { useApiResource } from '../hooks/useApiResource'
import { useAuth, useIsAdmin } from '../context/useAuth'
import { TransferUserDialog } from '../components/TransferUserDialog'
import { CreateUserDialog } from '../components/CreateUserDialog'
import { SetPasswordDialog } from '../components/SetPasswordDialog'

interface ManagedUser {
  id: number
  username: string
  email: string
  role: 'user' | 'power_user' | 'admin'
  is_active: boolean
}

interface PaginatedResponse {
  results: ManagedUser[]
}

const ROLE_OPTIONS: ManagedUser['role'][] = ['user', 'power_user', 'admin']
const ROLE_LABELS: Record<ManagedUser['role'], string> = {
  user: 'User',
  power_user: 'Power user',
  admin: 'Admin',
}
const ROLE_BADGE: Record<ManagedUser['role'], string> = {
  user: 'bg-gray-700 text-gray-200',
  power_user: 'bg-sky-700 text-sky-100',
  admin: 'bg-indigo-600 text-white',
}

export function UsersPage() {
  const { user: currentUser } = useAuth()
  const isAdmin = useIsAdmin()
  const {
    data,
    loading,
    error,
    reload: reloadUsers,
    setData: setUsersData,
    setError,
  } = useApiResource<PaginatedResponse>('/api/v1/users/', { enabled: isAdmin })
  const users = useMemo(() => data?.results ?? [], [data])
  function setUsers(updater: (prev: ManagedUser[]) => ManagedUser[]) {
    setUsersData(prev => (prev ? { ...prev, results: updater(prev.results) } : prev))
  }
  const [busyId, setBusyId] = useState<number | null>(null)
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [transfer, setTransfer] = useState<
    { id: number; username: string; networks: string[]; types: string[] } | null
  >(null)
  const [showCreate, setShowCreate] = useState(false)
  const [resetTarget, setResetTarget] = useState<{ id: number; username: string } | null>(null)

  async function patchUser(id: number, body: Partial<Pick<ManagedUser, 'role' | 'is_active'>>) {
    setBusyId(id)
    setError(null)
    try {
      const res = await apiFetch(`/api/v1/users/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error(`Update failed: ${res.status}`)
      const updated: ManagedUser = await res.json()
      setUsers(prev => prev.map(u => (u.id === id ? { ...u, ...updated } : u)))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Update failed')
    } finally {
      setBusyId(null)
    }
  }

  async function handleDelete(id: number) {
    if (confirmDeleteId !== id) {
      setConfirmDeleteId(id)
      return
    }
    setConfirmDeleteId(null)
    await doDelete(id)
  }

  // Returns true when the account was deleted; on 409 opens the transfer dialog.
  async function doDelete(id: number): Promise<boolean> {
    setBusyId(id)
    setError(null)
    try {
      const res = await apiFetch(`/api/v1/users/${id}/`, { method: 'DELETE' })
      if (res.status === 204) {
        setUsers(prev => prev.filter(u => u.id !== id))
        return true
      }
      const data = await res.json().catch(() => null)
      if (res.status === 409 && data) {
        const target = users.find(u => u.id === id)
        setTransfer({
          id,
          username: target?.username ?? String(id),
          networks: data.networks ?? [],
          types: data.types ?? [],
        })
        return false
      }
      throw new Error(data?.detail ?? `Delete failed: ${res.status}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Delete failed')
      return false
    } finally {
      setBusyId(null)
    }
  }

  const filteredUsers = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return users
    return users.filter(
      u =>
        u.username.toLowerCase().includes(q) ||
        u.email.toLowerCase().includes(q) ||
        u.role.toLowerCase().includes(q),
    )
  }, [users, search])

  if (!isAdmin) return <Navigate to="/" replace />

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">User Management</h2>
        <div className="flex items-center gap-2">
          <input
            type="search"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search users…"
            className="px-3 py-2 text-sm bg-gray-800 border border-gray-700 rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-indigo-500"
          />
          <button
            onClick={reloadUsers}
            className="px-4 py-2 text-sm bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
          >
            Refresh
          </button>
          <button
            onClick={() => setShowCreate(true)}
            className="px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-500 rounded-lg transition-colors"
          >
            New user
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 px-4 py-3 bg-red-900/40 border border-red-700 rounded-lg text-sm text-red-300">
          {error}
        </div>
      )}

      {loading ? (
        <p className="text-gray-400 text-sm">Loading…</p>
      ) : users.length === 0 ? (
        <p className="text-gray-400 text-sm">No users found.</p>
      ) : filteredUsers.length === 0 ? (
        <p className="text-gray-400 text-sm">No users match “{search}”.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-400 border-b border-gray-700">
                <th className="pb-2 pr-4 font-medium">Username</th>
                <th className="pb-2 pr-4 font-medium">Email</th>
                <th className="pb-2 pr-4 font-medium">Role</th>
                <th className="pb-2 pr-4 font-medium">Status</th>
                <th className="pb-2 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map(u => {
                const isSelf = u.id === currentUser?.id
                return (
                  <tr key={u.id} className="group border-b border-gray-800 hover:bg-gray-800/40">
                    <td className="py-2.5 pr-4 font-medium">
                      {u.username}
                      {isSelf && <span className="ml-2 text-xs text-gray-500">(you)</span>}
                    </td>
                    <td className="py-2.5 pr-4 text-gray-400">{u.email || '—'}</td>
                    <td className="py-2.5 pr-4">
                      <div className="flex items-center gap-2">
                        <span className={`px-1.5 py-0.5 text-xs rounded ${ROLE_BADGE[u.role]}`}>
                          {ROLE_LABELS[u.role]}
                        </span>
                        <select
                          value={u.role}
                          disabled={busyId === u.id || isSelf}
                          onChange={e => patchUser(u.id, { role: e.target.value as ManagedUser['role'] })}
                          className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-200 disabled:opacity-40"
                        >
                          {ROLE_OPTIONS.map(r => (
                            <option key={r} value={r}>{ROLE_LABELS[r]}</option>
                          ))}
                        </select>
                      </div>
                    </td>
                    <td className="py-2.5 pr-4">
                      <span className={u.is_active ? 'text-emerald-400' : 'text-gray-500'}>
                        {u.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="py-2.5 text-right whitespace-nowrap">
                      <span className="inline-flex items-center gap-2">
                        <button
                          onClick={() => setResetTarget({ id: u.id, username: u.username })}
                          disabled={busyId === u.id}
                          className="px-2.5 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors disabled:opacity-50"
                        >
                          Reset password
                        </button>
                        {!isSelf && (
                          <button
                            onClick={() => patchUser(u.id, { is_active: !u.is_active })}
                            disabled={busyId === u.id}
                            className="px-2.5 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors disabled:opacity-50"
                          >
                            {u.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                        )}
                        {!isSelf && confirmDeleteId === u.id ? (
                          <>
                            <button
                              onClick={() => handleDelete(u.id)}
                              disabled={busyId === u.id}
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
                          </>
                        ) : (
                          !isSelf && (
                            <button
                              onClick={() => handleDelete(u.id)}
                              disabled={busyId === u.id}
                              className="px-2.5 py-1 text-xs bg-gray-700 hover:bg-red-700 rounded transition-colors disabled:opacity-50"
                            >
                              Delete
                            </button>
                          )
                        )}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {transfer && (
        <TransferUserDialog
          userId={transfer.id}
          username={transfer.username}
          networks={transfer.networks}
          types={transfer.types}
          recipients={users}
          onCancel={() => setTransfer(null)}
          onTransferred={async () => {
            const id = transfer.id
            setTransfer(null)
            await doDelete(id)
          }}
        />
      )}

      {showCreate && (
        <CreateUserDialog
          onCancel={() => setShowCreate(false)}
          onCreated={created => {
            setUsers(prev => [...prev, created])
            setShowCreate(false)
          }}
        />
      )}

      {resetTarget && (
        <SetPasswordDialog
          userId={resetTarget.id}
          username={resetTarget.username}
          onCancel={() => setResetTarget(null)}
          onDone={() => setResetTarget(null)}
        />
      )}
    </AppLayout>
  )
}
