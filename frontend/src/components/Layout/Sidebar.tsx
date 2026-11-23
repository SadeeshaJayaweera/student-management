import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

const initials = (name: string) =>
  name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)

interface NavItem { to: string; icon: string; label: string; badge?: string }

function studentNav(): NavItem[] {
  return [
    { to: '/dashboard',    icon: '🏠', label: 'Dashboard' },
    { to: '/courses',      icon: '📖', label: 'My Courses' },
    { to: '/grades',       icon: '📊', label: 'Grades & GPA' },
    { to: '/assignments',  icon: '📝', label: 'Assignments' },
    { to: '/attendance',   icon: '📅', label: 'Attendance' },
    { to: '/timetable',    icon: '⏰', label: 'Timetable' },
    { to: '/evaluations',  icon: '⭐', label: 'Course Feedback' },
    { to: '/wellbeing',    icon: '💚', label: 'Student Wellbeing' },
    { to: '/billing',      icon: '💳', label: 'Fees & Billing' },
    { to: '/calendar',     icon: '📆', label: 'Calendar & Tasks' },
    { to: '/collaboration', icon: '👥', label: 'Study Groups' },
    { to: '/messages',     icon: '💬', label: 'Messages' },
  ]
}

function lecturerNav(): NavItem[] {
  return [
    { to: '/dashboard', icon: '🏠', label: 'Dashboard' },
    { to: '/courses',   icon: '📖', label: 'My Courses' },
    { to: '/ai-quiz-generator', icon: '📝', label: 'Quiz Generator' },
    { to: '/ai-grading',icon: '⚖️', label: 'AI Grading' },
    { to: '/grading',   icon: '✅', label: 'Grading' },
    { to: '/analytics', icon: '📈', label: 'Analytics' },
    { to: '/calendar',  icon: '📆', label: 'Calendar & Tasks' },
    { to: '/messages',  icon: '💬', label: 'Messages' },
  ]
}

function alumniNav(): NavItem[] {
  return [
    { to: '/dashboard',        icon: '🏠',  label: 'Alumni Hub' },
    { to: '/alumni-network',   icon: '🌐',  label: 'Network' },
    { to: '/experiences',      icon: '💬',  label: 'Experiences' },
    { to: '/mentorship',       icon: '🤝',  label: 'Mentorship' },
  ]
}

function adminNav(): NavItem[] {
  return [
    { to: '/dashboard',     icon: '🏠', label: 'Dashboard' },
    { to: '/campus-operations', icon: '🎛️', label: 'Operations Command' },
    { to: '/manage-users',  icon: '👥', label: 'Users' },
    { to: '/manage-courses',icon: '📖', label: 'Courses' },
    { to: '/billing',       icon: '💳', label: 'Fees & Billing' },
  ]
}

export default function Sidebar({ isOpen }: { isOpen: boolean }) {
  const { user, logout } = useAuth()
  if (!user) return null

  const portalNav: Record<string, NavItem[]> = {
    student: studentNav(),
    lecturer: lecturerNav(),
    alumni: alumniNav(),
    admin: adminNav(),
  }

  const campus: NavItem[] = [
    { to: '/library',       icon: '📚', label: 'Library' },
    { to: '/sports',        icon: '⚽', label: 'Sports & Clubs' },
    { to: '/news',          icon: '📰', label: 'News Portal' },
    { to: '/hostels',       icon: '🏢', label: 'Hostel & Housing' },
    { to: '/transport',     icon: '🚌', label: 'Transport & Shuttles' },
    { to: '/facilities',    icon: '🏛️', label: 'Facility Booking' },
    { to: '/alumni-network',icon: '🌐', label: 'Alumni Network' },
  ]

  const account: NavItem[] = [
    { to: '/ai-chat',       icon: '🤖', label: 'AI Assistant', badge: 'AI' },
    { to: '/course-rag',    icon: '📚', label: 'Course RAG', badge: 'RAG' },
    { to: '/ai-tutor',      icon: '🎓', label: 'Socratic Tutor', badge: 'Tutor' },
    { to: '/mcp-console',   icon: '⚙️', label: 'MCP Tools', badge: 'MCP' },
    { to: '/ai-quiz-generator', icon: '📝', label: 'AI Quiz Gen', badge: 'Quiz' },
    { to: '/ai-grading',    icon: '⚖️', label: 'AI Grading', badge: 'Grade' },
    { to: '/notifications', icon: '🔔', label: 'Notifications' },
    { to: '/profile',       icon: '👤', label: 'My Profile' },
  ]

  const roleLabel: Record<string, string> = {
    student: 'Student Portal', lecturer: 'Lecturer Portal',
    alumni: 'Alumni Network', admin: 'Administrator', librarian: 'Librarian',
  }

  return (
    <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
      {/* Profile */}
      <div className="sidebar-profile">
        <div className="avatar avatar-md">{initials(user.full_name)}</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="truncate" style={{ fontWeight: 600, fontSize: '.875rem' }}>{user.full_name}</div>
          <div style={{ fontSize: '.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '.06em' }}>
            {roleLabel[user.role] || user.role}
          </div>
        </div>
      </div>

      {/* Portal Nav */}
      {portalNav[user.role] && (
        <>
          <div className="sidebar-label">Portal</div>
          {portalNav[user.role].map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === '/dashboard'}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <span className="nav-icon">{item.icon}</span>
              {item.label}
              {item.badge && <span className="nav-badge pulse">{item.badge}</span>}
            </NavLink>
          ))}
        </>
      )}

      {/* Campus */}
      <div className="sidebar-label" style={{ marginTop: 16 }}>Campus</div>
      {campus.map((item) => (
        <NavLink key={item.to} to={item.to}
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">{item.icon}</span>
          {item.label}
        </NavLink>
      ))}

      {/* Account */}
      <div className="sidebar-label" style={{ marginTop: 16 }}>Account</div>
      {account.map((item) => (
        <NavLink key={item.to} to={item.to}
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
          <span className="nav-icon">{item.icon}</span>
          {item.label}
          {item.badge && <span className="nav-badge pulse">{item.badge}</span>}
        </NavLink>
      ))}

      {/* System Status */}
      <div style={{ marginTop: 'auto', paddingTop: 16 }}>
        <div style={{
          padding: '12px', background: 'rgba(0,212,170,.06)',
          border: '1px solid rgba(0,212,170,.15)', borderRadius: '12px',
          fontSize: '.68rem', color: 'var(--text-muted)',
        }}>
          <div className="flex items-center gap-8 mb-8">
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#00D4AA', display: 'inline-block' }} className="pulse" />
            <span style={{ color: '#00D4AA', fontWeight: 600 }}>System Online</span>
          </div>
          <div>EduSphere v1.0 · AI: RAG+MCP</div>
        </div>
      </div>
    </aside>
  )
}
