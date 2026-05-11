import { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import * as api from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const username = localStorage.getItem('username')
    if (token && username) {
      setUser({ username, token })
    }
    setLoading(false)
  }, [])

  const loginUser = async (username, password) => {
    const data = await api.login(username, password)
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('username', data.username)
    setUser({ username: data.username, token: data.access_token })
  }

  const registerUser = async (username, password) => {
    const data = await api.register(username, password)
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('username', data.username)
    setUser({ username: data.username, token: data.access_token })
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, loginUser, registerUser, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
