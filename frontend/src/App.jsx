import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import { ChatProvider } from './context/ChatContext'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import ChatPage from './pages/ChatPage'
import MemoriesPage from './pages/MemoriesPage'
import SettingsPage from './pages/SettingsPage'

export default function App() {
  const { loading } = useAuth()

  if (loading) {
    return <div className="loading-screen">加载中...</div>
  }

  return (
    <ChatProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <ChatPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/memories"
          element={
            <ProtectedRoute>
              <MemoriesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <SettingsPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </ChatProvider>
  )
}
