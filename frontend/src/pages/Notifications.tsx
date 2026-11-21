import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '@/api/client'
import { useAuth } from '@/contexts/AuthContext'
import {
  NotificationItem,
  NotificationPreferences,
  NotificationStats,
} from '@/types'
import toast from 'react-hot-toast'

export default function Notifications() {
  const { user } = useAuth()
  const [notifications, setNotifications] = useState<NotificationItem[]>([])
  const [stats, setStats] = useState<NotificationStats | null>(null)
  const [preferences, setPreferences] = useState<NotificationPreferences | null>(null)

  // Filters & State
  const [loading, setLoading] = useState<boolean>(true)
  const [activeCategory, setActiveCategory] = useState<string>('all')
  const [onlyUnread, setOnlyUnread] = useState<boolean>(false)
  const [priorityFilter, setPriorityFilter] = useState<string>('all')
  const [selectedIds, setSelectedIds] = useState<number[]>([])

  // Modals
  const [showPreferencesModal, setShowPreferencesModal] = useState<boolean>(false)
  const [savingPrefs, setSavingPrefs] = useState<boolean>(false)
  const [showBroadcastModal, setShowBroadcastModal] = useState<boolean>(false)
  const [broadcasting, setBroadcasting] = useState<boolean>(false)

  // Broadcast Form
  const [bTitle, setBTitle] = useState<string>('')
  const [bMessage, setBMessage] = useState<string>('')
  const [bType, setBType] = useState<string>('info')
  const [bCategory, setBCategory] = useState<string>('announcement')
  const [bPriority, setBPriority] = useState<string>('normal')
  const [bTargetRole, setBTargetRole] = useState<string>('')
  const [bLink, setBLink] = useState<string>('')

  const isStaff = user?.role === 'admin' || user?.role === 'lecturer'

  useEffect(() => {
    loadData()
  }, [activeCategory, onlyUnread, priorityFilter])

  const loadData = async () => {
    try {
      setLoading(true)
      const params: Record<string, any> = {}
      if (activeCategory !== 'all') params.category = activeCategory
      if (onlyUnread) params.is_read = false
      if (priorityFilter !== 'all') params.priority = priorityFilter

      const [notifsRes, statsRes, prefsRes] = await Promise.all([
        api.get<NotificationItem[]>('/notifications', { params }),
        api.get<NotificationStats>('/notifications/stats'),
        api.get<NotificationPreferences>('/notifications/preferences'),
      ])

      setNotifications(notifsRes.data)
      setStats(statsRes.data)
      setPreferences(prefsRes.data)
    } catch (err: any) {
      console.error('Failed to load notification center data:', err)
      toast.error('Failed to load notifications.')
    } finally {
      setLoading(false)
    }
  }

  const handleMarkAllRead = async () => {
    try {
      await api.post('/notifications/batch-read', {})
      toast.success('All notifications marked as read.')
      loadData()
    } catch (err: any) {
      toast.error('Failed to update notifications.')
    }
  }

  const handleBatchAction = async (action: 'mark_read' | 'delete') => {
    if (selectedIds.length === 0) return
    try {
      await api.post('/notifications/batch-action', {
        notification_ids: selectedIds,
        action,
      })
      toast.success(
        action === 'mark_read'
          ? `${selectedIds.length} notifications marked as read.`
          : `${selectedIds.length} notifications deleted.`
      )
      setSelectedIds([])
      loadData()
    } catch (err: any) {
      toast.error('Batch action failed.')
    }
  }

  const handleDeleteOne = async (id: number) => {
    try {
      await api.delete(`/notifications/${id}`)
      toast.success('Notification removed.')
      setNotifications((prev) => prev.filter((n) => n.id !== id))
      loadData()
    } catch (err: any) {
      toast.error('Failed to delete notification.')
    }
  }

  const toggleSelectOne = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    )
  }

  const toggleSelectAll = () => {
    if (selectedIds.length === notifications.length) {
      setSelectedIds([])
    } else {
      setSelectedIds(notifications.map((n) => n.id))
    }
  }

  const handleSavePreferences = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!preferences) return
    try {
      setSavingPrefs(true)
      const res = await api.put<NotificationPreferences>('/notifications/preferences', preferences)
      setPreferences(res.data)
      toast.success('Notification preferences updated!')
      setShowPreferencesModal(false)
    } catch (err: any) {
      toast.error('Failed to save preferences.')
    } finally {
      setSavingPrefs(false)
    }
  }

  const handleSendBroadcast = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!bTitle.trim() || !bMessage.trim()) return

    try {
      setBroadcasting(true)
      const payload = {
        title: bTitle.trim(),
        message: bMessage.trim(),
        notification_type: bType,
        category: bCategory,
        priority: bPriority,
        target_role: bTargetRole || undefined,
        link: bLink.trim() || undefined,
      }
      const res = await api.post('/notifications/broadcast', payload)
      toast.success(`Broadcast sent to ${res.data.recipients_count} users!`)
      setShowBroadcastModal(false)
      setBTitle('')
      setBMessage('')
      setBLink('')
      loadData()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to dispatch broadcast.')
    } finally {
      setBroadcasting(false)
    }
  }

  const categories = [
    { key: 'all', label: 'All Notifications', icon: '🔔' },
    { key: 'academic', label: 'Academic', icon: '📚' },
    { key: 'deadline', label: 'Deadlines', icon: '⏰' },
    { key: 'announcement', label: 'Campus Announcements', icon: '📢' },
    { key: 'system', label: 'System Alerts', icon: '⚙️' },
    { key: 'finance', label: 'Finance & Fees', icon: '💳' },
  ]

  const getPriorityStyle = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return {
          bg: 'rgba(239, 68, 68, 0.15)',
          color: '#ef4444',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          label: '🚨 URGENT',
        }
      case 'high':
        return {
          bg: 'rgba(245, 158, 11, 0.15)',
          color: '#f59e0b',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          label: '⚠️ HIGH',
        }
      default:
        return {
          bg: 'rgba(59, 130, 246, 0.12)',
          color: '#60a5fa',
          border: '1px solid rgba(59, 130, 246, 0.25)',
          label: 'NORMAL',
        }
    }
  }

  return (
    <div className="fade-in" style={{ maxWidth: 1200, margin: '0 auto', paddingBottom: 40 }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.85rem', fontWeight: 800, fontFamily: "'Outfit', sans-serif" }}>
            Notification Center
          </h1>
          <p className="text-muted" style={{ margin: '4px 0 0 0', fontSize: '0.92rem' }}>
            Unified real-time alerts, academic notifications, campus announcements, and reminders.
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {isStaff && (
            <button
              onClick={() => setShowBroadcastModal(true)}
              className="btn btn-secondary"
              style={{ display: 'flex', alignItems: 'center', gap: 6 }}
            >
              <span>📢</span> Broadcast Alert
            </button>
          )}
          <button
            onClick={() => setShowPreferencesModal(true)}
            className="btn btn-secondary"
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <span>⚙️</span> Delivery Settings
          </button>
          <button
            onClick={handleMarkAllRead}
            className="btn btn-primary"
            disabled={!stats || stats.total_unread === 0}
          >
            ✓ Mark All Read
          </button>
        </div>
      </div>

      {/* Metrics Banner */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 16,
          marginBottom: 24,
        }}
      >
        <div className="card" style={{ padding: '16px 20px' }}>
          <div className="text-muted" style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase' }}>
            Unread Alerts
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: 4, color: stats?.total_unread ? '#ef4444' : '#10b981' }}>
            {stats?.total_unread || 0}
          </div>
          <div className="text-muted" style={{ fontSize: '0.8rem', marginTop: 2 }}>
            Out of {stats?.total_count || 0} total notifications
          </div>
        </div>

        <div className="card" style={{ padding: '16px 20px' }}>
          <div className="text-muted" style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase' }}>
            Urgent Attention
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: 4, color: '#f59e0b' }}>
            {stats?.unread_by_priority?.['urgent'] || 0}
          </div>
          <div className="text-muted" style={{ fontSize: '0.8rem', marginTop: 2 }}>
            Requires immediate review
          </div>
        </div>

        <div className="card" style={{ padding: '16px 20px' }}>
          <div className="text-muted" style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase' }}>
            Academic Deadlines
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: 4, color: '#3b82f6' }}>
            {(stats?.unread_by_category?.['deadline'] || 0) + (stats?.unread_by_category?.['academic'] || 0)}
          </div>
          <div className="text-muted" style={{ fontSize: '0.8rem', marginTop: 2 }}>
            Assignments, quizzes & courses
          </div>
        </div>

        <div className="card" style={{ padding: '16px 20px' }}>
          <div className="text-muted" style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase' }}>
            Announcements
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: 4, color: '#8b5cf6' }}>
            {stats?.unread_by_category?.['announcement'] || 0}
          </div>
          <div className="text-muted" style={{ fontSize: '0.8rem', marginTop: 2 }}>
            Campus & department notices
          </div>
        </div>
      </div>

      {/* Category Tabs & Controls */}
      <div className="card" style={{ padding: '12px 16px', marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          {/* Category Chips */}
          <div style={{ display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 4 }}>
            {categories.map((c) => (
              <button
                key={c.key}
                onClick={() => setActiveCategory(c.key)}
                className={`btn ${activeCategory === c.key ? 'btn-primary' : 'btn-secondary'}`}
                style={{
                  fontSize: '0.85rem',
                  padding: '6px 14px',
                  borderRadius: 20,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  whiteSpace: 'nowrap',
                }}
              >
                <span>{c.icon}</span>
                <span>{c.label}</span>
                {c.key !== 'all' && (stats?.unread_by_category?.[c.key] || 0) > 0 && (
                  <span
                    style={{
                      backgroundColor: 'rgba(239, 68, 68, 0.8)',
                      color: '#fff',
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      padding: '1px 6px',
                      borderRadius: 10,
                    }}
                  >
                    {stats?.unread_by_category[c.key]}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Filter switches */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.85rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={onlyUnread}
                onChange={(e) => setOnlyUnread(e.target.checked)}
              />
              <span>Unread Only</span>
            </label>

            <select
              className="form-control"
              style={{ width: 140, fontSize: '0.82rem', padding: '4px 8px' }}
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
            >
              <option value="all">All Priorities</option>
              <option value="urgent">Urgent Only</option>
              <option value="high">High Only</option>
              <option value="normal">Normal</option>
            </select>
          </div>
        </div>

        {/* Batch Selection Action Bar */}
        {selectedIds.length > 0 && (
          <div
            style={{
              marginTop: 12,
              paddingTop: 10,
              borderTop: '1px solid var(--border-color)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              backgroundColor: 'rgba(59, 130, 246, 0.08)',
              padding: '8px 12px',
              borderRadius: 8,
            }}
          >
            <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>
              {selectedIds.length} item{selectedIds.length > 1 ? 's' : ''} selected
            </span>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={() => handleBatchAction('mark_read')}
                className="btn btn-secondary"
                style={{ fontSize: '0.8rem', padding: '4px 10px' }}
              >
                Mark as Read
              </button>
              <button
                onClick={() => handleBatchAction('delete')}
                className="btn btn-secondary"
                style={{ fontSize: '0.8rem', padding: '4px 10px', color: '#ef4444' }}
              >
                Delete Selected
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Notifications List */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div
          style={{
            padding: '12px 18px',
            borderBottom: '1px solid var(--border-color)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor: 'rgba(255, 255, 255, 0.02)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <input
              type="checkbox"
              checked={notifications.length > 0 && selectedIds.length === notifications.length}
              onChange={toggleSelectAll}
            />
            <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Select All</span>
          </div>
          <span className="text-muted" style={{ fontSize: '0.82rem' }}>
            Showing {notifications.length} notification{notifications.length !== 1 ? 's' : ''}
          </span>
        </div>

        <div>
          {loading ? (
            <div style={{ padding: 48, textAlign: 'center' }} className="text-muted">
              Loading notification feed...
            </div>
          ) : notifications.length === 0 ? (
            <div style={{ padding: 48, textAlign: 'center' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: 10 }}>🎉</div>
              <h3 style={{ margin: 0, fontWeight: 700 }}>All Caught Up!</h3>
              <p className="text-muted" style={{ margin: '6px 0 0 0', fontSize: '0.9rem' }}>
                You have no notifications matching your active filters.
              </p>
            </div>
          ) : (
            notifications.map((n) => {
              const prioStyle = getPriorityStyle(n.priority)
              const isSelected = selectedIds.includes(n.id)

              return (
                <div
                  key={n.id}
                  style={{
                    padding: '16px 20px',
                    borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: 14,
                    backgroundColor: isSelected
                      ? 'rgba(59, 130, 246, 0.1)'
                      : !n.is_read
                      ? 'rgba(255, 255, 255, 0.03)'
                      : 'transparent',
                    borderLeft: !n.is_read ? '3px solid #3b82f6' : '3px solid transparent',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleSelectOne(n.id)}
                    style={{ marginTop: 4 }}
                  />

                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span
                        style={{
                          fontSize: '0.7rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: 6,
                          backgroundColor: prioStyle.bg,
                          color: prioStyle.color,
                          border: prioStyle.border,
                        }}
                      >
                        {prioStyle.label}
                      </span>
                      <span
                        style={{
                          fontSize: '0.7rem',
                          textTransform: 'uppercase',
                          fontWeight: 600,
                          padding: '2px 6px',
                          borderRadius: 4,
                          backgroundColor: 'rgba(255, 255, 255, 0.08)',
                          color: '#94a3b8',
                        }}
                      >
                        {n.category}
                      </span>
                      <span className="text-muted" style={{ fontSize: '0.78rem', marginLeft: 'auto' }}>
                        {new Date(n.created_at).toLocaleString([], {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>

                    <h4
                      style={{
                        margin: '4px 0 6px 0',
                        fontSize: '0.98rem',
                        fontWeight: n.is_read ? 600 : 800,
                        color: n.is_read ? '#cbd5e1' : '#ffffff',
                      }}
                    >
                      {n.title}
                    </h4>

                    <p
                      className="text-muted"
                      style={{
                        margin: 0,
                        fontSize: '0.88rem',
                        lineHeight: 1.45,
                        color: '#94a3b8',
                      }}
                    >
                      {n.message}
                    </p>

                    {n.link && (
                      <div style={{ marginTop: 8 }}>
                        {n.link.startsWith('/') ? (
                          <Link
                            to={n.link}
                            style={{
                              color: '#60a5fa',
                              fontSize: '0.84rem',
                              fontWeight: 600,
                              textDecoration: 'underline',
                            }}
                          >
                            View Details →
                          </Link>
                        ) : (
                          <a
                            href={n.link}
                            target="_blank"
                            rel="noreferrer"
                            style={{
                              color: '#60a5fa',
                              fontSize: '0.84rem',
                              fontWeight: 600,
                              textDecoration: 'underline',
                            }}
                          >
                            Open Link ↗
                          </a>
                        )}
                      </div>
                    )}
                  </div>

                  <button
                    onClick={() => handleDeleteOne(n.id)}
                    title="Dismiss Notification"
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#64748b',
                      cursor: 'pointer',
                      fontSize: '1rem',
                      padding: 4,
                    }}
                  >
                    ✕
                  </button>
                </div>
              )
            })
          )}
        </div>
      </div>

      {/* Preferences Modal */}
      {showPreferencesModal && preferences && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
          }}
        >
          <div className="card" style={{ width: '100%', maxWidth: 540, padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800 }}>Notification Delivery Settings</h3>
              <button
                type="button"
                onClick={() => setShowPreferencesModal(false)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '1.2rem' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSavePreferences}>
              <h4 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', color: '#60a5fa' }}>Delivery Channels</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem' }}>
                  <input
                    type="checkbox"
                    checked={preferences.in_app_enabled}
                    onChange={(e) => setPreferences({ ...preferences, in_app_enabled: e.target.checked })}
                  />
                  <span>In-App Center</span>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem' }}>
                  <input
                    type="checkbox"
                    checked={preferences.email_enabled}
                    onChange={(e) => setPreferences({ ...preferences, email_enabled: e.target.checked })}
                  />
                  <span>Email Notifications</span>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem' }}>
                  <input
                    type="checkbox"
                    checked={preferences.push_enabled}
                    onChange={(e) => setPreferences({ ...preferences, push_enabled: e.target.checked })}
                  />
                  <span>Web Push</span>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem' }}>
                  <input
                    type="checkbox"
                    checked={preferences.sms_enabled}
                    onChange={(e) => setPreferences({ ...preferences, sms_enabled: e.target.checked })}
                  />
                  <span>SMS Alerts</span>
                </label>
              </div>

              <h4 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', color: '#60a5fa' }}>Category Subscriptions</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem' }}>
                  <input
                    type="checkbox"
                    checked={preferences.notify_academic}
                    onChange={(e) => setPreferences({ ...preferences, notify_academic: e.target.checked })}
                  />
                  <span>Course & Materials</span>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem' }}>
                  <input
                    type="checkbox"
                    checked={preferences.notify_deadlines}
                    onChange={(e) => setPreferences({ ...preferences, notify_deadlines: e.target.checked })}
                  />
                  <span>Assignment Deadlines</span>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem' }}>
                  <input
                    type="checkbox"
                    checked={preferences.notify_grades}
                    onChange={(e) => setPreferences({ ...preferences, notify_grades: e.target.checked })}
                  />
                  <span>Grade Publications</span>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem' }}>
                  <input
                    type="checkbox"
                    checked={preferences.notify_announcements}
                    onChange={(e) => setPreferences({ ...preferences, notify_announcements: e.target.checked })}
                  />
                  <span>Campus Announcements</span>
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem' }}>
                  <input
                    type="checkbox"
                    checked={preferences.notify_messages}
                    onChange={(e) => setPreferences({ ...preferences, notify_messages: e.target.checked })}
                  />
                  <span>Direct Messages</span>
                </label>
              </div>

              <h4 style={{ margin: '0 0 10px 0', fontSize: '0.9rem', color: '#60a5fa' }}>Quiet Hours (Mute Non-Urgent)</h4>
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem', marginBottom: 8 }}>
                  <input
                    type="checkbox"
                    checked={preferences.quiet_hours_enabled}
                    onChange={(e) => setPreferences({ ...preferences, quiet_hours_enabled: e.target.checked })}
                  />
                  <span>Enable Quiet Hours</span>
                </label>

                {preferences.quiet_hours_enabled && (
                  <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginTop: 8 }}>
                    <div>
                      <span className="text-muted" style={{ fontSize: '0.75rem' }}>Start Time</span>
                      <input
                        type="time"
                        className="form-control"
                        value={preferences.quiet_hours_start || '22:00'}
                        onChange={(e) => setPreferences({ ...preferences, quiet_hours_start: e.target.value })}
                      />
                    </div>
                    <div>
                      <span className="text-muted" style={{ fontSize: '0.75rem' }}>End Time</span>
                      <input
                        type="time"
                        className="form-control"
                        value={preferences.quiet_hours_end || '07:00'}
                        onChange={(e) => setPreferences({ ...preferences, quiet_hours_end: e.target.value })}
                      />
                    </div>
                  </div>
                )}
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowPreferencesModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={savingPrefs}>
                  {savingPrefs ? 'Saving...' : 'Save Preferences'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Broadcast Modal (Staff / Admin) */}
      {showBroadcastModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
          }}
        >
          <div className="card" style={{ width: '100%', maxWidth: 540, padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800 }}>Broadcast Campus Notification</h3>
              <button
                type="button"
                onClick={() => setShowBroadcastModal(false)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '1.2rem' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSendBroadcast}>
              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Title *
                </label>
                <input
                  type="text"
                  placeholder="e.g. Campus Network Maintenance Tonight"
                  className="form-control"
                  value={bTitle}
                  onChange={(e) => setBTitle(e.target.value)}
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
                    value={bCategory}
                    onChange={(e) => setBCategory(e.target.value)}
                  >
                    <option value="announcement">Announcement</option>
                    <option value="academic">Academic</option>
                    <option value="deadline">Deadline</option>
                    <option value="system">System Notice</option>
                    <option value="finance">Finance</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                    Priority
                  </label>
                  <select
                    className="form-control"
                    value={bPriority}
                    onChange={(e) => setBPriority(e.target.value)}
                  >
                    <option value="normal">Normal</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                    Target Audience
                  </label>
                  <select
                    className="form-control"
                    value={bTargetRole}
                    onChange={(e) => setBTargetRole(e.target.value)}
                  >
                    <option value="">All Users</option>
                    <option value="student">Students Only</option>
                    <option value="lecturer">Lecturers Only</option>
                    <option value="admin">Administrators</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                    Link URL (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="/news or https://..."
                    className="form-control"
                    value={bLink}
                    onChange={(e) => setBLink(e.target.value)}
                  />
                </div>
              </div>

              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Message Content *
                </label>
                <textarea
                  className="form-control"
                  rows={4}
                  placeholder="Type the broadcast message..."
                  value={bMessage}
                  onChange={(e) => setBMessage(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowBroadcastModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={broadcasting}>
                  {broadcasting ? 'Broadcasting...' : 'Send Broadcast'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
