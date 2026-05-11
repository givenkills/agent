import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">AI 游戏生成助手</Link>
      </div>
      <div className="navbar-links">
        <Link to="/memories">已存档游戏</Link>
        <Link>  </Link>
        <Link to="/settings">设置</Link>
      </div>
      <div className="navbar-user">
        <span className="navbar-username">{user?.username}</span>
        <button className="navbar-logout" onClick={handleLogout}>退出</button>
      </div>
    </nav>
  )
}
