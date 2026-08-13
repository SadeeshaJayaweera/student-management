import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

const initials = (name: string) =>
  name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)

interface NavbarProps {
  onMenuClick: () => void
}

export default function Navbar({ onMenuClick }: NavbarProps) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  return (
    <nav className="navbar">
      <button className="btn btn-icon btn-ghost" onClick={onMenuClick} title="Toggle Sidebar">
        ☰
      </button>

      <a href="#" className="nav-brand" onClick={(e) => { e.preventDefault(); navigate('/dashboard') }}>
        <div className="nav-logo">🎓</div>
        <div>
          <div className="nav-title">EduSphere</div>
          <div className="nav-subtitle">NSBM Green University</div>
        </div>
      </a>

      <div className="nav-spacer" />

      {/* AI Quick Access */}
      <button className="btn btn-secondary btn-sm" onClick={() => navigate('/ai-chat')}>
        🤖 AI Assistant
      </button>

      {/* User Info */}
      {user && (
        <div
          className="flex items-center gap-12"
          style={{ cursor: 'pointer' }}
          onClick={() => navigate('/profile')}
        >
          <div className="avatar avatar-sm">{initials(user.full_name)}</div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '.8rem', fontWeight: 600 }}>
              {user.full_name.split(' ')[0]}
            </span>
            <span style={{ fontSize: '.65rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
              {user.role}
            </span>
          </div>
        </div>
      )}

      <button
        className="btn btn-danger btn-sm"
        onClick={logout}
        style={{ marginLeft: 4 }}
      >
        ⏻ Logout
      </button>
    </nav>
  )
}
