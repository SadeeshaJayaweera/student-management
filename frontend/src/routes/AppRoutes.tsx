import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { ProtectedRoute } from './ProtectedRoute'
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
import Timetable from '@/pages/Timetable'
import CalendarTasks from '@/pages/CalendarTasks'
import CollaborationSpaces from '@/pages/CollaborationSpaces'
import Messaging from '@/pages/Messaging'
import Notifications from '@/pages/Notifications'
import { AlumniNetwork, Experiences } from '@/pages/Alumni'

function StubPage({ title, icon, desc }: { title: string; icon: string; desc?: string }) {
  return (
    <div className="fade-in">
      <div className="card" style={{ textAlign: 'center', padding: 64 }}>
        <div style={{ fontSize: '3.5rem', marginBottom: 18 }}>{icon}</div>
        <div style={{ fontFamily: "'Outfit',sans-serif", fontSize: '1.4rem', fontWeight: 800, marginBottom: 8 }}>
          {title}
        </div>
        <div className="text-muted">{desc ?? 'Coming soon — this section is under development.'}</div>
      </div>
    </div>
  )
}

const Grading = () => <StubPage title="Grading Center" icon="✅" desc="Review and grade student submissions." />
const Analytics = () => <StubPage title="Analytics Dashboard" icon="📈" desc="Teaching performance and student insights." />
const Mentorship = () => <StubPage title="Mentorship Program" icon="🤝" desc="Connect with alumni mentors." />
const JobBoard = () => <StubPage title="Job Board" icon="💼" desc="Career opportunities from alumni and partners." />
const ManageUsers = () => <StubPage title="User Management" icon="👥" desc="Manage all system users." />

export const AppRoutes: React.FC = () => {
  const { user } = useAuth()

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/dashboard" /> : <Login />} />

      <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={<Navigate to="/dashboard" />} />
        <Route path="/dashboard" element={<Dashboard />} />

        {/* Student Portals */}
        <Route path="/courses" element={<Courses />} />
        <Route path="/grades" element={<Grades />} />
        <Route path="/assignments" element={<Assignments />} />
        <Route path="/attendance" element={<Attendance />} />
        <Route path="/timetable" element={<Timetable />} />
        <Route path="/calendar" element={<CalendarTasks />} />
        <Route path="/tasks" element={<CalendarTasks />} />
        <Route path="/collaboration" element={<CollaborationSpaces />} />
        <Route path="/messages" element={<Messaging />} />

        {/* Lecturer Portals */}
        <Route path="/grading" element={<Grading />} />
        <Route path="/analytics" element={<Analytics />} />

        {/* Campus Ecosystem */}
        <Route path="/library" element={<Library />} />
        <Route path="/sports" element={<Sports />} />
        <Route path="/news" element={<News />} />
        <Route path="/alumni-network" element={<AlumniNetwork />} />
        <Route path="/experiences" element={<Experiences />} />
        <Route path="/mentorship" element={<Mentorship />} />
        <Route path="/jobs" element={<JobBoard />} />

        {/* AI Assistant */}
        <Route path="/ai-chat" element={<AIChat />} />

        {/* Administration */}
        <Route path="/manage-users" element={<ManageUsers />} />

        {/* User Account */}
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/profile" element={<Profile />} />

        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/dashboard" />} />
      </Route>
    </Routes>
  )
}
