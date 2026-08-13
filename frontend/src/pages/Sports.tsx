import React, { useEffect, useState } from 'react'
import api from '@/api/client'
import toast from 'react-hot-toast'
import type { Club, ClubEvent } from '@/types'
import { useAuth } from '@/contexts/AuthContext'

const CAT_COLOR: Record<string, string> = {
  sports: '#FF6B6B', technical: '#6C63FF', cultural: '#FFB347',
  academic: '#00D4AA', social: '#FF64C8',
}
const CAT_EMOJI: Record<string, string> = {
  sports: '⚽', technical: '💻', cultural: '🎭', academic: '🎓', social: '🌱',
}

export default function Sports() {
  const { user } = useAuth()
  const [clubs, setClubs] = useState<Club[]>([])
  const [events, setEvents] = useState<ClubEvent[]>([])
  const [activeTab, setActiveTab] = useState<'clubs' | 'events'>('clubs')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get<Club[]>('/sports/clubs').then(r => setClubs(r.data)),
      api.get<ClubEvent[]>('/sports/events?upcoming_only=true').then(r => setEvents(r.data)),
    ]).finally(() => setLoading(false))
  }, [])

  const joinClub = async (clubId: number, name: string) => {
    try {
      await api.post(`/sports/clubs/${clubId}/join`)
      toast.success(`🎉 Joined ${name}!`)
    } catch (e: any) {
      toast(e.response?.data?.detail || 'Could not join club', { icon: '⚠️' })
    }
  }

  const registerEvent = async (eventId: number) => {
    try {
      await api.post(`/sports/events/${eventId}/register`)
      toast.success('✅ Registered for event!')
    } catch (e: any) {
      toast(e.response?.data?.detail || 'Could not register', { icon: '⚠️' })
    }
  }

  if (loading) return <div className="flex justify-center items-center" style={{ height: 300 }}><div className="spinner" /></div>

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-title">⚽ Sports & Clubs</div>
        <div className="page-subtitle">{clubs.length} active clubs · {events.length} upcoming events</div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button className={`tab-btn ${activeTab === 'clubs' ? 'active' : ''}`} onClick={() => setActiveTab('clubs')}>🏆 Clubs</button>
        <button className={`tab-btn ${activeTab === 'events' ? 'active' : ''}`} onClick={() => setActiveTab('events')}>📅 Events</button>
      </div>

      {/* Clubs Grid */}
      {activeTab === 'clubs' && (
        <div className="grid-auto">
          {clubs.map(c => {
            const color = CAT_COLOR[c.category] || '#6C63FF'
            const emoji = CAT_EMOJI[c.category] || '🏆'
            const full = c.member_count >= c.max_members
            return (
              <div key={c.id} className="club-card">
                <div className="club-cover" style={{ background: `linear-gradient(135deg, ${color}28, ${color}0d)` }}>
                  <span>{emoji}</span>
                  <span className="badge" style={{ position: 'absolute', top: 10, right: 10, background: `${color}28`, color, borderColor: `${color}55` }}>
                    {c.category}
                  </span>
                </div>
                <div className="club-body">
                  <div className="club-name">{c.name}</div>
                  <div className="club-desc">{c.description}</div>
                  <div className="flex gap-16 text-xs text-muted mb-16">
                    <span>👥 {c.member_count} / {c.max_members} members</span>
                    {c.president_name && <span>👑 {c.president_name}</span>}
                  </div>
                  <div className="flex gap-8">
                    {user?.role === 'student' && (
                      <button className="btn btn-primary btn-sm" style={{ flex: 1 }}
                        onClick={() => joinClub(c.id, c.name)} disabled={full}>
                        {full ? '🔒 Full' : 'Join Club'}
                      </button>
                    )}
                    <button className="btn btn-ghost btn-sm">Details</button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Events List */}
      {activeTab === 'events' && (
        <div className="flex flex-col gap-16">
          {events.length === 0 && (
            <div className="card" style={{ textAlign: 'center', padding: 48 }}>
              <div style={{ fontSize: '3rem', marginBottom: 12 }}>📅</div>
              <div className="text-muted">No upcoming events scheduled</div>
            </div>
          )}
          {events.map(e => {
            const d = new Date(e.event_date)
            const color = CAT_COLOR[e.club_category] || '#6C63FF'
            return (
              <div key={e.id} className="event-item" style={{ padding: 20 }}>
                <div className="event-date-box" style={{ width: 60, height: 60, borderRadius: 14, background: `linear-gradient(135deg, ${color}, ${color}aa)` }}>
                  <div className="event-day" style={{ fontSize: '1.3rem' }}>{d.getDate()}</div>
                  <div className="event-month">{d.toLocaleString('default', { month: 'short' })}</div>
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: '1rem' }}>{e.title}</div>
                  <div className="text-sm text-muted mt-8">
                    🏆 {e.club} · 📍 {e.location || 'TBD'} · ⏰ {d.toLocaleTimeString('default', { hour: '2-digit', minute: '2-digit' })}
                  </div>
                  {e.description && <div className="text-sm text-secondary mt-8" style={{ lineHeight: 1.5 }}>{e.description}</div>}
                </div>
                {e.registration_required
                  ? <button className="btn btn-teal btn-sm" onClick={() => registerEvent(e.id)}>Register</button>
                  : <span className="badge badge-success">Open</span>
                }
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
