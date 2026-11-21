import React, { useEffect, useState } from 'react'
import api from '@/api/client'
import { useAuth } from '@/contexts/AuthContext'
import type { AttendanceRecord, AttendanceCorrectionRequest } from '@/types'
import toast from 'react-hot-toast'

export default function Attendance() {
  const { user } = useAuth()
  const [records, setRecords] = useState<AttendanceRecord[]>([])
  const [corrections, setCorrections] = useState<AttendanceCorrectionRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [pinCode, setPinCode] = useState('')
  const [checkingIn, setCheckingIn] = useState(false)
  const [showExcuseModal, setShowExcuseModal] = useState(false)
  const [excuseData, setExcuseData] = useState({
    course_id: '',
    attendance_date: new Date().toISOString().split('T')[0],
    requested_status: 'excused',
    reason: '',
    supporting_document_url: '',
  })

  const loadData = async () => {
    try {
      setLoading(true)
      const [attRes, corrRes] = await Promise.all([
        api.get<AttendanceRecord[]>('/students/attendance'),
        api.get<AttendanceCorrectionRequest[]>('/attendance/corrections'),
      ])
      setRecords(attRes.data || [])
      setCorrections(corrRes.data || [])
    } catch {
      toast.error('Failed to load attendance records')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleSelfCheckin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!pinCode.trim()) return
    try {
      setCheckingIn(true)
      // Call checkin endpoint with a target session ID or find open session
      const res = await api.post(`/attendance/sessions/1/checkin`, { checkin_code: pinCode.trim() })
      toast.success(res.data.message || 'Check-in verified successfully!')
      setPinCode('')
      loadData()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Invalid or expired check-in code')
    } finally {
      setCheckingIn(false)
    }
  }

  const handleSubmitExcuse = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/attendance/corrections', {
        course_id: parseInt(excuseData.course_id),
        attendance_date: excuseData.attendance_date,
        requested_status: excuseData.requested_status,
        reason: excuseData.reason,
        supporting_document_url: excuseData.supporting_document_url || null,
      })
      toast.success('Absence excuse submitted for review')
      setShowExcuseModal(false)
      setExcuseData({
        course_id: '',
        attendance_date: new Date().toISOString().split('T')[0],
        requested_status: 'excused',
        reason: '',
        supporting_document_url: '',
      })
      loadData()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to submit excuse request')
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center" style={{ height: 300 }}>
        <div className="spinner" />
      </div>
    )
  }

  const total = records.length
  const present = records.filter((r) => r.status === 'present').length
  const absent = records.filter((r) => r.status === 'absent').length
  const late = records.filter((r) => r.status === 'late').length
  const excused = records.filter((r) => r.status === 'excused').length
  const rate = total ? Math.round(((present + late * 0.5 + excused) / total) * 100) : 100
  const attOk = rate >= 80
  const statusCls: Record<string, string> = {
    present: 'badge-success',
    absent: 'badge-danger',
    late: 'badge-warning',
    excused: 'badge-info',
  }

  return (
    <div className="fade-in">
      <div className="flex justify-between items-center mb-24 flex-wrap gap-12">
        <div>
          <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 800 }}>📅 Attendance & Participation</h1>
          <p className="text-muted text-sm" style={{ marginTop: 4 }}>
            Institutional 80% threshold tracking, live lecture PIN check-in, and absence excuse appeals
          </p>
        </div>
        <div className="flex items-center gap-12">
          {user?.role === 'student' && (
            <button className="btn btn-secondary btn-sm" onClick={() => setShowExcuseModal(true)}>
              📝 Submit Excuse / Appeal
            </button>
          )}
        </div>
      </div>

      {/* Self Check-in Banner */}
      {user?.role === 'student' && (
        <div className="card mb-24" style={{ background: 'linear-gradient(135deg, rgba(79,70,229,.12), rgba(124,58,237,.12))' }}>
          <div className="flex justify-between items-center flex-wrap gap-16">
            <div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', marginBottom: 4 }}>⚡ Live Class Check-in</div>
              <div className="text-xs text-muted">
                In class right now? Enter the 6-digit PIN code displayed by your lecturer to record your presence and participation.
              </div>
            </div>
            <form onSubmit={handleSelfCheckin} className="flex items-center gap-8">
              <input
                type="text"
                placeholder="6-Digit PIN"
                maxLength={6}
                value={pinCode}
                onChange={(e) => setPinCode(e.target.value)}
                className="input"
                style={{ width: 140, textAlign: 'center', letterSpacing: 4, fontWeight: 700 }}
              />
              <button type="submit" className="btn btn-primary" disabled={checkingIn || pinCode.length < 4}>
                {checkingIn ? 'Checking in...' : 'Check In'}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(4,1fr)', marginBottom: 24 }}>
        <div className="stat-card stat-teal">
          <div className="stat-icon" style={{ background: 'rgba(0,212,170,.15)' }}>📊</div>
          <div>
            <div className="stat-value" style={{ color: attOk ? '#00D4AA' : '#FF6B6B' }}>
              {rate}%
            </div>
            <div className="stat-label">Weighted Rate</div>
          </div>
        </div>
        <div className="stat-card stat-purple">
          <div className="stat-icon" style={{ background: 'rgba(108,99,255,.18)' }}>📋</div>
          <div>
            <div className="stat-value" style={{ color: '#8B85FF' }}>{total}</div>
            <div className="stat-label">Total Sessions</div>
          </div>
        </div>
        <div className="stat-card stat-teal">
          <div className="stat-icon" style={{ background: 'rgba(0,212,170,.15)' }}>✅</div>
          <div>
            <div className="stat-value" style={{ color: '#00D4AA' }}>{present + excused}</div>
            <div className="stat-label">Attended / Excused</div>
          </div>
        </div>
        <div className="stat-card stat-coral">
          <div className="stat-icon" style={{ background: 'rgba(255,107,107,.18)' }}>❌</div>
          <div>
            <div className="stat-value" style={{ color: '#FF6B6B' }}>{absent}</div>
            <div className="stat-label">Absences</div>
          </div>
        </div>
      </div>

      {!attOk && (
        <div className="card mb-24" style={{ borderColor: 'rgba(255,107,107,.35)', background: 'rgba(255,107,107,.05)' }}>
          ⚠️ <strong>Academic Policy Warning:</strong> Your overall attendance is currently {rate}%, which falls below the mandatory 80% institutional threshold required to sit for final semester examinations. Please submit medical/official duty excuses or contact your academic advisor.
        </div>
      )}

      <div className="card" style={{ marginBottom: 24 }}>
        <div className="flex justify-between mb-8 text-sm">
          <span className="text-muted">Institutional Policy Threshold (80% Minimum)</span>
          <span style={{ color: attOk ? '#00D4AA' : '#FF6B6B', fontWeight: 700 }}>
            {rate}% / Minimum 80%
          </span>
        </div>
        <div className={`progress ${attOk ? 'progress-teal' : 'progress-primary'}`} style={{ height: 12 }}>
          <div className="progress-bar" style={{ width: `${Math.min(100, rate)}%` }} />
        </div>
      </div>

      {/* Submitted Excuses / Corrections */}
      {corrections.length > 0 && (
        <div className="card mb-24">
          <div className="card-title mb-16">📋 Absence Excuse Requests</div>
          <div className="flex flex-col gap-10">
            {corrections.map((corr) => (
              <div
                key={corr.id}
                className="flex justify-between items-center"
                style={{
                  padding: '12px 16px',
                  background: 'rgba(255,255,255,0.02)',
                  borderRadius: 8,
                  border: '1px solid rgba(255,255,255,0.05)',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: '.9rem' }}>
                    {corr.course_code}: {corr.reason}
                  </div>
                  <div className="text-xs text-muted" style={{ marginTop: 2 }}>
                    Date: {new Date(corr.attendance_date).toLocaleDateString()} · Requested: {corr.requested_status.toUpperCase()}
                    {corr.review_comment && <span> · Feedback: "{corr.review_comment}"</span>}
                  </div>
                </div>
                <span
                  className={`badge ${
                    corr.status === 'approved'
                      ? 'badge-success'
                      : corr.status === 'rejected'
                      ? 'badge-danger'
                      : 'badge-warning'
                  }`}
                >
                  {corr.status.toUpperCase()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Attendance Log Table */}
      <div className="card">
        <div className="card-title mb-16">Attendance History & Participation Log</div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Course</th>
                <th>Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {records.length > 0 ? (
                [...records].reverse().map((r) => (
                  <tr key={r.id}>
                    <td>
                      <span style={{ fontWeight: 600 }}>{r.course}</span>
                      <br />
                      <span className="text-xs text-muted">{r.course_code}</span>
                    </td>
                    <td className="text-sm">
                      {new Date(r.date).toLocaleDateString('default', {
                        weekday: 'short',
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </td>
                    <td>
                      <span className={`badge ${statusCls[r.status] || 'badge-info'}`}>
                        {r.status.toUpperCase()}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={3} className="text-center text-muted" style={{ padding: 24 }}>
                    No recorded attendance logs yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Submit Excuse Modal */}
      {showExcuseModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 16,
          }}
        >
          <div className="card" style={{ maxWidth: 480, width: '100%' }}>
            <div className="flex justify-between items-center mb-16">
              <div style={{ fontWeight: 700, fontSize: '1.2rem' }}>Submit Absence Excuse / Appeal</div>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowExcuseModal(false)}>✕</button>
            </div>
            <form onSubmit={handleSubmitExcuse} className="flex flex-col gap-12">
              <div>
                <label className="text-xs text-muted block mb-4">Course ID</label>
                <input
                  type="number"
                  required
                  placeholder="e.g. 1"
                  className="input w-full"
                  value={excuseData.course_id}
                  onChange={(e) => setExcuseData({ ...excuseData, course_id: e.target.value })}
                />
              </div>

              <div>
                <label className="text-xs text-muted block mb-4">Absence Date</label>
                <input
                  type="date"
                  required
                  className="input w-full"
                  value={excuseData.attendance_date}
                  onChange={(e) => setExcuseData({ ...excuseData, attendance_date: e.target.value })}
                />
              </div>

              <div>
                <label className="text-xs text-muted block mb-4">Excuse Reason / Justification</label>
                <textarea
                  required
                  rows={3}
                  placeholder="Describe your medical leave or official university representation..."
                  className="input w-full"
                  value={excuseData.reason}
                  onChange={(e) => setExcuseData({ ...excuseData, reason: e.target.value })}
                />
              </div>

              <div>
                <label className="text-xs text-muted block mb-4">Supporting Document URL (Medical certificate / Duty letter)</label>
                <input
                  type="url"
                  placeholder="https://..."
                  className="input w-full"
                  value={excuseData.supporting_document_url}
                  onChange={(e) => setExcuseData({ ...excuseData, supporting_document_url: e.target.value })}
                />
              </div>

              <div className="flex justify-end gap-12 mt-16">
                <button type="button" className="btn btn-ghost" onClick={() => setShowExcuseModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Submit Excuse
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
