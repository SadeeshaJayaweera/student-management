import React, { useEffect, useState } from 'react'
import api from '@/api/client'
import toast from 'react-hot-toast'
import type {
  Club,
  ClubEvent,
  AthleticTeam,
  SportsFixture,
  SportsFacilityBooking,
  AthleticStats,
} from '@/types'
import { useAuth } from '@/contexts/AuthContext'

const CAT_COLOR: Record<string, string> = {
  sports: '#FF6B6B', technical: '#6C63FF', cultural: '#FFB347',
  academic: '#00D4AA', social: '#FF64C8',
}
const CAT_EMOJI: Record<string, string> = {
  sports: '⚽', technical: '💻', cultural: '🎭', academic: '🎓', social: '🌱',
}

const SPORT_ICONS: Record<string, string> = {
  cricket: '🏏',
  rugby: '🏉',
  football: '⚽',
  basketball: '🏀',
  swimming: '🏊',
  badminton: '🏸',
  esports: '🎮',
  tennis: '🎾',
  volleyball: '🏐',
}

export default function Sports() {
  const { user } = useAuth()
  const isStaff = user?.role === 'admin' || user?.role === 'lecturer'

  // Tabs: 'teams' | 'fixtures' | 'facilities' | 'clubs' | 'events'
  const [activeTab, setActiveTab] = useState<'teams' | 'fixtures' | 'facilities' | 'clubs' | 'events'>('teams')

  // Athletic department state
  const [teams, setTeams] = useState<AthleticTeam[]>([])
  const [fixtures, setFixtures] = useState<SportsFixture[]>([])
  const [bookings, setBookings] = useState<SportsFacilityBooking[]>([])
  const [stats, setStats] = useState<AthleticStats | null>(null)
  const [selectedTeam, setSelectedTeam] = useState<AthleticTeam | null>(null)

  // Clubs and events state
  const [clubs, setClubs] = useState<Club[]>([])
  const [events, setEvents] = useState<ClubEvent[]>([])
  const [loading, setLoading] = useState(true)

  // Facility booking modal
  const [showBookingModal, setShowBookingModal] = useState<boolean>(false)
  const [facilityName, setFacilityName] = useState<string>('Indoor Sports Complex')
  const [bookingPurpose, setBookingPurpose] = useState<string>('Team Practice & Conditioning')
  const [bookingStartTime, setBookingStartTime] = useState<string>('')
  const [bookingEndTime, setBookingEndTime] = useState<string>('')
  const [submittingBooking, setSubmittingBooking] = useState<boolean>(false)

  const loadData = async () => {
    try {
      setLoading(true)
      const [teamsR, fixR, bookR, statsR, clubsR, eventsR] = await Promise.all([
        api.get<AthleticTeam[]>('/athletics/teams'),
        api.get<SportsFixture[]>('/athletics/fixtures'),
        api.get<SportsFacilityBooking[]>('/athletics/facility-bookings'),
        api.get<AthleticStats>('/athletics/stats'),
        api.get<Club[]>('/sports/clubs'),
        api.get<ClubEvent[]>('/sports/events?upcoming_only=true'),
      ])
      setTeams(teamsR.data)
      setFixtures(fixR.data)
      setBookings(bookR.data)
      setStats(statsR.data)
      setClubs(clubsR.data)
      setEvents(eventsR.data)
    } catch (err) {
      console.error('Failed to load athletics data', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const joinClub = async (clubId: number, name: string) => {
    try {
      await api.post(`/sports/clubs/${clubId}/join`)
      toast.success(`🎉 Joined ${name}!`)
      loadData()
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

  const handleCreateBooking = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!facilityName || !bookingStartTime || !bookingEndTime || submittingBooking) return

    try {
      setSubmittingBooking(true)
      await api.post('/athletics/facility-bookings', {
        facility_name: facilityName,
        purpose: bookingPurpose,
        start_time: new Date(bookingStartTime).toISOString(),
        end_time: new Date(bookingEndTime).toISOString(),
      })
      toast.success('Facility reserved successfully!')
      setShowBookingModal(false)
      loadData()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to book facility.')
    } finally {
      setSubmittingBooking(false)
    }
  }

  if (loading) return <div className="flex justify-center items-center" style={{ height: 300 }}><div className="spinner" /></div>

  return (
    <div className="fade-in" style={{ maxWidth: 1200, margin: '0 auto', paddingBottom: 40 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1 className="page-title" style={{ margin: 0 }}>🏅 NSBM Sports & Athletic Management</h1>
          <p className="page-subtitle" style={{ margin: '4px 0 0 0' }}>
            Varsity athletic teams, SLUG tournaments, inter-university fixtures, and sports ground reservations.
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setShowBookingModal(true)}
          style={{ display: 'flex', alignItems: 'center', gap: 6 }}
        >
          <span>🏟️</span> Book Sports Facility
        </button>
      </div>

      {/* KPI Stats Banner */}
      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', marginBottom: 24 }}>
        <div className="stat-card stat-teal">
          <div className="stat-icon" style={{ background: 'rgba(0,212,170,.15)' }}>🏆</div>
          <div>
            <div className="stat-value" style={{ color: '#00D4AA' }}>{stats?.total_teams || teams.length}</div>
            <div className="stat-label">Varsity Squads</div>
          </div>
        </div>
        <div className="stat-card stat-purple">
          <div className="stat-icon" style={{ background: 'rgba(108,99,255,.18)' }}>🏃</div>
          <div>
            <div className="stat-value" style={{ color: '#8B85FF' }}>{stats?.total_athletes || 0}</div>
            <div className="stat-label">Student Athletes</div>
          </div>
        </div>
        <div className="stat-card stat-coral">
          <div className="stat-icon" style={{ background: 'rgba(255,107,107,.18)' }}>⚔️</div>
          <div>
            <div className="stat-value" style={{ color: '#FF6B6B' }}>{stats?.upcoming_fixtures_count || fixtures.filter(f => f.status === 'upcoming').length}</div>
            <div className="stat-label">Upcoming Fixtures</div>
          </div>
        </div>
        <div className="stat-card stat-gold">
          <div className="stat-icon" style={{ background: 'rgba(255,215,0,.1)' }}>🥇</div>
          <div>
            <div className="stat-value" style={{ color: '#FFD700' }}>{stats?.matches_won || 0}</div>
            <div className="stat-label">Match Victories</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 8, borderBottom: '1px solid var(--border-color)', marginBottom: 24, overflowX: 'auto' }}>
        {[
          { key: 'teams', label: '🏆 Teams & Rosters', count: teams.length },
          { key: 'fixtures', label: '⚔️ Fixtures & Results', count: fixtures.length },
          { key: 'facilities', label: '🏟️ Facility Schedule', count: bookings.length },
          { key: 'clubs', label: '🌱 Student Clubs', count: clubs.length },
          { key: 'events', label: '📅 Sports Events', count: events.length },
        ].map(t => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key as any)}
            style={{
              padding: '10px 18px',
              border: 'none',
              background: 'none',
              fontWeight: 700,
              fontSize: '0.9rem',
              cursor: 'pointer',
              borderBottom: activeTab === t.key ? '2px solid #34d399' : '2px solid transparent',
              color: activeTab === t.key ? '#34d399' : 'var(--text-muted)',
              whiteSpace: 'nowrap',
            }}
          >
            {t.label} ({t.count})
          </button>
        ))}
      </div>

      {/* TAB 1: Athletic Teams */}
      {activeTab === 'teams' && (
        <div className="grid-3">
          {teams.map(team => {
            const icon = SPORT_ICONS[team.sport_type] || '🏅'
            return (
              <div key={team.id} className="card" style={{ padding: 20, display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                  <div style={{ fontSize: '2.5rem', width: 56, height: 56, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.04)', borderRadius: 12 }}>
                    {icon}
                  </div>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800 }}>{team.name}</h3>
                    <div className="text-muted" style={{ fontSize: '0.8rem', textTransform: 'uppercase' }}>
                      {team.division} • {team.sport_type}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.85rem', marginBottom: 16 }}>
                  {team.captain_name && (
                    <div><span className="text-muted">Captain:</span> <strong>{team.captain_name}</strong></div>
                  )}
                  {team.coach_name && (
                    <div><span className="text-muted">Head Coach:</span> <strong>{team.coach_name}</strong></div>
                  )}
                  {team.home_venue && (
                    <div><span className="text-muted">Home Venue:</span> {team.home_venue}</div>
                  )}
                  <div><span className="text-muted">Roster Strength:</span> <strong>{team.roster?.length || 0} Athletes</strong></div>
                </div>

                <div style={{ marginTop: 'auto' }}>
                  <button
                    onClick={() => setSelectedTeam(team)}
                    className="btn btn-secondary btn-sm btn-full"
                  >
                    View Roster & Schedule 👁
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* TAB 2: Fixtures & SLUG Tournaments */}
      {activeTab === 'fixtures' && (
        <div className="flex flex-col gap-12">
          {fixtures.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: 48 }}>
              <div style={{ fontSize: '3rem', marginBottom: 10 }}>⚔️</div>
              <h4 style={{ margin: 0, fontWeight: 700 }}>No Fixtures Scheduled</h4>
              <p className="text-muted" style={{ margin: '6px 0 0 0', fontSize: '0.88rem' }}>
                Check back later for updated match schedules and tournament draws.
              </p>
            </div>
          ) : (
            fixtures.map(f => {
              const dt = new Date(f.scheduled_time)
              const isPast = f.status === 'completed'
              const won = f.match_result === 'won'
              return (
                <div key={f.id} className="card" style={{ padding: 18, display: 'flex', alignItems: 'center', gap: 16 }}>
                  <div
                    style={{
                      width: 64,
                      height: 64,
                      borderRadius: 12,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: 'rgba(255, 255, 255, 0.04)',
                      border: '1px solid var(--border-color)',
                    }}
                  >
                    <span style={{ fontSize: '1.2rem', fontWeight: 800 }}>{dt.getDate()}</span>
                    <span style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase' }}>
                      {dt.toLocaleString('default', { month: 'short' })}
                    </span>
                  </div>

                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>{f.tournament_name}</span>
                      <span className="text-muted" style={{ fontSize: '0.78rem' }}>• {f.fixture_type.toUpperCase()}</span>
                    </div>
                    <div style={{ fontSize: '1.05rem', fontWeight: 800, marginTop: 4 }}>
                      {f.team_name || 'NSBM'} <span style={{ color: '#94a3b8', fontWeight: 400 }}>vs</span> {f.opponent_name}
                    </div>
                    <div className="text-muted" style={{ fontSize: '0.82rem', marginTop: 2 }}>
                      📍 {f.venue} · ⏰ {dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>

                  {isPast ? (
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '1.15rem', fontWeight: 800 }}>
                        {f.our_score || '0'} - {f.opponent_score || '0'}
                      </div>
                      <span
                        className={`badge ${won ? 'badge-success' : f.match_result === 'lost' ? 'badge-danger' : 'badge-info'}`}
                        style={{ fontSize: '0.75rem', marginTop: 4 }}
                      >
                        {f.match_result ? f.match_result.toUpperCase() : 'COMPLETED'}
                      </span>
                    </div>
                  ) : (
                    <div>
                      <span className="badge badge-gold" style={{ fontSize: '0.75rem' }}>UPCOMING</span>
                    </div>
                  )}
                </div>
              )
            })
          )}
        </div>
      )}

      {/* TAB 3: Sports Facility Bookings */}
      {activeTab === 'facilities' && (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700 }}>Campus Sports Facilities & Grounds Schedule</h3>
            <span className="text-muted" style={{ fontSize: '0.84rem' }}>{bookings.length} reservations</span>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', color: '#94a3b8', fontSize: '0.8rem', textTransform: 'uppercase' }}>
                  <th style={{ padding: '12px 18px' }}>Facility</th>
                  <th style={{ padding: '12px 18px' }}>Booked By</th>
                  <th style={{ padding: '12px 18px' }}>Team</th>
                  <th style={{ padding: '12px 18px' }}>Start Time</th>
                  <th style={{ padding: '12px 18px' }}>End Time</th>
                  <th style={{ padding: '12px 18px' }}>Purpose</th>
                  <th style={{ padding: '12px 18px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {bookings.map(b => (
                  <tr key={b.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                    <td style={{ padding: '12px 18px', fontWeight: 700, color: '#38bdf8' }}>{b.facility_name}</td>
                    <td style={{ padding: '12px 18px' }}>{b.booked_by_name || 'Member'}</td>
                    <td style={{ padding: '12px 18px' }}>{b.team_name || 'General Athletics'}</td>
                    <td style={{ padding: '12px 18px' }}>{new Date(b.start_time).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</td>
                    <td style={{ padding: '12px 18px' }}>{new Date(b.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</td>
                    <td style={{ padding: '12px 18px' }}>{b.purpose}</td>
                    <td style={{ padding: '12px 18px' }}>
                      <span className="badge badge-success" style={{ fontSize: '0.72rem' }}>{b.status.toUpperCase()}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 4: Student Clubs */}
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
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* TAB 5: Events */}
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

      {/* Team Roster Modal */}
      {selectedTeam && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(5px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
          }}
        >
          <div className="card" style={{ width: '100%', maxWidth: 640, maxHeight: '85vh', overflowY: 'auto', padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.3rem', fontWeight: 800 }}>{selectedTeam.name} Roster</h3>
                <div className="text-muted" style={{ fontSize: '0.82rem' }}>
                  {selectedTeam.division} • Head Coach: {selectedTeam.coach_name || 'N/A'}
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelectedTeam(null)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '1.2rem' }}
              >
                ✕
              </button>
            </div>

            {selectedTeam.roster.length === 0 ? (
              <div style={{ padding: 32, textAlign: 'center' }} className="text-muted">
                No registered athletes in this team roster yet.
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.86rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-color)', color: '#94a3b8', textTransform: 'uppercase' }}>
                      <th style={{ padding: '8px 12px' }}>#</th>
                      <th style={{ padding: '8px 12px' }}>Athlete</th>
                      <th style={{ padding: '8px 12px' }}>Role / Position</th>
                      <th style={{ padding: '8px 12px' }}>Fitness</th>
                      <th style={{ padding: '8px 12px' }}>Games</th>
                      <th style={{ padding: '8px 12px' }}>MVP</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedTeam.roster.map(a => (
                      <tr key={a.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                        <td style={{ padding: '8px 12px', fontWeight: 700, color: '#38bdf8' }}>{a.jersey_number || '—'}</td>
                        <td style={{ padding: '8px 12px', fontWeight: 600 }}>{a.student_name}</td>
                        <td style={{ padding: '8px 12px' }}>{a.position_or_role}</td>
                        <td style={{ padding: '8px 12px' }}>
                          <span className={`badge ${a.fitness_status === 'fit' ? 'badge-success' : 'badge-danger'}`} style={{ fontSize: '0.7rem' }}>
                            {a.fitness_status.toUpperCase()}
                          </span>
                        </td>
                        <td style={{ padding: '8px 12px' }}>{a.matches_played}</td>
                        <td style={{ padding: '8px 12px' }}>{a.mvp_awards}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setSelectedTeam(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Facility Booking Modal */}
      {showBookingModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(5px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
          }}
        >
          <div className="card" style={{ width: '100%', maxWidth: 500, padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800 }}>Reserve Sports Facility</h3>
              <button
                type="button"
                onClick={() => setShowBookingModal(false)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '1.2rem' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateBooking}>
              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Campus Facility *
                </label>
                <select
                  className="form-control"
                  value={facilityName}
                  onChange={e => setFacilityName(e.target.value)}
                  required
                >
                  <option value="Indoor Sports Complex">Indoor Sports Complex (Badminton/Basketball)</option>
                  <option value="Cricket Grounds & Practice Nets">Cricket Grounds & Practice Nets</option>
                  <option value="Rugby & Football Field">Rugby & Football Field</option>
                  <option value="Olympic Swimming Pool">Olympic Swimming Pool</option>
                  <option value="Fitness & Conditioning Gymnasium">Fitness & Conditioning Gymnasium</option>
                </select>
              </div>

              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Purpose / Training Session *
                </label>
                <input
                  type="text"
                  className="form-control"
                  value={bookingPurpose}
                  onChange={e => setBookingPurpose(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                    Start Time *
                  </label>
                  <input
                    type="datetime-local"
                    className="form-control"
                    value={bookingStartTime}
                    onChange={e => setBookingStartTime(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                    End Time *
                  </label>
                  <input
                    type="datetime-local"
                    className="form-control"
                    value={bookingEndTime}
                    onChange={e => setBookingEndTime(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowBookingModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submittingBooking}>
                  {submittingBooking ? 'Reserving...' : 'Confirm Reservation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
