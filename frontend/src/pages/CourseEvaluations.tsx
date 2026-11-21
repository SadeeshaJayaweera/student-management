import React, { useEffect, useState } from 'react'
import api from '@/api/client'
import { useAuth } from '@/contexts/AuthContext'
import {
  CourseEvaluationSurveyItem,
  CourseEvaluationSurveyDetail,
  SurveyAnalytics,
} from '@/types'
import toast from 'react-hot-toast'

export default function CourseEvaluations() {
  const { user } = useAuth()
  const isFaculty = user?.role === 'admin' || user?.role === 'lecturer'

  // Student survey states
  const [surveys, setSurveys] = useState<CourseEvaluationSurveyItem[]>([])
  const [loadingSurveys, setLoadingSurveys] = useState<boolean>(true)
  const [activeSurvey, setActiveSurvey] = useState<CourseEvaluationSurveyDetail | null>(null)
  const [submitting, setSubmitting] = useState<boolean>(false)

  // Answers payload: question_id -> { rating?: number, text?: string }
  const [answers, setAnswers] = useState<Record<number, { rating?: number; text?: string }>>({})

  // Faculty analytics states
  const [selectedSurveyIdForAnalytics, setSelectedSurveyIdForAnalytics] = useState<number | null>(null)
  const [analytics, setAnalytics] = useState<SurveyAnalytics | null>(null)
  const [loadingAnalytics, setLoadingAnalytics] = useState<boolean>(false)

  // Faculty create modal
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false)
  const [coursesList, setCoursesList] = useState<any[]>([])
  const [newCourseId, setNewCourseId] = useState<number | ''>('')
  const [newTitle, setNewTitle] = useState<string>('')
  const [newDesc, setNewDesc] = useState<string>('')
  const [newStartDate, setNewStartDate] = useState<string>('')
  const [newEndDate, setNewEndDate] = useState<string>('')
  const [newIsAnonymous, setNewIsAnonymous] = useState<boolean>(true)
  const [creatingSurvey, setCreatingSurvey] = useState<boolean>(false)

  useEffect(() => {
    loadSurveys()
    if (isFaculty) {
      loadCourses()
    }
  }, [])

  const loadSurveys = async () => {
    try {
      setLoadingSurveys(true)
      const res = await api.get<CourseEvaluationSurveyItem[]>('/evaluations/student/pending')
      setSurveys(res.data)
    } catch (err: any) {
      console.error('Failed to load surveys:', err)
      toast.error('Could not load course evaluations.')
    } finally {
      setLoadingSurveys(false)
    }
  }

  const loadCourses = async () => {
    try {
      const res = await api.get('/courses')
      setCoursesList(res.data)
    } catch (err: any) {
      console.error('Failed to load courses list:', err)
    }
  }

  const openSurveyModal = async (surveyId: number) => {
    try {
      const res = await api.get<CourseEvaluationSurveyDetail>(`/evaluations/surveys/${surveyId}`)
      setActiveSurvey(res.data)
      // Initialize answer map
      const initial: Record<number, { rating?: number; text?: string }> = {}
      res.data.questions.forEach((q) => {
        initial[q.id] = q.question_type.startsWith('rating') ? { rating: 5 } : { text: '' }
      })
      setAnswers(initial)
    } catch (err: any) {
      toast.error('Failed to load survey questions.')
    }
  }

  const handleRatingChange = (qId: number, rating: number) => {
    setAnswers((prev) => ({
      ...prev,
      [qId]: { ...prev[qId], rating },
    }))
  }

  const handleTextChange = (qId: number, text: string) => {
    setAnswers((prev) => ({
      ...prev,
      [qId]: { ...prev[qId], text },
    }))
  }

  const handleSubmitEvaluation = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!activeSurvey || submitting) return

    try {
      setSubmitting(true)
      const payloadAnswers = Object.entries(answers).map(([qIdStr, val]) => ({
        question_id: Number(qIdStr),
        numeric_rating: val.rating,
        text_response: val.text,
      }))

      await api.post(`/evaluations/surveys/${activeSurvey.id}/submit`, {
        answers: payloadAnswers,
      })

      toast.success('Course evaluation submitted successfully! Thank you for your feedback.')
      setActiveSurvey(null)
      loadSurveys()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to submit evaluation.')
    } finally {
      setSubmitting(false)
    }
  }

  const loadAnalytics = async (surveyId: number) => {
    try {
      setLoadingAnalytics(true)
      setSelectedSurveyIdForAnalytics(surveyId)
      const res = await api.get<SurveyAnalytics>(`/evaluations/surveys/${surveyId}/analytics`)
      setAnalytics(res.data)
    } catch (err: any) {
      toast.error('Failed to load survey analytics.')
    } finally {
      setLoadingAnalytics(false)
    }
  }

  const handleCreateSurvey = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newCourseId || !newTitle.trim() || !newStartDate || !newEndDate || creatingSurvey) return

    try {
      setCreatingSurvey(true)
      const payload = {
        course_id: Number(newCourseId),
        title: newTitle.trim(),
        description: newDesc.trim() || undefined,
        start_date: new Date(newStartDate).toISOString(),
        end_date: new Date(newEndDate).toISOString(),
        is_published: true,
        is_anonymous: newIsAnonymous,
      }
      await api.post('/evaluations/surveys', payload)
      toast.success('Course evaluation survey created and published!')
      setShowCreateModal(false)
      setNewCourseId('')
      setNewTitle('')
      setNewDesc('')
      setNewStartDate('')
      setNewEndDate('')
      loadSurveys()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to create survey.')
    } finally {
      setCreatingSurvey(false)
    }
  }

  return (
    <div className="fade-in" style={{ maxWidth: 1200, margin: '0 auto', paddingBottom: 40 }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.85rem', fontWeight: 800, fontFamily: "'Outfit', sans-serif" }}>
            Course Evaluation & Student Feedback
          </h1>
          <p className="text-muted" style={{ margin: '4px 0 0 0', fontSize: '0.92rem' }}>
            Empowering student voice, pedagogical improvement, and academic quality assurance.
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {isFaculty && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: 6 }}
            >
              <span>➕</span> Create New Evaluation
            </button>
          )}
        </div>
      </div>

      {/* Anonymity Assurance Banner */}
      <div
        className="card"
        style={{
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(59, 130, 246, 0.12))',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          marginBottom: 24,
          padding: '16px 20px',
          display: 'flex',
          alignItems: 'center',
          gap: 16,
        }}
      >
        <div style={{ fontSize: '2.4rem' }}>🔒</div>
        <div>
          <h4 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700, color: '#34d399' }}>
            100% Cryptographically Anonymous & Confidential
          </h4>
          <p className="text-muted" style={{ margin: '4px 0 0 0', fontSize: '0.88rem' }}>
            Your feedback directly drives curriculum updates and teaching excellence. Responses are disconnected
            from student IDs using one-way cryptographic tokens to ensure candid, authentic evaluations.
          </p>
        </div>
      </div>

      {/* Surveys List Section */}
      <div className="card" style={{ padding: 20, marginBottom: 24 }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: '1.2rem', fontWeight: 700 }}>
          {isFaculty ? 'Active Course Evaluations' : 'Your Course Evaluations'}
        </h3>

        {loadingSurveys ? (
          <div style={{ padding: 32, textAlign: 'center' }} className="text-muted">
            Loading evaluations...
          </div>
        ) : surveys.length === 0 ? (
          <div style={{ padding: 32, textAlign: 'center' }} className="text-muted">
            <div style={{ fontSize: '2.5rem', marginBottom: 8 }}>📝</div>
            <p style={{ margin: 0 }}>No course evaluations currently open for your courses.</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16 }}>
            {surveys.map((s) => (
              <div
                key={s.id}
                style={{
                  border: '1px solid var(--border-color)',
                  borderRadius: 12,
                  padding: 18,
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                    <span
                      style={{
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        backgroundColor: 'rgba(59, 130, 246, 0.15)',
                        color: '#60a5fa',
                        padding: '2px 8px',
                        borderRadius: 6,
                      }}
                    >
                      {s.course_code || 'Course'}
                    </span>
                    <span
                      style={{
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        padding: '2px 8px',
                        borderRadius: 6,
                        backgroundColor: s.has_submitted ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                        color: s.has_submitted ? '#34d399' : '#fbbf24',
                      }}
                    >
                      {s.has_submitted ? '✓ Completed' : 'Pending Feedback'}
                    </span>
                  </div>

                  <h4 style={{ margin: '0 0 6px 0', fontSize: '1.05rem', fontWeight: 700 }}>
                    {s.title}
                  </h4>
                  <div className="text-muted" style={{ fontSize: '0.82rem', marginBottom: 12 }}>
                    Course: {s.course_title || s.course_code}
                  </div>

                  {s.description && (
                    <p className="text-muted" style={{ fontSize: '0.84rem', margin: '0 0 12px 0', lineHeight: 1.4 }}>
                      {s.description}
                    </p>
                  )}

                  <div className="text-muted" style={{ fontSize: '0.78rem', marginBottom: 14 }}>
                    Ends on: {new Date(s.end_date).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: 10, marginTop: 10 }}>
                  {!s.has_submitted ? (
                    <button
                      onClick={() => openSurveyModal(s.id)}
                      className="btn btn-primary"
                      style={{ flex: 1, fontSize: '0.88rem' }}
                    >
                      Evaluate Course →
                    </button>
                  ) : (
                    <button
                      disabled
                      className="btn btn-secondary"
                      style={{ flex: 1, fontSize: '0.88rem', opacity: 0.7 }}
                    >
                      ✓ Already Submitted
                    </button>
                  )}

                  {isFaculty && (
                    <button
                      onClick={() => loadAnalytics(s.id)}
                      className="btn btn-secondary"
                      style={{ fontSize: '0.88rem' }}
                    >
                      📊 Analytics
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Faculty Analytics Dashboard Drawer */}
      {selectedSurveyIdForAnalytics && analytics && (
        <div className="card" style={{ padding: 24, marginTop: 24, border: '1px solid rgba(59, 130, 246, 0.3)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
            <div>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#60a5fa', textTransform: 'uppercase' }}>
                Course Feedback Analytics
              </span>
              <h3 style={{ margin: '4px 0 0 0', fontSize: '1.3rem', fontWeight: 800 }}>
                {analytics.course_code}: {analytics.title}
              </h3>
            </div>
            <button
              onClick={() => setSelectedSurveyIdForAnalytics(null)}
              className="btn btn-secondary"
              style={{ fontSize: '0.8rem' }}
            >
              ✕ Close Analytics
            </button>
          </div>

          {/* Metric KPI cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 24 }}>
            <div className="card" style={{ padding: 16, textAlign: 'center' }}>
              <div className="text-muted" style={{ fontSize: '0.8rem' }}>Total Responses</div>
              <div style={{ fontSize: '2rem', fontWeight: 800, marginTop: 4, color: '#60a5fa' }}>
                {analytics.total_responses}
              </div>
            </div>
            <div className="card" style={{ padding: 16, textAlign: 'center' }}>
              <div className="text-muted" style={{ fontSize: '0.8rem' }}>Overall Course Rating</div>
              <div style={{ fontSize: '2rem', fontWeight: 800, marginTop: 4, color: '#34d399' }}>
                {analytics.overall_average ? `${analytics.overall_average} / 5.0` : 'N/A'}
              </div>
            </div>
            {Object.entries(analytics.category_averages).map(([cat, score]) => (
              <div key={cat} className="card" style={{ padding: 16, textAlign: 'center' }}>
                <div className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase' }}>
                  {cat.replace('_', ' ')}
                </div>
                <div style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: 4 }}>
                  {score} / 5.0
                </div>
              </div>
            ))}
          </div>

          {/* Detailed Question breakdown */}
          <h4 style={{ margin: '0 0 14px 0', fontSize: '1rem', fontWeight: 700 }}>
            Pedagogical Criteria Breakdown
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {analytics.question_analytics.map((q) => (
              <div
                key={q.question_id}
                style={{
                  padding: 16,
                  borderRadius: 10,
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-color)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                  <span style={{ fontWeight: 600, fontSize: '0.92rem' }}>{q.question_text}</span>
                  {q.average_rating != null && (
                    <span
                      style={{
                        fontWeight: 800,
                        fontSize: '0.92rem',
                        color: q.average_rating >= 4.0 ? '#34d399' : q.average_rating >= 3.0 ? '#fbbf24' : '#ef4444',
                        backgroundColor: 'rgba(255, 255, 255, 0.06)',
                        padding: '2px 8px',
                        borderRadius: 6,
                      }}
                    >
                      ★ {q.average_rating} / 5.0
                    </span>
                  )}
                </div>

                {/* Rating distribution bar if numeric */}
                {Object.keys(q.rating_distribution).length > 0 && (
                  <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                    {['1', '2', '3', '4', '5'].map((star) => {
                      const count = q.rating_distribution[star] || 0
                      const pct = q.response_count > 0 ? (count / q.response_count) * 100 : 0
                      return (
                        <div key={star} style={{ flex: 1, textAlign: 'center' }}>
                          <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>{star}★ ({count})</div>
                          <div
                            style={{
                              height: 6,
                              backgroundColor: 'rgba(255, 255, 255, 0.1)',
                              borderRadius: 3,
                              overflow: 'hidden',
                              marginTop: 2,
                            }}
                          >
                            <div
                              style={{
                                width: `${pct}%`,
                                height: '100%',
                                backgroundColor: '#60a5fa',
                              }}
                            />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}

                {/* Qualitative student feedback comments */}
                {q.text_feedback && q.text_feedback.length > 0 && (
                  <div style={{ marginTop: 12 }}>
                    <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#94a3b8', marginBottom: 6 }}>
                      Student Comments ({q.text_feedback.length}):
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {q.text_feedback.map((txt, idx) => (
                        <div
                          key={idx}
                          style={{
                            fontSize: '0.84rem',
                            padding: '8px 12px',
                            backgroundColor: 'rgba(255, 255, 255, 0.03)',
                            borderRadius: 6,
                            fontStyle: 'italic',
                          }}
                        >
                          "{txt}"
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Student Evaluation Modal */}
      {activeSurvey && (
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
          <div
            className="card"
            style={{
              width: '100%',
              maxWidth: 680,
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: 24,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div>
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    backgroundColor: 'rgba(59, 130, 246, 0.15)',
                    color: '#60a5fa',
                    padding: '2px 8px',
                    borderRadius: 6,
                  }}
                >
                  {activeSurvey.course_code}
                </span>
                <h3 style={{ margin: '6px 0 0 0', fontSize: '1.25rem', fontWeight: 800 }}>
                  {activeSurvey.title}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setActiveSurvey(null)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '1.2rem' }}
              >
                ✕
              </button>
            </div>

            <div
              style={{
                backgroundColor: 'rgba(16, 185, 129, 0.08)',
                border: '1px solid rgba(16, 185, 129, 0.2)',
                borderRadius: 8,
                padding: '10px 14px',
                fontSize: '0.84rem',
                color: '#34d399',
                marginBottom: 20,
              }}
            >
              🔒 Confidential & Anonymous — Your ratings and feedback cannot be linked back to you.
            </div>

            <form onSubmit={handleSubmitEvaluation}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                {activeSurvey.questions.map((q, idx) => (
                  <div
                    key={q.id}
                    style={{
                      padding: 16,
                      borderRadius: 10,
                      backgroundColor: 'rgba(255, 255, 255, 0.02)',
                      border: '1px solid var(--border-color)',
                    }}
                  >
                    <label style={{ display: 'block', fontSize: '0.92rem', fontWeight: 600, marginBottom: 10 }}>
                      {idx + 1}. {q.question_text} {q.is_required && <span style={{ color: '#ef4444' }}>*</span>}
                    </label>

                    {q.question_type.startsWith('rating') ? (
                      <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                        {[1, 2, 3, 4, 5].map((val) => {
                          const isSelected = answers[q.id]?.rating === val
                          return (
                            <button
                              type="button"
                              key={val}
                              onClick={() => handleRatingChange(q.id, val)}
                              className={`btn ${isSelected ? 'btn-primary' : 'btn-secondary'}`}
                              style={{
                                width: 44,
                                height: 44,
                                borderRadius: '50%',
                                fontSize: '1rem',
                                fontWeight: 700,
                              }}
                            >
                              {val}
                            </button>
                          )
                        })}
                        <span className="text-muted" style={{ fontSize: '0.8rem', marginLeft: 10 }}>
                          (1 = Unsatisfactory, 5 = Excellent)
                        </span>
                      </div>
                    ) : (
                      <textarea
                        className="form-control"
                        rows={3}
                        placeholder="Provide your feedback..."
                        value={answers[q.id]?.text || ''}
                        onChange={(e) => handleTextChange(q.id, e.target.value)}
                        required={q.is_required}
                      />
                    )}
                  </div>
                ))}
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 24 }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setActiveSurvey(null)}
                  disabled={submitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={submitting}
                >
                  {submitting ? 'Submitting...' : 'Submit Evaluation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Faculty Create Survey Modal */}
      {showCreateModal && (
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
              <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800 }}>Create Course Evaluation</h3>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '1.2rem' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateSurvey}>
              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Course *
                </label>
                <select
                  className="form-control"
                  value={newCourseId}
                  onChange={(e) => setNewCourseId(Number(e.target.value) || '')}
                  required
                >
                  <option value="">Select course...</option>
                  {coursesList.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.course_code} — {c.title}
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Evaluation Title *
                </label>
                <input
                  type="text"
                  placeholder="e.g. End of Semester Course Evaluation"
                  className="form-control"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  required
                />
              </div>

              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Description (Optional)
                </label>
                <textarea
                  className="form-control"
                  rows={2}
                  placeholder="Instructions for students..."
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                    Start Date *
                  </label>
                  <input
                    type="date"
                    className="form-control"
                    value={newStartDate}
                    onChange={(e) => setNewStartDate(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                    End Date *
                  </label>
                  <input
                    type="date"
                    className="form-control"
                    value={newEndDate}
                    onChange={(e) => setNewEndDate(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem' }}>
                  <input
                    type="checkbox"
                    checked={newIsAnonymous}
                    onChange={(e) => setNewIsAnonymous(e.target.checked)}
                  />
                  <span>Enforce Student Anonymity</span>
                </label>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowCreateModal(false)}
                  disabled={creatingSurvey}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={creatingSurvey}
                >
                  {creatingSurvey ? 'Creating...' : 'Create & Publish'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
