// Profile.tsx
import React, { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import api from '@/api/client'
import toast from 'react-hot-toast'

export default function Profile() {
  const { user } = useAuth()
  const [oldPw, setOldPw] = useState('')
  const [newPw, setNewPw] = useState('')

  if (!user) return null
  const initials = user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)

  const changePassword = async () => {
    try {
      await api.post(`/auth/change-password?old_password=${encodeURIComponent(oldPw)}&new_password=${encodeURIComponent(newPw)}`)
      toast.success('✅ Password updated!')
      setOldPw(''); setNewPw('')
    } catch (e: any) { toast.error(e.response?.data?.detail || 'Error') }
  }

  return (
    <div className="fade-in" style={{ maxWidth: 700, margin: '0 auto' }}>
      <div className="page-header"><div className="page-title">👤 My Profile</div></div>

      <div className="card mb-24" style={{ textAlign: 'center' }}>
        <div className="avatar avatar-xl" style={{ margin: '0 auto 16px' }}>{initials}</div>
        <div style={{ fontFamily: "'Outfit',sans-serif", fontSize: '1.5rem', fontWeight: 800 }}>{user.full_name}</div>
        <div className="text-muted mt-8">@{user.username}</div>
        <span className="badge badge-info mt-8">{user.role}</span>
      </div>

      <div className="card mb-24">
        <div className="card-title mb-16">Account Information</div>
        {[['📧 Email', user.email], ['👤 Username', user.username], ['🎭 Role', user.role], ['✅ Status', user.is_active ? 'Active' : 'Inactive']].map(([l, v]) => (
          <div key={String(l)} className="flex justify-between" style={{ padding: '12px 0', borderBottom: '1px solid rgba(255,255,255,.05)' }}>
            <span className="text-muted text-sm">{l}</span>
            <span style={{ fontWeight: 600 }}>{v}</span>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-title mb-16">🔒 Change Password</div>
        <div className="flex flex-col gap-12">
          <input type="password" className="form-control" placeholder="Current password" value={oldPw} onChange={e => setOldPw(e.target.value)} />
          <input type="password" className="form-control" placeholder="New password (min 8 chars)" value={newPw} onChange={e => setNewPw(e.target.value)} />
          <button className="btn btn-primary" onClick={changePassword}>Update Password</button>
        </div>
      </div>
    </div>
  )
}
