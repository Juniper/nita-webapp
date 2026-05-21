import { useEffect, useRef, useState } from 'react'
import { AppLayout } from '../components/AppLayout'
import { apiFetch } from '../api/client'

interface Role {
  id: number
  name: string
}

interface Resource {
  id: number
  name: string
}

interface NetworkType {
  id: number
  name: string
  description: string
  app_zip_name: string
  roles: Role[]
  resources: Resource[]
}

interface PaginatedResponse {
  results: NetworkType[]
}

export function NetworkTypesPage() {
  const [networkTypes, setNetworkTypes] = useState<NetworkType[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  async function fetchNetworkTypes() {
    setLoading(true)
    setError(null)
    try {
      const res = await apiFetch('/api/v1/network-types/')
      if (!res.ok) throw new Error(`Failed to load: ${res.status}`)
      const data: PaginatedResponse = await res.json()
      setNetworkTypes(data.results)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchNetworkTypes() }, [])

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setUploadError(null)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await apiFetch('/api/v1/network-types/upload/', {
        method: 'POST',
        body: form,
      })
      if (!res.ok) {
        const text = await res.text()
        throw new Error(`Upload failed (${res.status}): ${text}`)
      }
      await fetchNetworkTypes()
    } catch (e) {
      setUploadError(e instanceof Error ? e.message : 'Upload failed')
    } finally {
      setUploading(false)
      // reset so the same file can be re-selected
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  async function handleDelete(id: number) {
    if (confirmDeleteId !== id) {
      setConfirmDeleteId(id)
      return
    }
    setDeletingId(id)
    setConfirmDeleteId(null)
    try {
      const res = await apiFetch(`/api/v1/network-types/${id}/`, { method: 'DELETE' })
      if (!res.ok && res.status !== 204) throw new Error(`Delete failed: ${res.status}`)
      setNetworkTypes(prev => prev.filter(nt => nt.id !== id))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Delete failed')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">Network Types</h2>
        <div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".zip"
            className="hidden"
            onChange={handleUpload}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors"
          >
            {uploading ? 'Uploading…' : 'Upload zip'}
          </button>
        </div>
      </div>

      {uploadError && (
        <div className="mb-4 px-4 py-3 bg-red-900/40 border border-red-700 rounded-lg text-sm text-red-300">
          {uploadError}
        </div>
      )}

      {loading ? (
        <p className="text-gray-400 text-sm">Loading…</p>
      ) : error ? (
        <div className="px-4 py-3 bg-red-900/40 border border-red-700 rounded-lg text-sm text-red-300">
          {error}
        </div>
      ) : networkTypes.length === 0 ? (
        <p className="text-gray-400 text-sm">No network types found. Upload a zip to add one.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-400 border-b border-gray-700">
                <th className="pb-2 pr-4 font-medium">Name</th>
                <th className="pb-2 pr-4 font-medium">Description</th>
                <th className="pb-2 pr-4 font-medium">Zip File</th>
                <th className="pb-2 pr-4 font-medium text-center">Roles</th>
                <th className="pb-2 pr-4 font-medium text-center">Resources</th>
                <th className="pb-2 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {networkTypes.map(nt => (
                <tr key={nt.id} className="border-b border-gray-800 hover:bg-gray-800/40">
                  <td className="py-2.5 pr-4 font-medium">{nt.name}</td>
                  <td className="py-2.5 pr-4 text-gray-400">{nt.description || '—'}</td>
                  <td className="py-2.5 pr-4 text-gray-400 font-mono text-xs">{nt.app_zip_name}</td>
                  <td className="py-2.5 pr-4 text-center text-gray-400">{nt.roles.length}</td>
                  <td className="py-2.5 pr-4 text-center text-gray-400">{nt.resources.length}</td>
                  <td className="py-2.5 text-right whitespace-nowrap">
                    {confirmDeleteId === nt.id ? (
                      <span className="inline-flex gap-2">
                        <button
                          onClick={() => handleDelete(nt.id)}
                          disabled={deletingId === nt.id}
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
                        onClick={() => handleDelete(nt.id)}
                        disabled={deletingId === nt.id}
                        className="px-2.5 py-1 text-xs bg-gray-700 hover:bg-red-700 rounded transition-colors disabled:opacity-50"
                      >
                        Delete
                      </button>
                    )}
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
