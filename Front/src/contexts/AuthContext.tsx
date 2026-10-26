import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import {
  authApi,
  type AuthUser,
  type AuthResponse,
} from '../lib/api'

type AuthContextType = {
  user: AuthUser | null
  loading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string, remember?: boolean) => Promise<AuthResponse | null>
  register: (payload: any, remember?: boolean) => Promise<AuthResponse | null>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    if (authApi.hasSession()) {
      authApi
        .me()
        .then((current) => {
          if (active) setUser(current)
        })
        .catch(() => {
          if (active) setUser(null)
        })
        .finally(() => {
          if (active) setLoading(false)
        })
    } else {
      setLoading(false)
    }
    return () => {
      active = false
    }
  }, [])

  const login = async (
    email: string,
    password: string,
    remember = true
  ): Promise<AuthResponse | null> => {
    try {
      const response = await authApi.login({ email, password }, remember)
      setUser(response.user)
      return response
    } catch {
      return null
    }
  }

  const register = async (
    payload: any,
    remember = true
  ): Promise<AuthResponse | null> => {
    try {
      const response = await authApi.register(payload, remember)
      setUser(response.user)
      return response
    } catch {
      return null
    }
  }

  const logout = () => {
    authApi.logout()
    setUser(null)
  }

  const refreshUser = async () => {
    try {
      const current = await authApi.me()
      setUser(current)
    } catch {
      setUser(null)
    }
  }

  const value = {
    user,
    loading,
    isAuthenticated: Boolean(user),
    login,
    register,
    logout,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth deve ser usado dentro de AuthProvider')
  }
  return ctx
}