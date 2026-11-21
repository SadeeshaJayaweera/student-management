import React, { useState, useEffect } from 'react'
import api from '@/api/client'
import { useAuth } from '@/contexts/AuthContext'
import type { StudentTask, StudentTaskMetrics, CalendarEvent } from '@/types'
import toast from 'react-hot-toast'

export default function CalendarTasks() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<'calendar' | 'tasks'>('tasks')
  const [tasks, setTasks] = useState<StudentTask[]>([])
  const [metrics, setMetrics] = useState<StudentTaskMetrics | null>(null)
  const [events, setEvents] = useState<CalendarEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string>('all')

  // Modals
  const [showTaskModal, setShowTaskModal] = useState(false)
  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    due_date: '',
    priority: 'medium',
    category: 'study',
    estimated_minutes: 60,
  })

  const [showEventModal, setShowEventModal] = useState(false)
  const [newEvent, setNewEvent] = useState({
    title: '',
    description: '',
    event_type: 'personal',
    start_time: '',
    end_time: '',
    all_day: false,
    location: '',
    color: '#4F46E5',
  })

  const loadData = async () => {
    try {
      setLoading(true)
      const [tRes, mRes, eRes] = await Promise.all([
        api.get<StudentTask[]>('/tasks'),
        api.get<StudentTaskMetrics>('/tasks/metrics'),
        api.get<CalendarEvent[]>('/calendar/events'),
      ])
      setTasks(tRes.data || [])
      setMetrics(mRes.data || null)
      setEvents(eRes.data || [])
    } catch {
      toast.error('Failed to load calendar and task data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleToggleTaskStatus = async (task: StudentTask) => {
    const nextStatus = task.status === 'completed' ? 'todo' : 'completed'
    try {
      await api.patch(`/tasks/${task.id}/status`, { status: nextStatus })
      toast.success(nextStatus === 'completed' ? 'Task completed! 🎉' : 'Task reopened')
      loadData()
    } catch {
      toast.error('Failed to update task status')
    }
  }

  const handleDeleteTask = async (id: number) => {
    if (!confirm('Are you sure you want to delete this task?')) return
    try {
      await api.delete(`/tasks/${id}`)
      toast.success('Task removed')
      loadData()
    } catch {
      toast.error('Failed to delete task')
    }
  }

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/tasks', {
        ...newTask,
        due_date: newTask.due_date ? new Date(newTask.due_date).toISOString() : null,
      })
      toast.success('New task added')
      setShowTaskModal(false)
      setNewTask({
        title: '',
        description: '',
        due_date: '',
        priority: 'medium',
        category: 'study',
        estimated_minutes: 60,
      })
      loadData()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to create task')
    }
  }

  const handleCreateEvent = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/calendar/events', {
        ...newEvent,
        start_time: new Date(newEvent.start_time).toISOString(),
        end_time: new Date(newEvent.end_time).toISOString(),
      })
      toast.success('Calendar event scheduled')
      setShowEventModal(false)
      setNewEvent({
        title: '',
        description: '',
        event_type: 'personal',
        start_time: '',
        end_time: '',
        all_day: false,
        location: '',
        color: '#4F46E5',
      })
      loadData()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to schedule event')
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center" style={{ height: 320 }}>
        <div className="spinner" />
      </div>
    )
  }

  const filteredTasks =
    statusFilter === 'all' ? tasks : tasks.filter((t) => t.status === statusFilter)

  return (
    <div className="fade-in">
      {/* Header */}
      <div className="flex justify-between items-center mb-24 flex-wrap gap-12">
        <div>
          <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 800 }}>📅 Calendar & Study Tasks</h1>
          <p className="text-muted text-sm" style={{ marginTop: 4 }}>
            Unified academic planner, assignment deadlines, lecture sessions, and personal study goals
          </p>
        </div>
        <div className="flex items-center gap-12">
          {activeTab === 'tasks' ? (
            <button className="btn btn-primary btn-sm" onClick={() => setShowTaskModal(true)}>
              ➕ New Task
            </button>
          ) : (
            <button className="btn btn-primary btn-sm" onClick={() => setShowEventModal(true)}>
              ➕ New Event
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-8 mb-24">
        <button
          className={`btn btn-sm ${activeTab === 'tasks' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setActiveTab('tasks')}
        >
          ✅ Tasks & Productivity ({tasks.length})
        </button>
        <button
          className={`btn btn-sm ${activeTab === 'calendar' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setActiveTab('calendar')}
        >
          📅 Unified Calendar ({events.length})
        </button>
      </div>

      {activeTab === 'tasks' ? (
        <div>
          {/* Metrics */}
          {metrics && (
            <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(4,1fr)', marginBottom: 24 }}>
              <div className="stat-card stat-teal">
                <div className="stat-icon" style={{ background: 'rgba(0,212,170,.15)' }}>🎯</div>
                <div>
                  <div className="stat-value" style={{ color: '#00D4AA' }}>{metrics.completion_rate}%</div>
                  <div className="stat-label">Completion Rate</div>
                </div>
              </div>
              <div className="stat-card stat-purple">
                <div className="stat-icon" style={{ background: 'rgba(108,99,255,.18)' }}>📋</div>
                <div>
                  <div className="stat-value" style={{ color: '#8B85FF' }}>{metrics.total_tasks}</div>
                  <div className="stat-label">Total Tasks</div>
                </div>
              </div>
              <div className="stat-card stat-coral">
                <div className="stat-icon" style={{ background: 'rgba(255,107,107,.18)' }}>⚠️</div>
                <div>
                  <div className="stat-value" style={{ color: '#FF6B6B' }}>{metrics.overdue_tasks}</div>
                  <div className="stat-label">Overdue Tasks</div>
                </div>
              </div>
              <div className="stat-card stat-purple">
                <div className="stat-icon" style={{ background: 'rgba(108,99,255,.18)' }}>⚡</div>
                <div>
                  <div className="stat-value" style={{ color: '#8B85FF' }}>{metrics.due_today_count}</div>
                  <div className="stat-label">Due Today</div>
                </div>
              </div>
            </div>
          )}

          {/* Filter Pills */}
          <div className="flex gap-8 mb-16 overflow-x-auto">
            {['all', 'todo', 'in_progress', 'completed'].map((f) => (
              <button
                key={f}
                className={`btn btn-sm ${statusFilter === f ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => setStatusFilter(f)}
                style={{ textTransform: 'capitalize' }}
              >
                {f.replace('_', ' ')}
              </button>
            ))}
          </div>

          {/* Tasks List */}
          <div className="card">
            {filteredTasks.length === 0 ? (
              <div className="text-muted text-sm" style={{ textAlign: 'center', padding: '36px 0' }}>
                No tasks found in this view.
              </div>
            ) : (
              <div className="flex flex-col gap-10">
                {filteredTasks.map((t) => (
                  <div
                    key={t.id}
                    className="flex justify-between items-center"
                    style={{
                      padding: '12px 16px',
                      background: 'rgba(255,255,255,0.02)',
                      borderRadius: 8,
                      border: '1px solid rgba(255,255,255,0.05)',
                      opacity: t.status === 'completed' ? 0.6 : 1,
                    }}
                  >
                    <div className="flex items-center gap-12">
                      <input
                        type="checkbox"
                        checked={t.status === 'completed'}
                        onChange={() => handleToggleTaskStatus(t)}
                        style={{ cursor: 'pointer', transform: 'scale(1.2)' }}
                      />
                      <div>
                        <div
                          style={{
                            fontWeight: 600,
                            fontSize: '.95rem',
                            textDecoration: t.status === 'completed' ? 'line-through' : 'none',
                          }}
                        >
                          {t.title}
                        </div>
                        <div className="text-xs text-muted flex gap-8 items-center mt-2 flex-wrap">
                          {t.course_code && <span className="badge badge-info text-xs">{t.course_code}</span>}
                          <span>📂 {t.category.toUpperCase()}</span>
                          {t.due_date && (
                            <span style={{ color: t.is_overdue ? '#FF6B6B' : 'inherit' }}>
                              ⏰ Due {new Date(t.due_date).toLocaleDateString()}
                            </span>
                          )}
                          <span>⏱️ {t.estimated_minutes}m</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-10">
                      <span
                        className={`badge ${
                          t.priority === 'urgent'
                            ? 'badge-danger'
                            : t.priority === 'high'
                            ? 'badge-warning'
                            : 'badge-info'
                        }`}
                        style={{ fontSize: '.7rem', textTransform: 'uppercase' }}
                      >
                        {t.priority}
                      </span>
                      <button
                        className="btn btn-ghost btn-sm"
                        style={{ padding: '2px 8px', color: '#FF6B6B' }}
                        onClick={() => handleDeleteTask(t.id)}
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Calendar Events Tab */
        <div className="flex flex-col gap-16">
          <div className="card">
            <div className="card-title mb-16">Chronological Academic & Personal Events</div>
            {events.length === 0 ? (
              <div className="text-muted text-sm" style={{ textAlign: 'center', padding: '36px 0' }}>
                No upcoming events or deadlines scheduled.
              </div>
            ) : (
              <div className="flex flex-col gap-12">
                {events.map((ev) => (
                  <div
                    key={`${ev.event_type}-${ev.id}`}
                    className="flex justify-between items-center"
                    style={{
                      padding: 14,
                      background: 'rgba(255,255,255,0.02)',
                      borderLeft: `4px solid ${ev.color || '#4F46E5'}`,
                      borderRadius: 6,
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 700, fontSize: '.95rem' }}>{ev.title}</div>
                      <div className="text-xs text-muted mt-4 flex items-center gap-12 flex-wrap">
                        {ev.course_code && <span className="badge badge-info">{ev.course_code}</span>}
                        <span>📅 {new Date(ev.start_time).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}</span>
                        {ev.location && <span>📍 {ev.location}</span>}
                      </div>
                    </div>
                    <span
                      className="badge badge-primary"
                      style={{ textTransform: 'uppercase', fontSize: '.7rem' }}
                    >
                      {ev.event_type.replace('_', ' ')}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Add Task Modal */}
      {showTaskModal && (
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
              <div style={{ fontWeight: 700, fontSize: '1.2rem' }}>Add Personal Task</div>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowTaskModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateTask} className="flex flex-col gap-12">
              <div>
                <label className="text-xs text-muted block mb-4">Task Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Complete SQA Lab Exercise 3"
                  className="input w-full"
                  value={newTask.title}
                  onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                />
              </div>

              <div>
                <label className="text-xs text-muted block mb-4">Description</label>
                <textarea
                  rows={2}
                  className="input w-full"
                  placeholder="Notes, instructions or reference links..."
                  value={newTask.description}
                  onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
                />
              </div>

              <div className="grid-2 gap-12">
                <div>
                  <label className="text-xs text-muted block mb-4">Priority</label>
                  <select
                    className="input w-full"
                    value={newTask.priority}
                    onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-muted block mb-4">Category</label>
                  <select
                    className="input w-full"
                    value={newTask.category}
                    onChange={(e) => setNewTask({ ...newTask, category: e.target.value })}
                  >
                    <option value="study">Study</option>
                    <option value="assignment">Assignment</option>
                    <option value="revision">Revision</option>
                    <option value="exam_prep">Exam Prep</option>
                    <option value="personal">Personal</option>
                  </select>
                </div>
              </div>

              <div className="grid-2 gap-12">
                <div>
                  <label className="text-xs text-muted block mb-4">Due Date & Time</label>
                  <input
                    type="datetime-local"
                    className="input w-full"
                    value={newTask.due_date}
                    onChange={(e) => setNewTask({ ...newTask, due_date: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-xs text-muted block mb-4">Est. Minutes</label>
                  <input
                    type="number"
                    min={5}
                    className="input w-full"
                    value={newTask.estimated_minutes}
                    onChange={(e) => setNewTask({ ...newTask, estimated_minutes: parseInt(e.target.value) || 30 })}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-12 mt-16">
                <button type="button" className="btn btn-ghost" onClick={() => setShowTaskModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save Task
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Event Modal */}
      {showEventModal && (
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
              <div style={{ fontWeight: 700, fontSize: '1.2rem' }}>Schedule Calendar Event</div>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowEventModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateEvent} className="flex flex-col gap-12">
              <div>
                <label className="text-xs text-muted block mb-4">Event Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Algorithm Study Group"
                  className="input w-full"
                  value={newEvent.title}
                  onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                />
              </div>

              <div className="grid-2 gap-12">
                <div>
                  <label className="text-xs text-muted block mb-4">Start Time</label>
                  <input
                    type="datetime-local"
                    required
                    className="input w-full"
                    value={newEvent.start_time}
                    onChange={(e) => setNewEvent({ ...newEvent, start_time: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-xs text-muted block mb-4">End Time</label>
                  <input
                    type="datetime-local"
                    required
                    className="input w-full"
                    value={newEvent.end_time}
                    onChange={(e) => setNewEvent({ ...newEvent, end_time: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid-2 gap-12">
                <div>
                  <label className="text-xs text-muted block mb-4">Event Type</label>
                  <select
                    className="input w-full"
                    value={newEvent.event_type}
                    onChange={(e) => setNewEvent({ ...newEvent, event_type: e.target.value })}
                  >
                    <option value="personal">Personal</option>
                    <option value="academic">Academic</option>
                    <option value="campus">Campus</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-muted block mb-4">Location</label>
                  <input
                    type="text"
                    className="input w-full"
                    placeholder="e.g. Library Discussion Room 2"
                    value={newEvent.location}
                    onChange={(e) => setNewEvent({ ...newEvent, location: e.target.value })}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-12 mt-16">
                <button type="button" className="btn btn-ghost" onClick={() => setShowEventModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save Event
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
