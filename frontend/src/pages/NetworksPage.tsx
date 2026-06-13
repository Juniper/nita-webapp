import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AppLayout } from '../components/AppLayout'
import { apiFetch } from '../api/client'

interface NetworkType {
  id: number
  name: string
}

interface Network {
  id: number
  name: string
  description: string
  status: string
  campus_type: number
  campus_type_name: string
  host_file: string
}

interface PaginatedNetworks {
  results: Network[]
}

interface PaginatedNetworkTypes {
  results: NetworkType[]
}

const emptyForm = {
  name: '',
  description: '',
  campus_type: '',
  host_file: '',
}

export function NetworksPage() {
  const [networks, setNetworks] = useState<Network[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [showAddForm, setShowAddForm] = useState(false)
  const [networkTypes, setNetworkTypes] = useState<NetworkType[]>([])
  const [loadingTypes, setLoadingTypes] = useState(false)
  const [form, setForm] = useState(emptyForm)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null)

  async function fetchNetworks() {
    setLoading(true)
    setError(null)
    try {
      const res = await apiFetch('/api/v1/networks/')
      if (!res.ok) throw new Error(`Failed to load: ${res.status}`)
      const data: PaginatedNetworks = await res.json()
      setNetworks(data.results)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchNetworks() }, [])

  async function openAddForm() {
    setShowAddForm(true)
    setForm(emptyForm)
    setFormError(null)
    if (networkTypes.length === 0) {
      setLoadingTypes(true)
      try {
        const res = await apiFetch('/api/v1/network-types/')
        if (!res.ok) throw new Error(`Failed to load types: ${res.status}`)
        const data: PaginatedNetworkTypes = await res.json()
        setNetworkTypes(data.results)
      } catch (e) {
        setFormError(e instanceof Error ? e.message : 'Failed to load network types')
      } finally {
        setLoadingTypes(false)
      }
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.campus_type) { setFormError('Network type is required'); return }
    if (!form.host_file) { setFormError('Host file is required'); return }
    setSubmitting(true)
    setFormError(null)
    try {
      const res = await apiFetch('/api/v1/networks/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: form.name,
          description: form.description,
          campus_type: Number(form.campus_type),
          host_file: form.host_file,
          status: 'Initialized',
        }),
      })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(`Create failed (${res.status}): ${text}`)
      }
      setShowAddForm(false)
      await fetchNetworks()
    } catch (e) {
      setFormError(e instanceof Error ? e.message : 'Create failed')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDelete(id: number) {
    if (confirmDeleteId !== id) { setConfirmDeleteId(id); return }
    setDeletingId(id)
    setConfirmDeleteId(null)
    try {
      const res = await apiFetch(`/api/v1/networks/${id}/`, { method: 'DELETE' })
      if (!res.ok && res.status !== 204) throw new Error(`Delete failed: ${res.status}`)
      setNetworks(prev => prev.filter(n => n.id !== id))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Delete failed')
    } finally {
      setDeletingId(null)
    }
  }

  const inputCls = 'w-full px-3 py-1.5 text-sm bg-gray-800 border border-gray-600 rounded-lg focus:outline-none focus:border-indigo-500'
  const labelCls = 'block text-xs text-gray-400 mb-1'

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">Networks</h2>
        <button
          onClick={showAddForm ? () => setShowAddForm(false) : openAddForm}
          className="px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-500 rounded-lg transition-colors"
        >
          {showAddForm ? 'Cancel' : 'Add Network'}
        </button>
      </div>

      {/* Inline add form */}
      {showAddForm && (
        <form
          onSubmit={handleSubmit}
          className="mb-6 p-4 bg-gray-800/60 border border-gray-700 rounded-xl"
        >
          <h3 className="text-sm font-medium mb-4">New Network</h3>
          {formError && (
            <div className="mb-3 px-3 py-2 bg-red-900/40 border border-red-700 rounded text-sm text-red-300">
              {formError}
            </div>
          )}
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <label className={labelCls}>Name *</label>
              <input
                className={inputCls}
                required
                value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              />
            </div>
            <div>
              <label className={labelCls}>Description *</label>
              <input
                className={inputCls}
                required
                value={form.description}
                onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              />
            </div>
            <div>
              <label className={labelCls}>Network Type *</label>
              <select
                className={inputCls}
                required
                value={form.campus_type}
                onChange={e => setForm(f => ({ ...f, campus_type: e.target.value }))}
              >
                <option value="">{loadingTypes ? 'Loading…' : '— select —'}</option>
                {networkTypes.map(nt => (
                  <option key={nt.id} value={nt.id}>{nt.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelCls}>Host File *</label>
              <input
                type="file"
                className={inputCls}
                required
                onChange={async e => {
                  const file = e.target.files?.[0]
                  if (!file) { setForm(f => ({ ...f, host_file: '' })); return }
                  const text = await file.text()
                  setForm(f => ({ ...f, host_file: text }))
                }}
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg transition-colors"
          >
            {submitting ? 'Creating…' : 'Create'}
          </button>
        </form>
      )}

      {loading ? (
        <p className="text-gray-400 text-sm">Loading…</p>
      ) : error ? (
        <div className="px-4 py-3 bg-red-900/40 border border-red-700 rounded-lg text-sm text-red-300">
          {error}
        </div>
      ) : networks.length === 0 ? (
        <p className="text-gray-400 text-sm">No networks found. Add one to get started.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-400 border-b border-gray-700">
                <th className="pb-2 pr-4 font-medium">Name</th>
                <th className="pb-2 pr-4 font-medium">Network Type</th>
                <th className="pb-2 pr-4 font-medium">Description</th>
                <th className="pb-2 pr-4 font-medium">Status</th>
                <th className="pb-2 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {networks.map(n => (
                <tr key={n.id} className="border-b border-gray-800 hover:bg-gray-800/40">
                  <td className="py-2.5 pr-4 font-medium">{n.name}</td>
                  <td className="py-2.5 pr-4 text-gray-400">{n.campus_type_name}</td>
                  <td className="py-2.5 pr-4 text-gray-400">{n.description || '—'}</td>
                  <td className="py-2.5 pr-4 text-gray-400">{n.status || '—'}</td>
                  <td className="py-2.5 text-right whitespace-nowrap">
                    <span className="inline-flex gap-2 items-center">
                      <Link
                        to={`/networks/${n.id}`}
                        className="px-2.5 py-1 text-xs bg-gray-700 hover:bg-gray-600 rounded transition-colors"
                      >
                        Modify
                      </Link>
                      {confirmDeleteId === n.id ? (
                        <>
                          <button
                            onClick={() => handleDelete(n.id)}
                            disabled={deletingId === n.id}
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
                        <button
                          onClick={() => handleDelete(n.id)}
                          disabled={deletingId === n.id}
                          className="px-2.5 py-1 text-xs bg-gray-700 hover:bg-red-700 rounded transition-colors disabled:opacity-50"
                        >
                          Delete
                        </button>
                      )}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppLayout>
  )
}
