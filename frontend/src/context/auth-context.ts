import { createContext } from 'react'

export interface User {
  id: number
  username: string
  is_superuser: boolean
  role?: string
  teams?: number[]
}

export interface AuthContextValue {
  user: User | null
  loading: boolean
  setUser: (u: User | null) => void
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue>({
  user: null,
  loading: true,
  setUser: () => {},
  logout: async () => {},
})
