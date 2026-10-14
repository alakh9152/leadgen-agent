import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import axios from 'axios'

interface User { id: number; email: string; name: string }

interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  logout: () => void
  loading: boolean
}

const Context = createContext<AuthContextType | null>(null)
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      axios.get(`${API}/api/auth/me`).then(r => setUser(r.data)).catch(() => logout())
    }
    setLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    const r = await axios.post(`${API}/api/auth/login`, { email, password })
    setToken(r.data.token)
    localStorage.setItem('token', r.data.token)
    axios.defaults.headers.common['Authorization'] = `Bearer ${r.data.token}`
    setUser({ id: r.data.user_id, email: r.data.email, name: r.data.name })
  }

  const register = async (name: string, email: string, password: string) => {
    const r = await axios.post(`${API}/api/auth/register`, { name, email, password })
    setToken(r.data.token)
    localStorage.setItem('token', r.data.token)
    axios.defaults.headers.common['Authorization'] = `Bearer ${r.data.token}`
    setUser({ id: r.data.user_id, email: r.data.email, name: r.data.name })
  }

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('token')
    delete axios.defaults.headers.common['Authorization']
  }

  return <Context.Provider value={{ user, token, login, register, logout, loading }}>{children}</Context.Provider>
}

export const useAuth = () => {
  const ctx = useContext(Context)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}
