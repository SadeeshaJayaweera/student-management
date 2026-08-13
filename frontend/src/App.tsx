import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'

import Layout from '@/components/Layout/Layout'
import Login from '@/pages/Login'
import Dashboard from '@/pages/Dashboard'
import Grades from '@/pages/Grades'
import Library from '@/pages/Library'
import Sports from '@/pages/Sports'
import News from '@/pages/News'
import AIChat from '@/pages/AIChat'
import Assignments from '@/pages/Assignments'
import Attendance from '@/pages/Attendance'
import Courses from '@/pages/Courses'
import Profile from '@/pages/Profile'
import { AlumniNetwork, Experiences } from '@/pages/Alumni'

// ── Lazy / Stub Pages ─────────────────────────────────────────

function StubPage({ title, icon, desc }: { title: string; icon: string; desc?: string }) {
  return (
    <div className="fade-in">
      <div className="card" style={{ textAlign: 'center', padding: 64 }}>
        <div style={{ fontSize: '3.5rem', marginBottom: 18 }}>{icon}</div>
        <div style={{ fontFamily: "'Outfit',sans-serif", fontSize: '1.4rem', fontWeight: 800, marginBottom: 8 }}>{title}</div>
        <div className="text-muted">{desc ?? 'Coming soon — this section is under development.'}</div>
      </div>
    </div>
  )
}

const Timetable    = () => <StubPage title="Weekly Timetable" icon="⏰" desc="View your class schedule for this semester." />
const Grading      = () => <StubPage title="Grading Center" icon="✅" desc="Review and grade student submissions." />
const Analytics    = () => <StubPage title="Analytics Dashboard" icon="📈" desc="Teaching performance and student insights." />
const Notifications= () => <StubPage title="Notifications" icon="🔔" desc="Stay up to date with campus announcements." />
const Mentorship   = () => <StubPage title="Mentorship Program" icon="🤝" desc="Connect with alumni mentors." />
const JobBoard     = () => <StubPage title="Job Board" icon="💼" desc="Career opportunities from alumni and partners." />
const ManageUsers  = () => <StubPage title="User Management" icon="👥" desc="Manage all system users." />

// ── Protected Route ───────────────────────────────────────────

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', flexDirection: 'column', gap: 16 }}>
        <div style={{ fontSize: '2.5rem' }}>🎓</div>
        <div className="spinner" />
        <div className="text-muted text-sm">Loading EduSphere…</div>
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

// ── Router ─────────────────────────────────────────────────────

function AppRoutes() {
  const { user } = useAuth()

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/dashboard" /> : <Login />} />

      <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={<Navigate to="/dashboard" />} />
        <Route path="/dashboard"     element={<Dashboard />} />

        {/* Student */}
        <Route path="/courses"       element={<Courses />} />
        <Route path="/grades"        element={<Grades />} />
        <Route path="/assignments"   element={<Assignments />} />
        <Route path="/attendance"    element={<Attendance />} />
        <Route path="/timetable"     element={<Timetable />} />

        {/* Lecturer */}
        <Route path="/grading"       element={<Grading />} />
        <Route path="/analytics"     element={<Analytics />} />

        {/* Campus Portals */}
        <Route path="/library"         element={<Library />} />
        <Route path="/sports"          element={<Sports />} />
        <Route path="/news"            element={<News />} />
        <Route path="/alumni-network"  element={<AlumniNetwork />} />
        <Route path="/experiences"     element={<Experiences />} />
        <Route path="/mentorship"      element={<Mentorship />} />
        <Route path="/jobs"            element={<JobBoard />} />

        {/* AI */}
        <Route path="/ai-chat"       element={<AIChat />} />

        {/* Admin */}
        <Route path="/manage-users"  element={<ManageUsers />} />

        {/* Account */}
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/profile"       element={<Profile />} />

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/dashboard" />} />
      </Route>
    </Routes>
  )
}

// ── App ───────────────────────────────────────────────────────

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
        <Toaster
          position="bottom-right"
          toastOptions={{
            style: {
              background: 'rgba(15,15,30,.97)',
              color: '#fff',
              border: '1px solid rgba(255,255,255,.14)',
              borderRadius: '14px',
              fontFamily: "'Inter',sans-serif",
              fontSize: '.875rem',
            },
            success: { iconTheme: { primary: '#00D4AA', secondary: '#fff' } },
            error:   { iconTheme: { primary: '#FF6B6B', secondary: '#fff' } },
          }}
        />
      </AuthProvider>
    </BrowserRouter>
  )
}
