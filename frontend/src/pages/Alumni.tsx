import React, { useEffect, useState } from 'react'
import api from '@/api/client'
import toast from 'react-hot-toast'
import type { AlumniMember, AlumniExperience, Paginated } from '@/types'
import { useAuth } from '@/contexts/AuthContext'

const ini = (name: string) => name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)

function AlumniNetwork() {
  const [alumni, setAlumni] = useState<AlumniMember[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<Paginated<AlumniMember>>('/alumni/network?page=1&size=12')
      .then(r => { setAlumni(r.data.items); setTotal(r.data.total) })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center items-center" style={{ height: 300 }}><div className="spinner" /></div>

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-title">🌐 Alumni Network</div>
        <div className="page-subtitle">{total} NSBM graduates worldwide</div>
      </div>
      <div className="grid-auto">
        {alumni.map(a => (
          <div key={a.id} className="alumni-card">
            <div className="avatar avatar-lg">{ini(a.full_name)}</div>
            <div>
              <div style={{ fontWeight: 700, fontSize: '1rem' }}>{a.full_name}</div>
              <div className="text-sm text-muted">{a.current_position}</div>
              <div className="text-sm text-muted">{a.current_company}</div>
            </div>
            <span className="badge badge-info">{a.graduation_year}</span>
            <div className="text-xs text-muted">📍 {a.location || 'Sri Lanka'} · {a.industry}</div>
            {a.willing_to_mentor && <span className="badge badge-success">🤝 Available to Mentor</span>}
            <div className="flex gap-8 w-full">
              {a.willing_to_mentor && <button className="btn btn-primary btn-sm" style={{ flex: 1 }}>Request Mentorship</button>}
              {a.linkedin_url && <a href={a.linkedin_url} target="_blank" rel="noreferrer" className="btn btn-ghost btn-sm">LinkedIn</a>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function Experiences() {
  const { user } = useAuth()
  const [experiences, setExperiences] = useState<AlumniExperience[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<AlumniExperience[]>('/alumni/experiences?page=1&size=10')
      .then(r => setExperiences(r.data))
      .finally(() => setLoading(false))
  }, [])

  const like = async (id: number) => {
    const r = await api.post<{ likes: number }>(`/alumni/experiences/${id}/like`)
    setExperiences(prev => prev.map(e => e.id === id ? { ...e, likes: r.data.likes } : e))
  }

  if (loading) return <div className="flex justify-center items-center" style={{ height: 300 }}><div className="spinner" /></div>

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="flex justify-between items-center" style={{ flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div className="page-title">💬 Alumni Experiences</div>
            <div className="page-subtitle">Stories from NSBM graduates</div>
          </div>
          {user?.role === 'alumni' && <button className="btn btn-primary">✍️ Share Your Story</button>}
        </div>
      </div>
      <div className="flex flex-col gap-20">
        {experiences.map(e => (
          <div key={e.id} className="card">
            <div className="flex gap-16">
              <div className="avatar avatar-md">{ini(e.author)}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700, fontSize: '1.05rem', marginBottom: 6 }}>{e.title}</div>
                <div className="text-xs text-muted mb-12">
                  ✍️ {e.author} · {e.category} · Class of {e.graduation_year} {e.company && `· ${e.company}`}
                </div>
                <div className="text-sm text-secondary" style={{ lineHeight: 1.75 }}>
                  {e.content.slice(0, 300)}...
                </div>
                <div className="flex items-center gap-8 mt-12">
                  {(e.tags || []).map(t => <span key={t} className="badge badge-info">{t}</span>)}
                  <button className="btn btn-ghost btn-sm" style={{ marginLeft: 'auto' }} onClick={() => like(e.id)}>
                    ❤️ {e.likes}
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export { AlumniNetwork, Experiences }
