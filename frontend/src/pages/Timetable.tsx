import React, { useState, useEffect } from 'react'
import api from '@/api/client'
import { useAuth } from '@/contexts/AuthContext'
import { StudentTimetableData, TimetableSlot } from '@/types'
import toast from 'react-hot-toast'

export default function Timetable() {
  const { user } = useAuth()
  const [data, setData] = useState<StudentTimetableData | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedDay, setSelectedDay] = useState<number | 'all'>('all')
  const [showAddModal, setShowAddModal] = useState(false)
  const [newSlot, setNewSlot] = useState({
    title: '',
    slot_type: 'lecture',
    day_of_week: 0,
    start_time: '09:00',
    end_time: '11:00',
    room: '',
    building: '',
    color: '#4F46E5',
    notes: '',
    allow_conflicts: false,
  })

  const fetchTimetable = async () => {
    try {
      setLoading(true)
      const res = await api.get<StudentTimetableData>('/timetable/student')
      setData(res.data)
    } catch {
      toast.error('Failed to load academic timetable')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTimetable()
  }, [])

  const handleExportICal = async () => {
    try {
      const response = await api.get('/timetable/ical/export', { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `timetable_${user?.username || 'student'}.ics`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      toast.success('Calendar exported! Import this file into Google/Apple Calendar.')
    } catch {
      toast.error('Failed to export iCalendar file')
    }
  }

  const handleCreateSlot = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/timetable/slots', newSlot)
      toast.success('Timetable slot created successfully')
      setShowAddModal(false)
      fetchTimetable()
    } catch (err: any) {
      if (err.response?.status === 409) {
        toast.error('Conflict detected! Room or instructor is already booked at this time.')
      } else {
        toast.error(err.response?.data?.detail || 'Failed to create slot')
      }
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center" style={{ height: 320 }}>
        <div className="spinner" />
      </div>
    )
  }

  const daysToShow =
    selectedDay === 'all'
      ? data?.schedule || []
      : data?.schedule.filter((d) => d.day_of_week === selectedDay) || []

  return (
    <div className="fade-in">
      {/* Header */}
      <div className="flex justify-between items-center mb-24 flex-wrap gap-12">
        <div>
          <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 800 }}>📅 Academic Timetable</h1>
          <p className="text-muted text-sm" style={{ marginTop: 4 }}>
            Personalized class schedule, classroom locations, and weekly recurring lecture slots
          </p>
        </div>
        <div className="flex items-center gap-12">
          <button className="btn btn-secondary btn-sm" onClick={handleExportICal}>
            📥 Export iCal (.ics)
          </button>
          {(user?.role === 'admin' || user?.role === 'lecturer') && (
            <button className="btn btn-primary btn-sm" onClick={() => setShowAddModal(true)}>
              ➕ Add Slot
            </button>
          )}
        </div>
      </div>

      {/* Conflicts Banner */}
      {data?.conflicts_detected && data.conflicts_detected.length > 0 && (
        <div
          className="card mb-24"
          style={{
            background: 'rgba(239, 68, 68, 0.1)',
            borderColor: 'rgba(239, 68, 68, 0.4)',
          }}
        >
          <div style={{ fontWeight: 700, color: '#F87171', marginBottom: 8, fontSize: '.95rem' }}>
            ⚠️ Schedule Overlap Detected ({data.conflicts_detected.length})
          </div>
          <div className="flex flex-col gap-6 text-xs text-muted">
            {data.conflicts_detected.map((c, i) => (
              <div key={i} style={{ color: '#FCA5A5' }}>
                • {c.description}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-8 mb-20 overflow-x-auto pb-4">
        <button
          className={`btn btn-sm ${selectedDay === 'all' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setSelectedDay('all')}
        >
          All Days ({data?.total_slots || 0})
        </button>
        {data?.schedule.map((day) => (
          <button
            key={day.day_of_week}
            className={`btn btn-sm ${selectedDay === day.day_of_week ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setSelectedDay(day.day_of_week)}
          >
            {day.day_name.slice(0, 3)} ({day.slots.length})
          </button>
        ))}
      </div>

      {/* Days & Slots Grid */}
      <div className="flex flex-col gap-24">
        {daysToShow.map((day) => (
          <div key={day.day_of_week} className="card">
            <div className="flex justify-between items-center mb-16" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: 10 }}>
              <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>
                {day.day_name}
              </div>
              <span className="badge badge-info text-xs">
                {day.slots.length} {day.slots.length === 1 ? 'session' : 'sessions'}
              </span>
            </div>

            {day.slots.length === 0 ? (
              <div className="text-muted text-sm" style={{ textAlign: 'center', padding: '24px 0' }}>
                No scheduled lectures or sessions on this day.
              </div>
            ) : (
              <div className="grid-2 gap-16">
                {day.slots.map((slot) => (
                  <div
                    key={slot.id}
                    className="card"
                    style={{
                      background: 'rgba(255,255,255,0.02)',
                      borderLeft: `4px solid ${slot.color || '#4F46E5'}`,
                      padding: 16,
                    }}
                  >
                    <div className="flex justify-between items-start mb-8">
                      <div>
                        <div style={{ fontWeight: 700, fontSize: '.95rem' }}>{slot.title}</div>
                        {slot.course_code && (
                          <div className="text-xs text-muted" style={{ marginTop: 2 }}>
                            {slot.course_code} {slot.course_title ? `· ${slot.course_title}` : ''}
                          </div>
                        )}
                      </div>
                      <span className="badge badge-primary" style={{ textTransform: 'uppercase', fontSize: '.7rem' }}>
                        {slot.slot_type}
                      </span>
                    </div>

                    <div className="flex flex-col gap-6 text-xs text-muted mt-12">
                      <div className="flex items-center gap-6">
                        <span>⏰</span>
                        <span style={{ fontWeight: 600, color: '#fff' }}>
                          {slot.start_time} - {slot.end_time}
                        </span>
                        <span>({slot.recurrence_pattern})</span>
                      </div>
                      <div className="flex items-center gap-6">
                        <span>📍</span>
                        <span>
                          {slot.room} {slot.building ? `(${slot.building})` : ''}
                        </span>
                      </div>
                      {slot.lecturer_name && (
                        <div className="flex items-center gap-6">
                          <span>👨‍🏫</span>
                          <span>Instructor: {slot.lecturer_name}</span>
                        </div>
                      )}
                      {slot.notes && (
                        <div className="text-xs text-muted" style={{ marginTop: 6, fontStyle: 'italic' }}>
                          Note: {slot.notes}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Add Slot Modal */}
      {showAddModal && (
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
          <div className="card" style={{ maxWidth: 500, width: '100%', maxHeight: '90vh', overflowY: 'auto' }}>
            <div className="flex justify-between items-center mb-16">
              <div style={{ fontWeight: 700, fontSize: '1.2rem' }}>Add Timetable Slot</div>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowAddModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateSlot} className="flex flex-col gap-12">
              <div>
                <label className="text-xs text-muted block mb-4">Slot Title</label>
                <input
                  type="text"
                  required
                  className="input w-full"
                  placeholder="e.g. CS101 Lecture"
                  value={newSlot.title}
                  onChange={(e) => setNewSlot({ ...newSlot, title: e.target.value })}
                />
              </div>

              <div className="grid-2 gap-12">
                <div>
                  <label className="text-xs text-muted block mb-4">Day of Week</label>
                  <select
                    className="input w-full"
                    value={newSlot.day_of_week}
                    onChange={(e) => setNewSlot({ ...newSlot, day_of_week: parseInt(e.target.value) })}
                  >
                    <option value={0}>Monday</option>
                    <option value={1}>Tuesday</option>
                    <option value={2}>Wednesday</option>
                    <option value={3}>Thursday</option>
                    <option value={4}>Friday</option>
                    <option value={5}>Saturday</option>
                    <option value={6}>Sunday</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-muted block mb-4">Type</label>
                  <select
                    className="input w-full"
                    value={newSlot.slot_type}
                    onChange={(e) => setNewSlot({ ...newSlot, slot_type: e.target.value })}
                  >
                    <option value="lecture">Lecture</option>
                    <option value="lab">Lab</option>
                    <option value="tutorial">Tutorial</option>
                    <option value="workshop">Workshop</option>
                    <option value="exam">Exam</option>
                  </select>
                </div>
              </div>

              <div className="grid-2 gap-12">
                <div>
                  <label className="text-xs text-muted block mb-4">Start Time (HH:MM)</label>
                  <input
                    type="time"
                    required
                    className="input w-full"
                    value={newSlot.start_time}
                    onChange={(e) => setNewSlot({ ...newSlot, start_time: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-xs text-muted block mb-4">End Time (HH:MM)</label>
                  <input
                    type="time"
                    required
                    className="input w-full"
                    value={newSlot.end_time}
                    onChange={(e) => setNewSlot({ ...newSlot, end_time: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid-2 gap-12">
                <div>
                  <label className="text-xs text-muted block mb-4">Room</label>
                  <input
                    type="text"
                    required
                    className="input w-full"
                    placeholder="e.g. Hall A"
                    value={newSlot.room}
                    onChange={(e) => setNewSlot({ ...newSlot, room: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-xs text-muted block mb-4">Building</label>
                  <input
                    type="text"
                    className="input w-full"
                    placeholder="e.g. Computing Wing"
                    value={newSlot.building}
                    onChange={(e) => setNewSlot({ ...newSlot, building: e.target.value })}
                  />
                </div>
              </div>

              <div className="flex items-center gap-8 mt-8">
                <input
                  type="checkbox"
                  id="allow_conflicts"
                  checked={newSlot.allow_conflicts}
                  onChange={(e) => setNewSlot({ ...newSlot, allow_conflicts: e.target.checked })}
                />
                <label htmlFor="allow_conflicts" className="text-xs text-muted">
                  Allow room/instructor schedule override (bypass collision warning)
                </label>
              </div>

              <div className="flex justify-end gap-12 mt-16">
                <button type="button" className="btn btn-ghost" onClick={() => setShowAddModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save Schedule Slot
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
