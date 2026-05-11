import { useState } from 'react'
import Navbar from '../components/Navbar'

export default function SettingsPage() {
  const [clearing, setClearing] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')

  const handleClear = async () => {
    if (!window.confirm('确定要清空所有已存档的游戏记忆吗？此操作不可撤销。')) {
      return
    }
    setClearing(true)
    setError('')
    setDone(false)
    try {
      const token = localStorage.getItem('token')
      const res = await fetch('/api/memories/clear', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: '清空失败' }))
        throw new Error(err.detail || '清空失败')
      }
      setDone(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setClearing(false)
    }
  }

  return (
    <div className="chat-page">
      <Navbar />
      <div className="settings-page">
        <div className="settings-card">
          <h2 className="settings-title">设置</h2>

          <div className="settings-section">
            <h3 className="settings-section-title">记忆管理</h3>
            <p className="settings-desc">
              清空当前账号下所有已存档的游戏记忆。此操作会同时删除 SQLite 数据库和 ChromaDB 向量索引中的记录。
            </p>
            <button
              className="settings-danger-btn"
              onClick={handleClear}
              disabled={clearing}
            >
              {clearing ? '清空中...' : '清空所有已存档游戏'}
            </button>
            {done && <p className="settings-success">已成功清空所有游戏记忆</p>}
            {error && <p className="settings-error">{error}</p>}
          </div>
        </div>
      </div>
    </div>
  )
}
