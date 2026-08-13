// Courses.tsx — Works for students AND lecturers
import React, { useEffect, useState } from 'react'
import api from '@/api/client'
import { useAuth } from '@/contexts/AuthContext'
import type { CourseEnrollment } from '@/types'

const COLORS = ['#6C63FF', '#00D4AA', '#FF6B6B', '#FFB347', '#FF64C8', '#0099FF', '#9B59B6']

export default function Courses() {
  const { user } = useAuth()
  const [courses, setCourses] = useState<CourseEnrollment[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const url = user?.role === 'lecturer' ? '/lecturers/courses' : '/students/courses'
    api.get<CourseEnrollment[]>(url).then(r => setCourses(r.data)).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center items-center" style={{ height: 300 }}><div className="spinner" /></div>

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-title">📖 My Courses</div>
        <div className="page-subtitle">{courses.length} courses this semester</div>
      </div>
      <div className="grid-auto">
        {courses.map((c, i) => {
          const color = COLORS[c.id % COLORS.length]
          return (
            <div key={c.id} className="card" style={{ borderColor: `${color}33`, transition: 'var(--spring)' }}>
              <div className="flex items-center gap-12 mb-16">
                <div style={{ width: 44, height: 44, borderRadius: 12, background: `${color}22`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.1rem', color, fontWeight: 800, flexShrink: 0 }}>
                  {c.course_code.slice(0, 2)}
                </div>
                <div>
                  <div style={{ fontWeight: 700 }}>{c.title}</div>
                  <div className="text-xs text-muted">{c.course_code} · {c.credits} credits</div>
                </div>
              </div>
              {c.description && <div className="text-sm text-secondary mb-12" style={{ lineHeight: 1.5 }}>{c.description.slice(0, 100)}…</div>}
              {c.schedule && (
                <div className="text-sm text-muted mb-8">⏰ {c.schedule.day} {c.schedule.time} · 📍 {c.schedule.room}</div>
              )}
              {c.lecturer && <div className="text-sm text-muted">👨‍🏫 {c.lecturer}</div>}
              {c.enrolled_count !== undefined && (
                <div className="text-sm text-muted mt-8">👥 {c.enrolled_count}/{c.max_students} students</div>
              )}
              <span className="badge badge-success mt-8">Active</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
