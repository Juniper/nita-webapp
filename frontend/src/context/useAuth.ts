import { useContext } from 'react'
import { AuthContext } from './auth-context'
import type { AuthContextValue } from './auth-context'

export function useAuth(): AuthContextValue {
  return useContext(AuthContext)
}

export function useIsAdmin(): boolean {
  const { user } = useAuth()
  return Boolean(user?.is_superuser || user?.role === 'admin')
}

export function useIsPowerUser(): boolean {
  const { user } = useAuth()
  return Boolean(
    user?.is_superuser || user?.role === 'admin' || user?.role === 'power_user',
  )
}
