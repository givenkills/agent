import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const [isRegister, setIsRegister] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { loginUser, registerUser } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      if (isRegister) {
        await registerUser(username, password)
      } else {
        await loginUser(username, password)
      }
      navigate('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-title">AI 游戏生成助手</h1>
        <p className="auth-subtitle">{isRegister ? '创建新账号' : '登录账号'}</p>
        <form onSubmit={handleSubmit} className="auth-form">
          <input
            className="auth-input"
            type="text"
            placeholder="用户名"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            minLength={2}
            maxLength={32}
            required
          />
          <input
            className="auth-input"
            type="password"
            placeholder="密码"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={4}
            required
          />
          {error && <div className="auth-error">{error}</div>}
          <button className="auth-submit" type="submit" disabled={submitting}>
            {submitting ? '处理中...' : isRegister ? '注册' : '登录'}
          </button>
        </form>
        <p className="auth-toggle">
          {isRegister ? '已有账号？' : '没有账号？'}
          <button
            className="link-btn"
            type="button"
            onClick={() => { setIsRegister(!isRegister); setError('') }}
          >
            {isRegister ? '去登录' : '去注册'}
          </button>
        </p>
      </div>
    </div>
  )
}
