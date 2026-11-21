import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import api from '@/api/client'
import type { StudentDashboard, LecturerDashboard, AdminDashboard, PersonalizedStudentDashboard } from '@/types'
import { Bar } from 'react-chartjs-2'
import { Chart, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js'
Chart.register(BarElement, CategoryScale, LinearScale, Tooltip, Legend)

// ── Helpers ────────────────────────────────────────────────────

const initials = (name: string) =>
  name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)

const letterClass = (l: string | null) =>
  !l ? 'badge-warning' : l.startsWith('A') ? 'badge-success' : l.startsWith('B') ? 'badge-info' : l === 'F' ? 'badge-danger' : 'badge-warning'

// ── Stat Card Component ────────────────────────────────────────

function StatCard({ icon, value, label, color, bg, variant }: {
  icon: string; value: string | number; label: string
  color: string; bg: string; variant: string
}) {
  return (
    <div className={`stat-card ${variant}`}>
      <div className="stat-icon" style={{ background: bg }}>{icon}</div>
      <div>
        <div className="stat-value" style={{ color }}>{value}</div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  )
}

// ── GPA Ring ───────────────────────────────────────────────────

function GpaRing({ gpa }: { gpa: number }) {
  const r = 65; const circ = 2 * Math.PI * r
  const dash = (gpa / 4) * circ
  return (
    <div className="gpa-ring">
      <svg width="160" height="160" viewBox="0 0 160 160">
        <circle cx="80" cy="80" r={r} fill="none" stroke="rgba(255,255,255,.06)" strokeWidth="12" />
        <circle cx="80" cy="80" r={r} fill="none"
          stroke="url(#g1)" strokeWidth="12"
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round" />
        <defs>
          <linearGradient id="g1" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#6C63FF" />
            <stop offset="100%" stopColor="#00D4AA" />
          </linearGradient>
        </defs>
      </svg>
      <div className="gpa-ring-val">{gpa.toFixed(2)}</div>
    </div>
  )
}

// ── Student Dashboard ──────────────────────────────────────────

function StudentDash() {
  const [data, setData] = useState<StudentDashboard | null>(null)
  const [personalized, setPersonalized] = useState<PersonalizedStudentDashboard | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.get<StudentDashboard>('/students/dashboard').then(r => setData(r.data))
    api.get<PersonalizedStudentDashboard>('/students/dashboard/personalized')
      .then(r => setPersonalized(r.data))
      .catch(() => console.info('Personalized dashboard endpoint loading or fallback.'))
  }, [])

  if (!data) return <div className="flex justify-center items-center" style={{ height: 300 }}><div className="spinner" /></div>

  const hour = new Date().getHours()
  const greeting = hour < 12 ? '☀️ Good Morning' : hour < 17 ? '🌤️ Good Afternoon' : '🌙 Good Evening'
  const gpaColor = data.gpa >= 3.5 ? '#00D4AA' : data.gpa >= 2.5 ? '#8B85FF' : data.gpa >= 2.0 ? '#FFB347' : '#FF6B6B'
  const attOk = data.attendance_rate >= 80

  return (
    <div className="fade-in">
      {/* Hero */}
      <div className="hero-banner">
        <div className="hero-badge">🎓 Student Portal</div>
        <div className="hero-greeting">{greeting}, {data.full_name.split(' ')[0]}! 👋</div>
        <div className="hero-sub">{data.program} · Year {data.year_of_study} Sem {data.semester} · {data.faculty}</div>
        <div className="flex items-center gap-24 mt-16" style={{ flexWrap: 'wrap' }}>
          <div className="text-sm text-muted">Student ID: <span style={{ color: '#8B85FF', fontWeight: 600 }}>{data.student_id}</span></div>
          <div className="text-sm text-muted">Department: <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>{data.department}</span></div>
        </div>
      </div>

      {/* Personalized Recommendations */}
      {personalized && personalized.recommendations && personalized.recommendations.length > 0 && (
        <div className="mb-24">
          <div className="card-title mb-12">💡 Personalized Recommendations</div>
          <div className="grid-2 gap-16">
            {personalized.recommendations.map(rec => (
              <div
                key={rec.id}
                className="card"
                style={{
                  borderLeft: rec.priority === 'high' ? '4px solid #FF6B6B' : rec.priority === 'medium' ? '4px solid #FFB347' : '4px solid #00D4AA',
                  padding: '16px 20px',
                  marginBottom: 0
                }}
              >
                <div className="flex justify-between items-center mb-8">
                  <span style={{ fontWeight: 600, fontSize: '.9rem' }}>{rec.title}</span>
                  <span className={`badge ${rec.priority === 'high' ? 'badge-danger' : rec.priority === 'medium' ? 'badge-warning' : 'badge-success'}`}>
                    {rec.priority.toUpperCase()}
                  </span>
                </div>
                <p className="text-xs text-muted mb-12" style={{ lineHeight: 1.5 }}>{rec.description}</p>
                <button
                  className="btn btn-primary btn-sm"
                  style={{ fontSize: '.75rem', padding: '4px 12px' }}
                  onClick={() => navigate(rec.action_link)}
                >
                  {rec.action_label} →
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="stat-grid">
        <StatCard icon="📚" value={data.enrolled_courses} label="Courses" color="#8B85FF" bg="rgba(108,99,255,.18)" variant="stat-purple" />
        <StatCard icon="⭐" value={data.gpa.toFixed(2)} label="GPA" color={gpaColor} bg="rgba(0,212,170,.15)" variant="stat-teal" />
        <StatCard icon="📝" value={data.pending_assignments} label="Pending" color="#FF6B6B" bg="rgba(255,107,107,.18)" variant="stat-coral" />
        <StatCard icon="🎯" value={`${data.attendance_rate}%`} label="Attendance" color="#FFD700" bg="rgba(255,215,0,.12)" variant="stat-gold" />
        <StatCard icon="📖" value={data.borrowed_books} label="Borrowed" color="#0099FF" bg="rgba(0,153,255,.14)" variant="stat-blue" />
        <StatCard icon="🏅" value={data.credits_earned} label="Credits" color="#FF64C8" bg="rgba(255,100,200,.14)" variant="stat-pink" />
      </div>

      {/* Quick Actions */}
      <div className="mb-24">
        <div className="card-title mb-16">⚡ Quick Actions</div>
        <div className="quick-actions">
          {[
            { to: '/grades',      icon: '📊', label: 'View Grades' },
            { to: '/assignments', icon: '📝', label: 'Assignments' },
            { to: '/library',     icon: '📚', label: 'Library' },
            { to: '/timetable',   icon: '⏰', label: 'Timetable' },
            { to: '/sports',      icon: '⚽', label: 'Clubs' },
            { to: '/ai-chat',     icon: '🤖', label: 'AI Help' },
          ].map(a => (
            <div key={a.to} className="quick-action" onClick={() => navigate(a.to)}>
              <div className="quick-action-icon">{a.icon}</div>
              <div className="quick-action-label">{a.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Course Progress Breakdown */}
      {personalized && personalized.courses_progress && personalized.courses_progress.length > 0 && (
        <div className="card mb-24">
          <div className="flex justify-between items-center mb-16">
            <div>
              <div className="card-title">📖 Course Progress & Academic Standing</div>
              <div className="card-subtitle">Active enrollments and lesson completion rates</div>
            </div>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/courses')}>All Courses →</button>
          </div>
          <div className="grid-2 gap-16">
            {personalized.courses_progress.map(cp => (
              <div key={cp.course_id} style={{ padding: 14, background: 'rgba(255,255,255,.03)', borderRadius: 10, border: '1px solid rgba(255,255,255,.06)' }}>
                <div className="flex justify-between items-center mb-6">
                  <div style={{ fontWeight: 600, fontSize: '.9rem' }}>{cp.course_code}: {cp.course_title}</div>
                  {cp.letter_grade && <span className={`badge ${letterClass(cp.letter_grade)}`}>{cp.letter_grade}</span>}
                </div>
                <div className="text-xs text-muted mb-8">Lecturer: {cp.lecturer_name} · Attendance: {cp.attendance_rate}%</div>
                <div className="flex justify-between text-xs text-muted mb-4">
                  <span>Lesson Progress</span>
                  <span>{cp.completed_lessons}/{cp.total_lessons} ({cp.progress_percentage}%)</span>
                </div>
                <div className="progress progress-primary" style={{ height: 6 }}>
                  <div className="progress-bar" style={{ width: `${cp.progress_percentage}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upcoming Deadlines & Classes */}
      {personalized && (
        <div className="grid-2 mb-24">
          {/* Upcoming Deadlines */}
          <div className="card">
            <div className="flex justify-between items-center mb-16">
              <div>
                <div className="card-title">⏳ Upcoming Deadlines</div>
                <div className="card-subtitle">Assignments and timed quizzes</div>
              </div>
              <button className="btn btn-ghost btn-sm" onClick={() => navigate('/assignments')}>View All →</button>
            </div>
            {personalized.upcoming_deadlines.length > 0 ? (
              <div className="flex flex-col gap-10">
                {personalized.upcoming_deadlines.slice(0, 4).map(d => (
                  <div key={`${d.item_type}-${d.id}`} className="flex justify-between items-center" style={{ padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,.04)' }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '.85rem' }}>{d.title}</div>
                      <div className="text-xs text-muted">{d.course_code} · Due {new Date(d.due_date).toLocaleDateString()}</div>
                    </div>
                    <span className={`badge ${d.submission_status === 'submitted' || d.submission_status === 'graded' ? 'badge-success' : d.is_overdue ? 'badge-danger' : 'badge-warning'}`}>
                      {d.submission_status.toUpperCase()}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-muted" style={{ textAlign: 'center', padding: 20 }}>No pending deadlines</div>
            )}
          </div>

          {/* Upcoming Virtual Classes */}
          <div className="card">
            <div className="flex justify-between items-center mb-16">
              <div>
                <div className="card-title">💻 Virtual Classrooms</div>
                <div className="card-subtitle">Scheduled live lectures & sessions</div>
              </div>
            </div>
            {personalized.upcoming_classes.length > 0 ? (
              <div className="flex flex-col gap-10">
                {personalized.upcoming_classes.slice(0, 4).map(s => (
                  <div key={s.session_id} className="flex justify-between items-center" style={{ padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,.04)' }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '.85rem' }}>
                        {s.is_live && <span style={{ color: '#FF453A', marginRight: 6 }}>● LIVE</span>}
                        {s.title}
                      </div>
                      <div className="text-xs text-muted">{s.course_code} · {new Date(s.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ({s.duration_minutes}m)</div>
                    </div>
                    {s.join_url ? (
                      <a href={s.join_url} target="_blank" rel="noreferrer" className="btn btn-primary btn-sm" style={{ fontSize: '.75rem', padding: '3px 10px' }}>
                        Join
                      </a>
                    ) : (
                      <span className="badge badge-info">{s.session_type}</span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-xs text-muted" style={{ textAlign: 'center', padding: 20 }}>No live classes scheduled today</div>
            )}
          </div>
        </div>
      )}

      <div className="grid-2">
        {/* Grades */}
        <div className="card">
          <div className="flex justify-between items-center mb-16">
            <div><div className="card-title">📊 Recent Grades</div><div className="card-subtitle">Latest results</div></div>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/grades')}>View All →</button>
          </div>
          {data.recent_grades.map((g, i) => (
            <div key={i} className="flex justify-between items-center"
              style={{ padding: '11px 0', borderBottom: '1px solid rgba(255,255,255,.05)' }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: '.875rem' }}>{g.course}</div>
                <div className="text-xs text-muted">{g.course_code}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span className={`badge ${letterClass(g.letter)}`}>{g.letter || '—'}</span>
                <div className="text-xs text-muted mt-8">{g.total ? g.total.toFixed(1) : '—'}%</div>
              </div>
            </div>
          ))}
          {data.recent_grades.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <div className="flex justify-between text-xs text-muted mb-8">
                <span>GPA Progress</span>
                <span style={{ color: gpaColor, fontWeight: 700 }}>{data.gpa.toFixed(2)} / 4.00</span>
              </div>
              <div className="progress progress-primary">
                <div className="progress-bar" style={{ width: `${(data.gpa / 4) * 100}%` }} />
              </div>
            </div>
          )}
        </div>

        {/* Events */}
        <div className="card">
          <div className="flex justify-between items-center mb-16">
            <div><div className="card-title">📅 Upcoming Events</div><div className="card-subtitle">Campus activities</div></div>
            <button className="btn btn-ghost btn-sm" onClick={() => navigate('/sports')}>View All →</button>
          </div>
          <div className="flex flex-col gap-12">
            {data.upcoming_events.length ? data.upcoming_events.map((e, i) => {
              const d = new Date(e.date)
              return (
                <div key={i} className="event-item">
                  <div className="event-date-box">
                    <div className="event-day">{d.getDate()}</div>
                    <div className="event-month">{d.toLocaleString('default', { month: 'short' })}</div>
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '.875rem' }}>{e.title}</div>
                    <div className="text-xs text-muted mt-8">📍 {e.location || 'TBD'}</div>
                  </div>
                </div>
              )
            }) : <div className="text-muted text-sm" style={{ textAlign: 'center', padding: 24 }}>No upcoming events</div>}
          </div>
        </div>
      </div>

      {/* Attendance */}
      <div className="card mt-24">
        <div className="flex justify-between items-center mb-16">
          <div>
            <div className="card-title">📈 Attendance</div>
            <div className="card-subtitle">
              Rate: <span style={{ color: attOk ? '#00D4AA' : '#FF6B6B', fontWeight: 700 }}>{data.attendance_rate}%</span>
              <span className={`badge ${attOk ? 'badge-success' : 'badge-danger'} ml-8`} style={{ marginLeft: 8 }}>
                {attOk ? '✅ Good' : '⚠️ Below 80%'}
              </span>
            </div>
          </div>
        </div>
        <div className={`progress ${attOk ? 'progress-teal' : 'progress-primary'}`} style={{ height: 12, marginBottom: 8 }}>
          <div className="progress-bar" style={{ width: `${data.attendance_rate}%` }} />
        </div>
        <div className="flex justify-between text-xs text-muted"><span>0%</span><span>Minimum: 80%</span><span>100%</span></div>
      </div>
    </div>
  )
}

// ── Lecturer Dashboard ─────────────────────────────────────────

function LecturerDash() {
  const [data, setData] = useState<LecturerDashboard | null>(null)
  const navigate = useNavigate()
  useEffect(() => { api.get<LecturerDashboard>('/lecturers/dashboard').then(r => setData(r.data)) }, [])
  if (!data) return <div className="flex justify-center items-center" style={{ height: 300 }}><div className="spinner" /></div>

  return (
    <div className="fade-in">
      <div className="hero-banner">
        <div className="hero-badge">👨‍🏫 Lecturer Portal</div>
        <div className="hero-greeting">Welcome back, {data.full_name.split(' ')[0]}! 👋</div>
        <div className="hero-sub">{data.department} · {data.faculty}</div>
        {data.office_location && <div className="text-sm text-muted mt-8">📍 {data.office_location}</div>}
      </div>
      <div className="stat-grid">
        <StatCard icon="📖" value={data.total_courses} label="Courses" color="#8B85FF" bg="rgba(108,99,255,.18)" variant="stat-purple" />
        <StatCard icon="👥" value={data.total_students} label="Students" color="#00D4AA" bg="rgba(0,212,170,.15)" variant="stat-teal" />
        <StatCard icon="📝" value={data.pending_submissions} label="Pending Grading" color="#FF6B6B" bg="rgba(255,107,107,.18)" variant="stat-coral" />
      </div>
      <div className="card">
        <div className="flex justify-between items-center mb-16">
          <div className="card-title">🕐 Recent Submissions</div>
          <button className="btn btn-secondary btn-sm" onClick={() => navigate('/grading')}>Grade All →</button>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Student</th><th>Assignment</th><th>Course</th><th>Submitted</th><th>Status</th></tr></thead>
            <tbody>
              {data.recent_submissions.map((s, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600 }}>{s.student}</td>
                  <td>{s.assignment}</td>
                  <td><span className="badge badge-info">{s.course}</span></td>
                  <td className="text-sm text-muted">{new Date(s.submitted_at).toLocaleDateString()}</td>
                  <td><span className={`badge ${s.graded ? 'badge-success' : 'badge-warning'}`}>{s.graded ? '✅ Graded' : '⏳ Pending'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ── Admin Dashboard ────────────────────────────────────────────

function AdminDash() {
  const [data, setData] = useState<AdminDashboard | null>(null)
  const navigate = useNavigate()
  useEffect(() => { api.get<AdminDashboard>('/admin/dashboard').then(r => setData(r.data)) }, [])
  if (!data) return <div className="flex justify-center items-center" style={{ height: 300 }}><div className="spinner" /></div>

  const roleColor: Record<string, string> = { admin: 'badge-danger', lecturer: 'badge-info', alumni: 'badge-gold', student: 'badge-success' }

  return (
    <div className="fade-in">
      <div className="hero-banner">
        <div className="hero-badge">⚙️ Admin Panel</div>
        <div className="hero-greeting">System Overview 🖥️</div>
        <div className="hero-sub">NSBM EduSphere Administration</div>
      </div>
      <div className="stat-grid">
        <StatCard icon="🎓" value={data.total_students}  label="Students"  color="#8B85FF" bg="rgba(108,99,255,.18)" variant="stat-purple" />
        <StatCard icon="👨‍🏫" value={data.total_lecturers} label="Lecturers" color="#00D4AA" bg="rgba(0,212,170,.15)"  variant="stat-teal"   />
        <StatCard icon="🌐" value={data.total_alumni}    label="Alumni"    color="#FFD700" bg="rgba(255,215,0,.1)"   variant="stat-gold"   />
        <StatCard icon="📖" value={data.total_courses}   label="Courses"   color="#0099FF" bg="rgba(0,153,255,.14)"  variant="stat-blue"   />
        <StatCard icon="📚" value={data.total_books}     label="Books"     color="#FF64C8" bg="rgba(255,100,200,.14)"variant="stat-pink"   />
        <StatCard icon="⚽" value={data.total_clubs}     label="Clubs"     color="#FF6B6B" bg="rgba(255,107,107,.18)"variant="stat-coral"  />
      </div>
      <div className="card">
        <div className="flex justify-between items-center mb-16">
          <div className="card-title">👤 Recent Registrations</div>
          <button className="btn btn-secondary btn-sm" onClick={() => navigate('/manage-users')}>Manage Users →</button>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>#</th><th>Name</th><th>Email</th><th>Role</th><th>Joined</th></tr></thead>
            <tbody>
              {data.recent_registrations.map(u => (
                <tr key={u.id}>
                  <td className="text-muted">#{u.id}</td>
                  <td style={{ fontWeight: 600 }}>{u.full_name}</td>
                  <td className="text-sm text-muted">{u.email}</td>
                  <td><span className={`badge ${roleColor[u.role] || 'badge-info'}`}>{u.role}</span></td>
                  <td className="text-sm text-muted">{new Date(u.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ── Alumni Dashboard ───────────────────────────────────────────

function AlumniDash() {
  const [data, setData] = useState<any>(null)
  const navigate = useNavigate()
  useEffect(() => { api.get('/alumni/dashboard').then(r => setData(r.data)) }, [])
  if (!data) return <div className="flex justify-center items-center" style={{ height: 300 }}><div className="spinner" /></div>

  return (
    <div className="fade-in">
      <div className="hero-banner">
        <div className="hero-badge">🎓 Alumni Portal</div>
        <div className="hero-greeting">Welcome back, {data.full_name.split(' ')[0]}! 🌟</div>
        <div className="hero-sub">{data.degree} · Class of {data.graduation_year}</div>
      </div>
      <div className="stat-grid">
        <StatCard icon="🌐" value={data.total_alumni_network} label="Network" color="#8B85FF" bg="rgba(108,99,255,.18)" variant="stat-purple" />
        <StatCard icon="💬" value={data.my_experiences} label="My Stories" color="#00D4AA" bg="rgba(0,212,170,.15)" variant="stat-teal" />
        <StatCard icon="🤝" value={data.active_mentorships} label="Mentorships" color="#FFD700" bg="rgba(255,215,0,.1)" variant="stat-gold" />
      </div>
      <div className="card">
        <div className="flex justify-between items-center mb-16">
          <div className="card-title">⭐ Featured Stories</div>
          <button className="btn btn-secondary btn-sm" onClick={() => navigate('/experiences')}>View All →</button>
        </div>
        {data.featured_stories.map((e: any) => (
          <div key={e.id} style={{ padding: '14px', background: 'rgba(255,255,255,.03)', border: '1px solid rgba(255,255,255,.06)', borderRadius: 12, marginBottom: 10 }}>
            <div style={{ fontWeight: 700, marginBottom: 6 }}>{e.title}</div>
            <div className="text-xs text-muted">✍️ {e.author} · {e.category} · ❤️ {e.likes}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Main Export ────────────────────────────────────────────────

export default function Dashboard() {
  const { user } = useAuth()
  if (!user) return null
  if (user.role === 'student')  return <StudentDash />
  if (user.role === 'lecturer') return <LecturerDash />
  if (user.role === 'admin')    return <AdminDash />
  if (user.role === 'alumni')   return <AlumniDash />
  return <StudentDash />
}
