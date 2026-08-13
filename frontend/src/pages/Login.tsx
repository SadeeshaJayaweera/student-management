import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import toast from 'react-hot-toast'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!username || !password) { toast.error('Please fill in all fields'); return }
    setLoading(true)
    try {
      await login(username, password)
      toast.success('Welcome back! 🎓')
      navigate('/dashboard')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Invalid credentials')
    } finally {
      setLoading(false)
    }
  }

  const fillDemo = (role: string) => {
    const accounts: Record<string, [string, string]> = {
      admin:    ['admin',    'Admin@123'],
      student:  ['student01','Student@123'],
      lecturer: ['kperera',  'Lecturer@123'],
      alumni:   ['alumni01', 'Alumni@123'],
    }
    const [u, p] = accounts[role]
    setUsername(u); setPassword(p)
  }

  return (
    <>
      <div className="bg-orbs">
        <div className="bg-orb bg-orb-1" />
        <div className="bg-orb bg-orb-2" />
        <div className="bg-orb bg-orb-3" />
      </div>

      <div className="login-page">
        {/* Left — branding */}
        <div className="login-left">
          {/* Floating shapes */}
          {[
            { w: 200, h: 200, t: '10%',  l: '10%', delay: '0s'  },
            { w: 150, h: 150, t: '60%',  l: '70%', delay: '3s'  },
            { w: 100, h: 100, t: '80%',  l: '20%', delay: '6s'  },
            { w:  80, h:  80, t: '30%',  l: '80%', delay: '2s'  },
          ].map((s, i) => (
            <div key={i} className="float-shape" style={{
              width: s.w, height: s.h, top: s.t, left: s.l,
              animationDelay: s.delay,
            }} />
          ))}

          <div style={{ position: 'relative', zIndex: 1, textAlign: 'center', maxWidth: 520 }}>
            <div style={{
              width: 90, height: 90, borderRadius: 24,
              background: 'var(--grad-primary)', margin: '0 auto 28px',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '2.5rem', boxShadow: 'var(--shadow-glow)',
            }}>🎓</div>

            <h1 style={{ fontFamily: "'Outfit',sans-serif", fontSize: '2.8rem', fontWeight: 900, lineHeight: 1.1, marginBottom: 16 }}>
              NSBM<br />
              <span style={{ background: 'var(--grad-secondary)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                EduSphere
              </span>
            </h1>

            <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem', lineHeight: 1.7, marginBottom: 36 }}>
              Your all-in-one intelligent university portal with AI-powered assistance, real-time collaboration, and seamless academic management.
            </p>

            <div style={{ display: 'flex', justifyContent: 'center', gap: 24, flexWrap: 'wrap' }}>
              {[
                { icon: '🤖', label: 'RAG + MCP AI' },
                { icon: '📚', label: 'Smart Library' },
                { icon: '📊', label: 'Live Analytics' },
                { icon: '⚽', label: 'Campus Life' },
              ].map((f) => (
                <div key={f.label} style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
                  padding: '16px 20px', background: 'rgba(255,255,255,.06)',
                  border: '1px solid rgba(255,255,255,.1)', borderRadius: 16,
                }}>
                  <span style={{ fontSize: '1.5rem' }}>{f.icon}</span>
                  <span style={{ fontSize: '.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>{f.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right — form */}
        <div className="login-right">
          <div className="login-form">
            <div className="login-logo">🎓</div>
            <h2 style={{ fontFamily: "'Outfit',sans-serif", fontSize: '1.7rem', fontWeight: 800, marginBottom: 6 }}>
              Welcome back
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '.875rem', marginBottom: 28 }}>
              Sign in to your EduSphere portal
            </p>

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div className="form-group">
                <label className="form-label">Username</label>
                <input className="form-control" type="text" placeholder="Enter your username"
                  value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
              </div>
              <div className="form-group">
                <label className="form-label">Password</label>
                <input className="form-control" type="password" placeholder="Enter your password"
                  value={password} onChange={(e) => setPassword(e.target.value)} />
              </div>

              <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading}>
                {loading ? '⏳ Signing in...' : '🚀 Sign In'}
              </button>
            </form>

            {/* Quick Demo Logins */}
            <div style={{ marginTop: 28, paddingTop: 24, borderTop: '1px solid var(--border)' }}>
              <div style={{ fontSize: '.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.1em', color: 'var(--text-muted)', marginBottom: 12 }}>
                Quick Demo Login
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 8 }}>
                {[
                  { role: 'student',  label: '🎓 Student',  color: '#6C63FF' },
                  { role: 'lecturer', label: '👨‍🏫 Lecturer', color: '#00D4AA' },
                  { role: 'alumni',   label: '🌐 Alumni',    color: '#FFD700' },
                  { role: 'admin',    label: '⚙️ Admin',     color: '#FF6B6B' },
                ].map((d) => (
                  <button key={d.role} type="button"
                    onClick={() => fillDemo(d.role)}
                    className="btn btn-ghost btn-sm"
                    style={{ justifyContent: 'center', borderColor: d.color + '44', color: d.color }}>
                    {d.label}
                  </button>
                ))}
              </div>
              <p style={{ fontSize: '.7rem', color: 'var(--text-muted)', marginTop: 10, textAlign: 'center' }}>
                Click a role to auto-fill credentials, then Sign In
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
