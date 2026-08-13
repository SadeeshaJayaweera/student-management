// Assignments.tsx
import React, { useEffect, useState } from 'react'
import api from '@/api/client'
import toast from 'react-hot-toast'
import type { AssignmentItem } from '@/types'

function SubmitModal({ assignment, onClose, onSubmit }: { assignment: AssignmentItem; onClose: () => void; onSubmit: (text: string) => void }) {
  const [text, setText] = useState('')
  return (
    <div className="modal-backdrop" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.8)', backdropFilter: 'blur(10px)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      <div style={{ background: 'rgba(15,15,30,.97)', border: '1px solid rgba(255,255,255,.14)', borderRadius: 28, padding: 32, width: '100%', maxWidth: 500, position: 'relative' }}>
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: 'linear-gradient(90deg,#6C63FF,#00D4AA)', borderRadius: '28px 28px 0 0' }} />
        <div style={{ fontFamily: "'Outfit',sans-serif", fontSize: '1.3rem', fontWeight: 700, marginBottom: 6 }}>📤 Submit Assignment</div>
        <div className="text-sm text-muted mb-20">{assignment.title}</div>
        <div className="form-group mb-16">
          <label className="form-label">Your Answer / Notes</label>
          <textarea className="form-control" rows={5} placeholder="Type your submission…" value={text} onChange={e => setText(e.target.value)} />
        </div>
        <div className="flex gap-12">
          <button className="btn btn-primary" style={{ flex: 1 }} onClick={() => onSubmit(text)}>Submit</button>
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
        </div>
      </div>
    </div>
  )
}

export default function Assignments() {
  const [assignments, setAssignments] = useState<AssignmentItem[]>([])
  const [loading, setLoading] = useState(true)
  const [modalItem, setModalItem] = useState<AssignmentItem | null>(null)

  useEffect(() => {
    api.get<AssignmentItem[]>('/students/assignments').then(r => setAssignments(r.data)).finally(() => setLoading(false))
  }, [])

  const handleSubmit = async (text: string) => {
    if (!modalItem) return
    try {
      await api.post(`/students/assignments/${modalItem.id}/submit`, { assignment_id: modalItem.id, text_content: text })
      toast.success('✅ Submitted successfully!')
      setModalItem(null)
      api.get<AssignmentItem[]>('/students/assignments').then(r => setAssignments(r.data))
    } catch (e: any) { toast.error(e.response?.data?.detail || 'Error') }
  }

  const pending = assignments.filter(a => !a.is_submitted && !a.is_overdue)
  const overdue = assignments.filter(a => a.is_overdue)
  const submitted = assignments.filter(a => a.is_submitted)

  if (loading) return <div className="flex justify-center items-center" style={{ height: 300 }}><div className="spinner" /></div>

  return (
    <div className="fade-in">
      {modalItem && <SubmitModal assignment={modalItem} onClose={() => setModalItem(null)} onSubmit={handleSubmit} />}
      <div className="page-header">
        <div className="page-title">📝 Assignments</div>
        <div className="page-subtitle">{pending.length} pending · {overdue.length} overdue · {submitted.length} submitted</div>
      </div>
      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(3,1fr)', marginBottom: 24 }}>
        <div className="stat-card stat-coral"><div className="stat-icon" style={{ background: 'rgba(255,107,107,.18)' }}>⏳</div><div><div className="stat-value" style={{ color: '#FF6B6B' }}>{pending.length}</div><div className="stat-label">Pending</div></div></div>
        <div className="stat-card stat-gold"><div className="stat-icon" style={{ background: 'rgba(255,215,0,.1)' }}>⚠️</div><div><div className="stat-value" style={{ color: '#FFD700' }}>{overdue.length}</div><div className="stat-label">Overdue</div></div></div>
        <div className="stat-card stat-teal"><div className="stat-icon" style={{ background: 'rgba(0,212,170,.15)' }}>✅</div><div><div className="stat-value" style={{ color: '#00D4AA' }}>{submitted.length}</div><div className="stat-label">Submitted</div></div></div>
      </div>
      <div className="flex flex-col gap-16">
        {assignments.map(a => {
          const due = new Date(a.due_date)
          const soonDue = !a.is_overdue && !a.is_submitted && due.getTime() - Date.now() < 86400000
          return (
            <div key={a.id} className="card" style={{ borderColor: a.is_overdue ? 'rgba(255,107,107,.3)' : undefined }}>
              <div className="flex justify-between items-start" style={{ flexWrap: 'wrap', gap: 12 }}>
                <div style={{ flex: 1 }}>
                  <div className="flex items-center gap-8 mb-8">
                    <span className={`badge ${a.type === 'quiz' ? 'badge-warning' : a.type === 'project' ? 'badge-info' : 'badge-success'}`}>{a.type}</span>
                    <span style={{ fontWeight: 700, fontSize: '1rem' }}>{a.title}</span>
                  </div>
                  <div className="text-sm text-muted">📖 {a.course} ({a.course_code}) · Max: {a.max_marks} marks</div>
                  <div className="text-sm mt-8" style={{ color: a.is_overdue ? '#FF6B6B' : soonDue ? '#FFB347' : 'rgba(255,255,255,.45)' }}>
                    ⏰ Due: {due.toLocaleString()} {a.is_overdue && '🔴 OVERDUE'}
                  </div>
                  {a.is_submitted && a.submission && (
                    <div className="mt-8" style={{ padding: '8px 12px', background: 'rgba(0,212,170,.07)', border: '1px solid rgba(0,212,170,.2)', borderRadius: 8 }}>
                      <div className="text-sm text-teal font-bold">
                        ✅ Submitted {a.submission.marks != null ? `· Marks: ${a.submission.marks}/${a.max_marks}` : '· Awaiting grade'}
                      </div>
                      {a.submission.feedback && <div className="text-xs text-muted mt-8">💬 {a.submission.feedback}</div>}
                    </div>
                  )}
                </div>
                <div>
                  {!a.is_submitted && !a.is_overdue && (
                    <button className="btn btn-primary btn-sm" onClick={() => setModalItem(a)}>📤 Submit</button>
                  )}
                  {a.is_overdue && !a.is_submitted && <span className="badge badge-danger">Overdue</span>}
                  {a.is_submitted && <span className="badge badge-success">✅ Submitted</span>}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
