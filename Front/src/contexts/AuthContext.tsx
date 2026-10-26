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
  type LoginPayload,
  type RegisterPayload,
} from '../lib/api'

type AuthContextType = {
  user: AuthUser | null
  loading: boolean
  isAuthenticated: boolean
  login: (payload: LoginPayload, remember?: boolean) => Promise<AuthResponse>
  register: (payload: RegisterPayload, remember?: boolean) => Promise<AuthResponse>
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
    payload: LoginPayload,
    remember = true
  ): Promise<AuthResponse> => {
    const response = await authApi.login(payload, remember)
    setUser(response.user)
    return response
  }

  const register = async (
    payload: RegisterPayload,
    remember = true
  ): Promise<AuthResponse> => {
    const response = await authApi.register(payload, remember)
    setUser(response.user)
    return response
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