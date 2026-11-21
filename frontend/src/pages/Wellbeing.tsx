import React, { useEffect, useState } from 'react'
import api from '@/api/client'
import { useAuth } from '@/contexts/AuthContext'
import {
  WellbeingSupportRequestItem,
  WellbeingResourceItem,
  WellbeingAppointmentItem,
} from '@/types'
import toast from 'react-hot-toast'

export default function Wellbeing() {
  const { user } = useAuth()
  const isCounselor = user?.role === 'admin' || user?.role === 'lecturer'

  // Data states
  const [myRequests, setMyRequests] = useState<WellbeingSupportRequestItem[]>([])
  const [triageQueue, setTriageQueue] = useState<WellbeingSupportRequestItem[]>([])
  const [resources, setResources] = useState<WellbeingResourceItem[]>([])
  const [loading, setLoading] = useState<boolean>(true)

  // Active sub-tab
  const [activeTab, setActiveTab] = useState<'requests' | 'resources'>('requests')

  // Student New Request Modal
  const [showRequestModal, setShowRequestModal] = useState<boolean>(false)
  const [reqType, setReqType] = useState<string>('counseling')
  const [reqSubject, setReqSubject] = useState<string>('')
  const [reqDescription, setReqDescription] = useState<string>('')
  const [reqUrgency, setReqUrgency] = useState<string>('normal')
  const [submittingReq, setSubmittingReq] = useState<boolean>(false)

  // Counselor Schedule Modal
  const [selectedReqForAppt, setSelectedReqForAppt] = useState<WellbeingSupportRequestItem | null>(null)
  const [apptScheduledAt, setApptScheduledAt] = useState<string>('')
  const [apptDuration, setApptDuration] = useState<number>(45)
  const [apptType, setApptType] = useState<'virtual' | 'in_person'>('virtual')
  const [apptLocation, setApptLocation] = useState<string>('')
  const [apptNotes, setApptNotes] = useState<string>('')
  const [schedulingAppt, setSchedulingAppt] = useState<boolean>(false)

  // Staff New Resource Modal
  const [showResourceModal, setShowResourceModal] = useState<boolean>(false)
  const [resTitle, setResTitle] = useState<string>('')
  const [resCat, setResCat] = useState<string>('mental_health')
  const [resDesc, setResDesc] = useState<string>('')
  const [resUrl, setResUrl] = useState<string>('')
  const [resPhone, setResPhone] = useState<string>('')
  const [resIsCrisis, setResIsCrisis] = useState<boolean>(false)
  const [creatingRes, setCreatingRes] = useState<boolean>(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const resPromise = api.get<WellbeingResourceItem[]>('/wellbeing/resources')
      const reqPromise = isCounselor
        ? api.get<WellbeingSupportRequestItem[]>('/wellbeing/counselor/requests')
        : api.get<WellbeingSupportRequestItem[]>('/wellbeing/requests/my')

      const [resourcesRes, requestsRes] = await Promise.all([resPromise, reqPromise])
      setResources(resourcesRes.data)
      if (isCounselor) {
        setTriageQueue(requestsRes.data)
      } else {
        setMyRequests(requestsRes.data)
      }
    } catch (err: any) {
      console.error('Failed to load wellbeing data:', err)
      toast.error('Failed to load wellbeing information.')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmitRequest = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!reqSubject.trim() || !reqDescription.trim() || submittingReq) return

    try {
      setSubmittingReq(true)
      const payload = {
        request_type: reqType,
        subject: reqSubject.trim(),
        description: reqDescription.trim(),
        urgency: reqUrgency,
        is_confidential: true,
      }
      await api.post('/wellbeing/requests', payload)
      toast.success('Your confidential support request has been submitted. A counselor will follow up.')
      setShowRequestModal(false)
      setReqSubject('')
      setReqDescription('')
      setReqUrgency('normal')
      loadData()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to submit request.')
    } finally {
      setSubmittingReq(false)
    }
  }

  const handleScheduleAppointment = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedReqForAppt || !apptScheduledAt || schedulingAppt) return

    try {
      setSchedulingAppt(true)
      const payload = {
        scheduled_at: new Date(apptScheduledAt).toISOString(),
        duration_minutes: apptDuration,
        appointment_type: apptType,
        location_or_link: apptLocation.trim() || undefined,
        meeting_notes: apptNotes.trim() || undefined,
      }
      await api.post(`/wellbeing/requests/${selectedReqForAppt.id}/appointments`, payload)
      toast.success('Counseling session scheduled successfully!')
      setSelectedReqForAppt(null)
      setApptScheduledAt('')
      setApptLocation('')
      setApptNotes('')
      loadData()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to schedule appointment.')
    } finally {
      setSchedulingAppt(false)
    }
  }

  const handleUpdateStatus = async (requestId: number, newStatus: string) => {
    try {
      await api.put(`/wellbeing/requests/${requestId}/status`, {
        status: newStatus,
      })
      toast.success(`Request marked as ${newStatus}.`)
      loadData()
    } catch (err: any) {
      toast.error('Failed to update status.')
    }
  }

  const handleCreateResource = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!resTitle.trim() || !resDesc.trim() || creatingRes) return

    try {
      setCreatingRes(true)
      const payload = {
        title: resTitle.trim(),
        category: resCat,
        description: resDesc.trim(),
        content_url: resUrl.trim() || undefined,
        emergency_phone: resPhone.trim() || undefined,
        is_crisis_resource: resIsCrisis,
        is_featured: true,
      }
      await api.post('/wellbeing/resources', payload)
      toast.success('Wellbeing resource added to directory!')
      setShowResourceModal(false)
      setResTitle('')
      setResDesc('')
      setResUrl('')
      setResPhone('')
      loadData()
    } catch (err: any) {
      toast.error('Failed to create resource.')
    } finally {
      setCreatingRes(false)
    }
  }

  const getUrgencyBadge = (urgency: string) => {
    switch (urgency) {
      case 'crisis':
        return { label: '🚨 CRISIS', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)' }
      case 'high':
        return { label: '⚠️ HIGH', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', border: '1px solid rgba(245, 158, 11, 0.3)' }
      default:
        return { label: 'NORMAL', color: '#60a5fa', bg: 'rgba(59, 130, 246, 0.12)', border: '1px solid rgba(59, 130, 246, 0.25)' }
    }
  }

  return (
    <div className="fade-in" style={{ maxWidth: 1200, margin: '0 auto', paddingBottom: 40 }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.85rem', fontWeight: 800, fontFamily: "'Outfit', sans-serif" }}>
            Student Wellbeing & Mental Health Support
          </h1>
          <p className="text-muted" style={{ margin: '4px 0 0 0', fontSize: '0.92rem' }}>
            Safe, confidential mental health counseling, stress relief support, and campus wellness care.
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {isCounselor && (
            <button
              onClick={() => setShowResourceModal(true)}
              className="btn btn-secondary"
              style={{ display: 'flex', alignItems: 'center', gap: 6 }}
            >
              <span>➕</span> Add Resource
            </button>
          )}
          <button
            onClick={() => setShowRequestModal(true)}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: 8 }}
          >
            <span>💬</span> Request Confidential Support
          </button>
        </div>
      </div>

      {/* 24/7 Crisis Hotline Alert Banner */}
      <div
        className="card"
        style={{
          background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(185, 28, 28, 0.15))',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          marginBottom: 24,
          padding: '16px 20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 16,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ fontSize: '2.4rem' }}>🆘</div>
          <div>
            <h4 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800, color: '#f87171' }}>
              Are you or someone you know in crisis? Immediate Support is Available 24/7
            </h4>
            <p className="text-muted" style={{ margin: '4px 0 0 0', fontSize: '0.88rem' }}>
              National Mental Health Helpline: <strong>1926</strong> • Sumithrayo Crisis Line: <strong>+94 11 269 2909</strong> • Campus Security Emergency: <strong>011 544 5000</strong>
            </p>
          </div>
        </div>
        <div>
          <a
            href="tel:1926"
            className="btn"
            style={{
              backgroundColor: '#ef4444',
              color: '#fff',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <span>📞</span> Call 1926 (Free & 24/7)
          </a>
        </div>
      </div>

      {/* Sub Tabs */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        <button
          onClick={() => setActiveTab('requests')}
          className={`btn ${activeTab === 'requests' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ borderRadius: 20, padding: '8px 20px', fontSize: '0.9rem' }}
        >
          {isCounselor ? 'Triage Support Cases' : 'My Support Requests & Appointments'}
        </button>
        <button
          onClick={() => setActiveTab('resources')}
          className={`btn ${activeTab === 'resources' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ borderRadius: 20, padding: '8px 20px', fontSize: '0.9rem' }}
        >
          Self-Help & Wellness Directory
        </button>
      </div>

      {/* Tab 1: Requests & Appointments */}
      {activeTab === 'requests' && (
        <div>
          {isCounselor ? (
            /* Counselor Triage View */
            <div className="card" style={{ padding: 20 }}>
              <h3 style={{ margin: '0 0 16px 0', fontSize: '1.2rem', fontWeight: 700 }}>
                Counseling Triage & Case Management
              </h3>

              {loading ? (
                <div style={{ padding: 32, textAlign: 'center' }} className="text-muted">Loading cases...</div>
              ) : triageQueue.length === 0 ? (
                <div style={{ padding: 32, textAlign: 'center' }} className="text-muted">
                  No pending student support cases.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  {triageQueue.map((req) => {
                    const uStyle = getUrgencyBadge(req.urgency)
                    return (
                      <div
                        key={req.id}
                        style={{
                          border: '1px solid var(--border-color)',
                          borderRadius: 12,
                          padding: 18,
                          backgroundColor: 'rgba(255, 255, 255, 0.02)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: 12,
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span
                              style={{
                                fontSize: '0.72rem',
                                fontWeight: 800,
                                padding: '2px 8px',
                                borderRadius: 6,
                                backgroundColor: uStyle.bg,
                                color: uStyle.color,
                                border: uStyle.border,
                              }}
                            >
                              {uStyle.label}
                            </span>
                            <span
                              style={{
                                fontSize: '0.72rem',
                                textTransform: 'uppercase',
                                padding: '2px 6px',
                                borderRadius: 4,
                                backgroundColor: 'rgba(255, 255, 255, 0.08)',
                                color: '#94a3b8',
                                fontWeight: 600,
                              }}
                            >
                              {req.request_type.replace('_', ' ')}
                            </span>
                            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#60a5fa' }}>
                              Status: {req.status.toUpperCase()}
                            </span>
                          </div>
                          <span className="text-muted" style={{ fontSize: '0.78rem' }}>
                            {new Date(req.created_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>

                        <div>
                          <h4 style={{ margin: '0 0 6px 0', fontSize: '1.05rem', fontWeight: 700 }}>
                            {req.subject}
                          </h4>
                          <p className="text-muted" style={{ margin: 0, fontSize: '0.9rem', lineHeight: 1.45 }}>
                            {req.description}
                          </p>
                        </div>

                        <div className="text-muted" style={{ fontSize: '0.82rem' }}>
                          Student: {req.student_name || 'Confidential Student'} ({req.student_number || 'ID hidden'})
                        </div>

                        {/* Scheduled Appointments List if any */}
                        {req.appointments && req.appointments.length > 0 && (
                          <div style={{ backgroundColor: 'rgba(59, 130, 246, 0.08)', padding: 10, borderRadius: 8 }}>
                            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#60a5fa' }}>
                              Scheduled Session:
                            </span>{' '}
                            <span style={{ fontSize: '0.82rem' }}>
                              {new Date(req.appointments[0].scheduled_at).toLocaleString()} ({req.appointments[0].appointment_type}) — {req.appointments[0].location_or_link || 'Virtual Link Pending'}
                            </span>
                          </div>
                        )}

                        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', borderTop: '1px solid rgba(255, 255, 255, 0.05)', paddingTop: 10 }}>
                          <button
                            onClick={() => setSelectedReqForAppt(req)}
                            className="btn btn-primary"
                            style={{ fontSize: '0.82rem', padding: '5px 12px' }}
                          >
                            📅 Schedule Session
                          </button>
                          {req.status !== 'resolved' && (
                            <button
                              onClick={() => handleUpdateStatus(req.id, 'resolved')}
                              className="btn btn-secondary"
                              style={{ fontSize: '0.82rem', padding: '5px 12px', color: '#34d399' }}
                            >
                              ✓ Mark Resolved
                            </button>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          ) : (
            /* Student My Requests View */
            <div className="card" style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700 }}>
                  Your Support Tickets & Appointments
                </h3>
                <button
                  onClick={() => setShowRequestModal(true)}
                  className="btn btn-primary"
                  style={{ fontSize: '0.85rem' }}
                >
                  + New Request
                </button>
              </div>

              {loading ? (
                <div style={{ padding: 32, textAlign: 'center' }} className="text-muted">Loading your tickets...</div>
              ) : myRequests.length === 0 ? (
                <div style={{ padding: 36, textAlign: 'center' }}>
                  <div style={{ fontSize: '2.5rem', marginBottom: 10 }}>🌱</div>
                  <h4 style={{ margin: 0, fontWeight: 700 }}>No Active Support Requests</h4>
                  <p className="text-muted" style={{ margin: '6px 0 16px 0', fontSize: '0.88rem' }}>
                    If you are experiencing academic burnout, anxiety, personal distress, or accessibility needs, our campus team is here to help.
                  </p>
                  <button onClick={() => setShowRequestModal(true)} className="btn btn-primary">
                    Reach Out for Support
                  </button>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  {myRequests.map((req) => (
                    <div
                      key={req.id}
                      style={{
                        border: '1px solid var(--border-color)',
                        borderRadius: 12,
                        padding: 16,
                        backgroundColor: 'rgba(255, 255, 255, 0.02)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                          <span
                            style={{
                              fontSize: '0.75rem',
                              fontWeight: 700,
                              padding: '2px 8px',
                              borderRadius: 6,
                              backgroundColor: req.status === 'resolved' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(59, 130, 246, 0.15)',
                              color: req.status === 'resolved' ? '#34d399' : '#60a5fa',
                            }}
                          >
                            {req.status.toUpperCase()}
                          </span>
                          <span className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase' }}>
                            {req.request_type.replace('_', ' ')}
                          </span>
                        </div>
                        <span className="text-muted" style={{ fontSize: '0.78rem' }}>
                          Submitted: {new Date(req.created_at).toLocaleDateString()}
                        </span>
                      </div>

                      <h4 style={{ margin: '4px 0 6px 0', fontSize: '1rem', fontWeight: 700 }}>
                        {req.subject}
                      </h4>
                      <p className="text-muted" style={{ margin: 0, fontSize: '0.88rem', lineHeight: 1.45 }}>
                        {req.description}
                      </p>

                      {/* Scheduled Appointment Card */}
                      {req.appointments && req.appointments.length > 0 && (
                        <div
                          style={{
                            marginTop: 12,
                            padding: '10px 14px',
                            borderRadius: 8,
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            border: '1px solid rgba(16, 185, 129, 0.25)',
                          }}
                        >
                          <div style={{ fontWeight: 700, fontSize: '0.84rem', color: '#34d399', marginBottom: 2 }}>
                            🗓 Confirmed Counseling Session
                          </div>
                          <div style={{ fontSize: '0.84rem' }}>
                            Date & Time: {new Date(req.appointments[0].scheduled_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
                          </div>
                          {req.appointments[0].location_or_link && (
                            <div style={{ fontSize: '0.84rem', marginTop: 2 }}>
                              Location/Link: <strong>{req.appointments[0].location_or_link}</strong>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Wellness Directory */}
      {activeTab === 'resources' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16 }}>
          {resources.map((res) => (
            <div
              key={res.id}
              className="card"
              style={{
                padding: 20,
                border: res.is_crisis_resource ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid var(--border-color)',
                backgroundColor: res.is_crisis_resource ? 'rgba(239, 68, 68, 0.05)' : 'rgba(255, 255, 255, 0.02)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span
                  style={{
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    padding: '2px 8px',
                    borderRadius: 6,
                    backgroundColor: res.is_crisis_resource ? 'rgba(239, 68, 68, 0.15)' : 'rgba(59, 130, 246, 0.15)',
                    color: res.is_crisis_resource ? '#ef4444' : '#60a5fa',
                  }}
                >
                  {res.category.replace('_', ' ')}
                </span>
                {res.emergency_phone && (
                  <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#f87171' }}>
                    📞 {res.emergency_phone}
                  </span>
                )}
              </div>

              <h4 style={{ margin: '0 0 6px 0', fontSize: '1.05rem', fontWeight: 700 }}>
                {res.title}
              </h4>
              <p className="text-muted" style={{ margin: '0 0 14px 0', fontSize: '0.88rem', lineHeight: 1.45 }}>
                {res.description}
              </p>

              {res.content_url && (
                <a
                  href={res.content_url}
                  target="_blank"
                  rel="noreferrer"
                  className="btn btn-secondary"
                  style={{ fontSize: '0.82rem', padding: '4px 12px' }}
                >
                  Access Resource ↗
                </a>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Student Confidential Request Modal */}
      {showRequestModal && (
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
          <div className="card" style={{ width: '100%', maxWidth: 540, padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800 }}>Confidential Support Request</h3>
              <button
                type="button"
                onClick={() => setShowRequestModal(false)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '1.2rem' }}
              >
                ✕
              </button>
            </div>

            <div
              style={{
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                border: '1px solid rgba(59, 130, 246, 0.25)',
                borderRadius: 8,
                padding: '10px 14px',
                fontSize: '0.82rem',
                color: '#60a5fa',
                marginBottom: 16,
              }}
            >
              🔒 All support requests are strictly confidential. Only authorized campus counselors and wellbeing advisors have access to your submission.
            </div>

            <form onSubmit={handleSubmitRequest}>
              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Support Category *
                </label>
                <select
                  className="form-control"
                  value={reqType}
                  onChange={(e) => setReqType(e.target.value)}
                >
                  <option value="counseling">Personal Counseling & Guidance</option>
                  <option value="academic_stress">Academic Stress & Burnout</option>
                  <option value="mental_health">Anxiety / Depression Support</option>
                  <option value="accessibility_accommodation">Accessibility & Disability Accommodations</option>
                  <option value="financial_emergency">Student Welfare / Financial Hardship</option>
                  <option value="peer_support">Peer Mentorship Support</option>
                </select>
              </div>

              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Subject *
                </label>
                <input
                  type="text"
                  placeholder="e.g. Requesting a one-on-one session to discuss exam stress"
                  className="form-control"
                  value={reqSubject}
                  onChange={(e) => setReqSubject(e.target.value)}
                  required
                />
              </div>

              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Urgency Level
                </label>
                <select
                  className="form-control"
                  value={reqUrgency}
                  onChange={(e) => setReqUrgency(e.target.value)}
                >
                  <option value="normal">Normal (Routine follow up within 24-48 hrs)</option>
                  <option value="high">High (Needs attention within 24 hrs)</option>
                  <option value="crisis">Crisis (Immediate campus counselor escalation)</option>
                </select>
              </div>

              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Tell us a bit about how you are feeling *
                </label>
                <textarea
                  className="form-control"
                  rows={4}
                  placeholder="Share details you feel comfortable with..."
                  value={reqDescription}
                  onChange={(e) => setReqDescription(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowRequestModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submittingReq}>
                  {submittingReq ? 'Submitting...' : 'Submit Support Request'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Counselor Schedule Appointment Modal */}
      {selectedReqForAppt && (
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
          <div className="card" style={{ width: '100%', maxWidth: 520, padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800 }}>Schedule Counseling Session</h3>
              <button
                type="button"
                onClick={() => setSelectedReqForAppt(null)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '1.2rem' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleScheduleAppointment}>
              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Date & Time *
                </label>
                <input
                  type="datetime-local"
                  className="form-control"
                  value={apptScheduledAt}
                  onChange={(e) => setApptScheduledAt(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                    Type
                  </label>
                  <select
                    className="form-control"
                    value={apptType}
                    onChange={(e) => setApptType(e.target.value as any)}
                  >
                    <option value="virtual">Virtual Meeting</option>
                    <option value="in_person">In-Person Office</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                    Duration (Minutes)
                  </label>
                  <input
                    type="number"
                    className="form-control"
                    value={apptDuration}
                    onChange={(e) => setApptDuration(Number(e.target.value) || 45)}
                  />
                </div>
              </div>

              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Location / Meeting Link
                </label>
                <input
                  type="text"
                  placeholder="e.g. Student Wellness Center Room 204 or https://meet.google.com/..."
                  className="form-control"
                  value={apptLocation}
                  onChange={(e) => setApptLocation(e.target.value)}
                />
              </div>

              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Notes for Student (Optional)
                </label>
                <textarea
                  className="form-control"
                  rows={2}
                  placeholder="Instructions or preparations for the session..."
                  value={apptNotes}
                  onChange={(e) => setApptNotes(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setSelectedReqForAppt(null)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={schedulingAppt}>
                  {schedulingAppt ? 'Scheduling...' : 'Confirm Appointment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Staff Add Resource Modal */}
      {showResourceModal && (
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
          <div className="card" style={{ width: '100%', maxWidth: 520, padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800 }}>Add Wellness Resource</h3>
              <button
                type="button"
                onClick={() => setShowResourceModal(false)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '1.2rem' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateResource}>
              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Title *
                </label>
                <input
                  type="text"
                  placeholder="e.g. Guided Mindfulness & Meditation Audio Guides"
                  className="form-control"
                  value={resTitle}
                  onChange={(e) => setResTitle(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                    Category
                  </label>
                  <select
                    className="form-control"
                    value={resCat}
                    onChange={(e) => setResCat(e.target.value)}
                  >
                    <option value="mental_health">Mental Health</option>
                    <option value="mindfulness">Mindfulness</option>
                    <option value="stress_management">Stress Relief</option>
                    <option value="study_habits">Study Habits</option>
                    <option value="crisis_hotline">Crisis Hotline</option>
                    <option value="accessibility">Accessibility</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                    Emergency Helpline
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. 1926 or +94 11 ..."
                    className="form-control"
                    value={resPhone}
                    onChange={(e) => setResPhone(e.target.value)}
                  />
                </div>
              </div>

              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Resource URL
                </label>
                <input
                  type="text"
                  placeholder="https://..."
                  className="form-control"
                  value={resUrl}
                  onChange={(e) => setResUrl(e.target.value)}
                />
              </div>

              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Description *
                </label>
                <textarea
                  className="form-control"
                  rows={3}
                  placeholder="Details about this resource..."
                  value={resDesc}
                  onChange={(e) => setResDesc(e.target.value)}
                  required
                />
              </div>

              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem' }}>
                  <input
                    type="checkbox"
                    checked={resIsCrisis}
                    onChange={(e) => setResIsCrisis(e.target.checked)}
                  />
                  <span>Mark as Urgent Crisis Resource</span>
                </label>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowResourceModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={creatingRes}>
                  {creatingRes ? 'Adding...' : 'Add Resource'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
