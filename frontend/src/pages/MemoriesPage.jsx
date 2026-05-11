import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import * as api from '../api/client'

export default function MemoriesPage() {
  const [games, setGames] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const loadGames = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await api.getMemories()
      setGames(data.games || [])
    } catch (err) {
      if (err.message === '未登录') {
        navigate('/login')
      } else {
        setError(err.message)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadGames()
  }, [])

  const formatDate = (dateStr) => {
    if (!dateStr) return ''
    const d = new Date(dateStr)
    return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
  }

  return (
    <div className="memories-page">
      <Navbar />
      <div className="memories-container">
        <div className="memories-header">
          <h1>已存档的游戏</h1>
          <div className="memories-header-actions">
            <button className="refresh-btn" onClick={loadGames} disabled={loading}>
              {loading ? '加载中...' : '刷新'}
            </button>
            <Link to="/" className="back-btn">返回对话</Link>
          </div>
        </div>

        {error && <div className="memories-error">{error}</div>}

        {loading ? (
          <div className="memories-loading">加载中...</div>
        ) : games.length === 0 ? (
          <div className="memories-empty">
            <p>暂无已存档的游戏</p>
            <p className="hint">生成新游戏后，旧游戏会自动存档到这里</p>
            <Link to="/" className="back-btn">去生成游戏</Link>
          </div>
        ) : (
          <div className="game-list">
            {games.map((game, i) => (
              <div key={game.id} className="game-item">
                <div className="game-item-info">
                  <div className="game-item-name">{game.game_name}</div>
                  <div className="game-item-type">{game.game_type || '未分类'}</div>
                  {game.created_at && (
                    <div className="game-item-date">{formatDate(game.created_at)}</div>
                  )}
                </div>
                <span className="game-item-index">#{i + 1}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
