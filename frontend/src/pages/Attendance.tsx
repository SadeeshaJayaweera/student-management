// Attendance.tsx
import React, { useEffect, useState } from 'react'
import api from '@/api/client'
import type { AttendanceRecord } from '@/types'

export default function Attendance() {
  const [records, setRecords] = useState<AttendanceRecord[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get<AttendanceRecord[]>('/students/attendance').then(r => setRecords(r.data)).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex justify-center items-center" style={{ height: 300 }}><div className="spinner" /></div>

  const total = records.length
  const present = records.filter(r => r.status === 'present').length
  const absent = records.filter(r => r.status === 'absent').length
  const late = records.filter(r => r.status === 'late').length
  const rate = total ? Math.round(present / total * 100) : 0
  const attOk = rate >= 80
  const statusCls: Record<string, string> = { present: 'badge-success', absent: 'badge-danger', late: 'badge-warning', excused: 'badge-info' }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-title">📅 Attendance</div>
        <div className="page-subtitle">Track your class attendance across all courses</div>
      </div>

      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(4,1fr)', marginBottom: 24 }}>
        <div className="stat-card stat-teal"><div className="stat-icon" style={{ background: 'rgba(0,212,170,.15)' }}>📊</div><div><div className="stat-value" style={{ color: attOk ? '#00D4AA' : '#FF6B6B' }}>{rate}%</div><div className="stat-label">Rate</div></div></div>
        <div className="stat-card stat-purple"><div className="stat-icon" style={{ background: 'rgba(108,99,255,.18)' }}>📋</div><div><div className="stat-value" style={{ color: '#8B85FF' }}>{total}</div><div className="stat-label">Total</div></div></div>
        <div className="stat-card stat-teal"><div className="stat-icon" style={{ background: 'rgba(0,212,170,.15)' }}>✅</div><div><div className="stat-value" style={{ color: '#00D4AA' }}>{present}</div><div className="stat-label">Present</div></div></div>
        <div className="stat-card stat-coral"><div className="stat-icon" style={{ background: 'rgba(255,107,107,.18)' }}>❌</div><div><div className="stat-value" style={{ color: '#FF6B6B' }}>{absent}</div><div className="stat-label">Absent</div></div></div>
      </div>

      {!attOk && (
        <div className="card mb-24" style={{ borderColor: 'rgba(255,107,107,.35)', background: 'rgba(255,107,107,.05)' }}>
          ⚠️ <strong>Warning:</strong> Your attendance is below 80%. You may not be eligible to sit for final exams.
        </div>
      )}

      <div className="card" style={{ marginBottom: 24 }}>
        <div className="flex justify-between mb-8 text-sm">
          <span className="text-muted">Attendance Progress</span>
          <span style={{ color: attOk ? '#00D4AA' : '#FF6B6B', fontWeight: 700 }}>{rate}% / Minimum 80%</span>
        </div>
        <div className={`progress ${attOk ? 'progress-teal' : 'progress-primary'}`} style={{ height: 12 }}>
          <div className="progress-bar" style={{ width: `${rate}%` }} />
        </div>
      </div>

      <div className="card">
        <div className="card-title mb-16">Attendance Log</div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Course</th><th>Date</th><th>Status</th></tr></thead>
            <tbody>
              {[...records].reverse().map(r => (
                <tr key={r.id}>
                  <td>
                    <span style={{ fontWeight: 600 }}>{r.course}</span><br />
                    <span className="text-xs text-muted">{r.course_code}</span>
                  </td>
                  <td className="text-sm">{new Date(r.date).toLocaleDateString('default', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' })}</td>
                  <td><span className={`badge ${statusCls[r.status] || 'badge-info'}`}>{r.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
