import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { apiFetch, clearCsrfCache } from '../api/client'
import { AuthContext } from './auth-context'
import type { User } from './auth-context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiFetch('/api/v1/auth/me/')
      .then((res) => {
        if (res.ok) return res.json() as Promise<User>
        return null
      })
      .then((data) => setUser(data))
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  async function logout() {
    try {
      await apiFetch('/api/v1/auth/logout/', { method: 'POST' })
    } finally {
      clearCsrfCache()
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, setUser, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
