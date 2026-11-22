import React, { useEffect, useState } from 'react'
import api from '@/api/client'
import toast from 'react-hot-toast'
import type {
  CampusFacility,
  FacilityEquipment,
  FacilityReservation,
  FacilityBookingSummary,
} from '@/types'
import { useAuth } from '@/contexts/AuthContext'

const FACILITY_ICONS: Record<string, string> = {
  auditorium: '🎭',
  lecture_hall: '🏛️',
  computer_lab: '💻',
  seminar_room: '👥',
  conference_room: '💼',
  multipurpose_hall: '🎪',
  study_pod: '🎧',
}

export default function Facilities() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<'venues' | 'bookings' | 'equipment'>('venues')
  const [summary, setSummary] = useState<FacilityBookingSummary | null>(null)
  const [facilities, setFacilities] = useState<CampusFacility[]>([])
  const [selectedFacility, setSelectedFacility] = useState<CampusFacility | null>(null)
  const [equipmentList, setEquipmentList] = useState<FacilityEquipment[]>([])
  const [reservations, setReservations] = useState<FacilityReservation[]>([])
  const [loading, setLoading] = useState(true)

  // Filter
  const [typeFilter, setTypeFilter] = useState('')

  // Modals
  const [showBookingModal, setShowBookingModal] = useState(false)
  const [showFacilityModal, setShowFacilityModal] = useState(false)
  const [showEquipmentModal, setShowEquipmentModal] = useState(false)

  // Booking Form
  const [bookFacilityId, setBookFacilityId] = useState<number>(0)
  const [bookStartTime, setBookStartTime] = useState('')
  const [bookEndTime, setBookEndTime] = useState('')
  const [bookPurpose, setBookPurpose] = useState('')
  const [bookAttendees, setBookAttendees] = useState(30)
  const [bookEquip, setBookEquip] = useState<string[]>([])
  const [submittingBooking, setSubmittingBooking] = useState(false)

  // Facility Form
  const [newFacName, setNewFacName] = useState('')
  const [newFacCode, setNewFacCode] = useState('')
  const [newFacType, setNewFacType] = useState('lecture_hall')
  const [newFacBuilding, setNewFacBuilding] = useState('')
  const [newFacFloor, setNewFacFloor] = useState(1)
  const [newFacCapacity, setNewFacCapacity] = useState(80)

  // Equipment Form
  const [newEqName, setNewEqName] = useState('')
  const [newEqTag, setNewEqTag] = useState('')
  const [newEqType, setNewEqType] = useState('av_projector')
  const [newEqFacId, setNewEqFacId] = useState<number>(0)

  const fetchSummary = async () => {
    try {
      const res = await api.get<FacilityBookingSummary>('/facilities/summary')
      setSummary(res.data)
    } catch {
      // Ignore
    }
  }

  const fetchFacilities = async () => {
    try {
      const params = new URLSearchParams()
      if (typeFilter) params.set('facility_type', typeFilter)
      const res = await api.get<CampusFacility[]>(`/facilities?${params}`)
      setFacilities(res.data)
      if (res.data.length > 0 && !selectedFacility) {
        setSelectedFacility(res.data[0])
        setBookFacilityId(res.data[0].id)
      }
    } catch {
      // Ignore
    }
  }

  const fetchEquipment = async () => {
    try {
      const res = await api.get<FacilityEquipment[]>('/facilities/equipment/all')
      setEquipmentList(res.data)
    } catch {
      // Ignore
    }
  }

  const fetchReservations = async () => {
    try {
      const endpoint = user?.role === 'student' ? '/facilities/reservations/my' : '/facilities/reservations/all'
      const res = await api.get<FacilityReservation[]>(endpoint)
      setReservations(res.data)
    } catch {
      // Ignore
    }
  }

  const refreshAll = async () => {
    setLoading(true)
    await Promise.all([fetchSummary(), fetchFacilities(), fetchEquipment(), fetchReservations()])
    setLoading(false)
  }

  useEffect(() => {
    refreshAll()
  }, [])

  useEffect(() => {
    fetchFacilities()
  }, [typeFilter])

  // Handlers
  const handleCreateReservation = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!bookFacilityId || !bookStartTime || !bookEndTime || !bookPurpose.trim()) {
      toast.error('Please complete all required reservation fields.')
      return
    }
    setSubmittingBooking(true)
    try {
      await api.post('/facilities/reservations', {
        facility_id: Number(bookFacilityId),
        start_time: bookStartTime,
        end_time: bookEndTime,
        purpose: bookPurpose.trim(),
        attendee_count: Number(bookAttendees),
        equipment_requested: bookEquip,
      })
      toast.success(
        ['admin', 'lecturer'].includes(user?.role ?? '')
          ? '🎉 Reservation confirmed on campus schedule!'
          : '📬 Reservation requested! Awaiting facility bureau approval.'
      )
      setShowBookingModal(false)
      setBookPurpose('')
      setBookStartTime('')
      setBookEndTime('')
      refreshAll()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Reservation failed due to scheduling conflict')
    } finally {
      setSubmittingBooking(false)
    }
  }

  const handleCreateFacility = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/facilities', {
        name: newFacName.trim(),
        facility_code: newFacCode.trim().toUpperCase(),
        facility_type: newFacType,
        building_name: newFacBuilding.trim(),
        floor: Number(newFacFloor),
        capacity: Number(newFacCapacity),
        amenities: ['Central Air Conditioning', 'Dual Projector Array', 'Digital Sound Stage', 'Wi-Fi 6'],
        is_active: true,
      })
      toast.success('🏛️ Facility venue registered!')
      setShowFacilityModal(false)
      setNewFacName('')
      setNewFacCode('')
      setNewFacBuilding('')
      refreshAll()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to create venue')
    }
  }

  const handleCreateEquipment = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/facilities/equipment', {
        name: newEqName.trim(),
        asset_tag: newEqTag.trim().toUpperCase(),
        equipment_type: newEqType,
        facility_id: newEqFacId ? Number(newEqFacId) : undefined,
        status: 'available',
      })
      toast.success('📽️ Equipment asset catalogued!')
      setShowEquipmentModal(false)
      setNewEqName('')
      setNewEqTag('')
      refreshAll()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to add equipment')
    }
  }

  const handleApproveReservation = async (resId: number) => {
    try {
      await api.put(`/facilities/reservations/${resId}`, {
        status: 'confirmed',
        approval_notes: 'Approved by NSBM Academic Facilities Directorate.',
      })
      toast.success('Reservation approved!')
      fetchReservations()
      fetchSummary()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Approval failed')
    }
  }

  const handleCancelReservation = async (resId: number) => {
    if (!confirm('Cancel this facility reservation?')) return
    try {
      await api.put(`/facilities/reservations/${resId}`, {
        status: 'cancelled',
      })
      toast.success('Reservation cancelled and timeslot freed.')
      fetchReservations()
      fetchSummary()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Cancellation failed')
    }
  }

  const isAdmin = ['admin'].includes(user?.role ?? '')

  return (
    <div className="fade-in">
      {/* Header */}
      <div className="page-header mb-24">
        <div className="flex justify-between items-center" style={{ flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div className="page-title">🏛️ NSBM Campus Facilities & Space Booking</div>
            <div className="page-subtitle">Auditoriums, specialized laboratories, lecture theatres, conference venues, and AV equipment</div>
          </div>
          <div className="flex gap-12">
            <button className="btn btn-primary" onClick={() => setShowBookingModal(true)}>
              📅 Reserve Space
            </button>
            {isAdmin && (
              <>
                <button className="btn btn-secondary" onClick={() => setShowEquipmentModal(true)}>
                  ➕ Add Asset
                </button>
                <button className="btn btn-secondary" onClick={() => setShowFacilityModal(true)}>
                  🏛️ Add Facility
                </button>
              </>
            )}
          </div>
        </div>

        {/* Operational Summary */}
        {summary && (
          <div className="grid-4 mt-20" style={{ gap: 14 }}>
            <div className="card text-center" style={{ padding: '16px' }}>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: '#6C63FF' }}>
                {summary.total_facilities}
              </div>
              <div className="text-xs text-muted uppercase mt-4">Total Campus Venues</div>
            </div>
            <div className="card text-center" style={{ padding: '16px' }}>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: '#00D4AA' }}>
                {summary.total_capacity.toLocaleString()}
              </div>
              <div className="text-xs text-muted uppercase mt-4">Simultaneous Seat Capacity</div>
            </div>
            <div className="card text-center" style={{ padding: '16px' }}>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: '#FFB347' }}>
                {summary.confirmed_reservations_today}
              </div>
              <div className="text-xs text-muted uppercase mt-4">Bookings Active Today</div>
            </div>
            <div className="card text-center" style={{ padding: '16px' }}>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: '#FF64C8' }}>
                {summary.pending_approvals}
              </div>
              <div className="text-xs text-muted uppercase mt-4">Pending Approvals</div>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex gap-16 mt-20" style={{ borderBottom: '1px solid var(--border)' }}>
          <button
            className={`btn btn-sm ${activeTab === 'venues' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setActiveTab('venues')}
            style={{ borderRadius: '6px 6px 0 0' }}
          >
            🏛️ Campus Venues ({facilities.length})
          </button>
          <button
            className={`btn btn-sm ${activeTab === 'bookings' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setActiveTab('bookings')}
            style={{ borderRadius: '6px 6px 0 0' }}
          >
            📅 {user?.role === 'student' ? 'My Bookings' : 'All Reservations'} ({reservations.length})
          </button>
          <button
            className={`btn btn-sm ${activeTab === 'equipment' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setActiveTab('equipment')}
            style={{ borderRadius: '6px 6px 0 0' }}
          >
            📽️ AV & Tech Assets ({equipmentList.length})
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center" style={{ height: 300 }}>
          <div className="spinner" />
        </div>
      ) : activeTab === 'venues' ? (
        <div className="fade-in">
          {/* Filters */}
          <div className="flex gap-12 mb-20" style={{ flexWrap: 'wrap' }}>
            <select
              className="form-control"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              style={{ width: 220 }}
            >
              <option value="">All Venue Types</option>
              <option value="auditorium">🎭 Auditorium</option>
              <option value="lecture_hall">🏛️ Lecture Theatres</option>
              <option value="computer_lab">💻 Computing Labs</option>
              <option value="conference_room">💼 Conference Suites</option>
              <option value="seminar_room">👥 Seminar Rooms</option>
              <option value="study_pod">🎧 Study Pods</option>
            </select>
          </div>

          <div className="grid-3" style={{ gap: 16 }}>
            {facilities.map((fac) => (
              <div key={fac.id} className="card" style={{ padding: 18, position: 'relative' }}>
                <div className="flex justify-between items-start mb-8">
                  <div>
                    <span style={{ fontSize: '2rem', marginRight: 8 }}>
                      {FACILITY_ICONS[fac.facility_type] || '🏛️'}
                    </span>
                    <h4 style={{ margin: 0, fontWeight: 800, fontSize: '1.2rem', display: 'inline' }}>
                      {fac.name}
                    </h4>
                    <div className="text-xs text-muted mt-2">{fac.facility_code}</div>
                  </div>
                  <span className="badge badge-info">
                    {fac.capacity} Persons
                  </span>
                </div>
                <div className="text-xs text-secondary mt-8">
                  <div>📍 Location: <strong>{fac.building_name} (Floor {fac.floor})</strong></div>
                  <div>🏷️ Category: <span style={{ textTransform: 'capitalize' }}>{fac.facility_type.replace('_', ' ')}</span></div>
                </div>

                {/* Amenities Badges */}
                {fac.amenities && (
                  <div className="flex gap-4 mt-12 flex-wrap">
                    {fac.amenities.map((a, i) => (
                      <span key={i} className="badge badge-secondary" style={{ fontSize: '.68rem' }}>
                        ✓ {a}
                      </span>
                    ))}
                  </div>
                )}

                <div className="flex justify-between items-center mt-16 pt-12" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                  <span className="text-xs text-muted">
                    {fac.active_reservations_count} Scheduled Runs
                  </span>
                  <button
                    className="btn btn-primary btn-xs"
                    onClick={() => {
                      setBookFacilityId(fac.id)
                      setShowBookingModal(true)
                    }}
                  >
                    Reserve Space
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : activeTab === 'bookings' ? (
        <div className="fade-in">
          <div className="card">
            <div className="flex justify-between items-center mb-16">
              <h3 style={{ margin: 0, fontWeight: 700 }}>
                📅 Scheduled Facility Reservations
              </h3>
              <button className="btn btn-primary btn-sm" onClick={() => setShowBookingModal(true)}>
                ➕ New Booking
              </button>
            </div>
            <div className="table-responsive">
              <table className="table">
                <thead>
                  <tr>
                    <th>Facility</th>
                    <th>Reserved By</th>
                    <th>Time Window</th>
                    <th>Purpose</th>
                    <th>Attendees</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {reservations.map((r) => (
                    <tr key={r.id}>
                      <td style={{ fontWeight: 700 }}>
                        {r.facility_name}
                        <span className="text-xs text-muted block">{r.facility_code}</span>
                      </td>
                      <td className="text-sm">
                        {r.reserved_by_name || `User #${r.reserved_by_user_id}`}
                        <span className="text-xs text-muted block" style={{ textTransform: 'capitalize' }}>
                          {r.reserved_by_role}
                        </span>
                      </td>
                      <td className="text-xs">
                        <div style={{ fontWeight: 600 }}>{new Date(r.start_time).toLocaleDateString()}</div>
                        <div className="text-muted">
                          {new Date(r.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} -{' '}
                          {new Date(r.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </td>
                      <td className="text-sm" style={{ maxWidth: 220 }}>
                        <div className="truncate">{r.purpose}</div>
                      </td>
                      <td className="text-sm">{r.attendee_count} pax</td>
                      <td>
                        <span
                          className={`badge ${
                            r.status === 'confirmed'
                              ? 'badge-success'
                              : r.status === 'pending'
                              ? 'badge-warning'
                              : 'badge-danger'
                          }`}
                        >
                          {r.status.toUpperCase()}
                        </span>
                      </td>
                      <td>
                        <div className="flex gap-6">
                          {['admin', 'lecturer'].includes(user?.role ?? '') && r.status === 'pending' && (
                            <button className="btn btn-success btn-xs" onClick={() => handleApproveReservation(r.id)}>
                              Approve
                            </button>
                          )}
                          {r.status !== 'cancelled' && (
                            <button className="btn btn-ghost btn-xs text-danger" onClick={() => handleCancelReservation(r.id)}>
                              Cancel
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        /* Equipment Tab */
        <div className="fade-in">
          <div className="card mb-20" style={{ background: 'rgba(255,255,255,0.02)' }}>
            <div className="flex justify-between items-center">
              <div>
                <h3 style={{ margin: 0, fontWeight: 700, fontSize: '1.15rem' }}>
                  📽️ Audio-Visual & Technical Resource Inventory
                </h3>
                <p className="text-xs text-muted mt-4">
                  Manage fixed and portable lecture hall equipment, smart podiums, microphones, and projector assets.
                </p>
              </div>
              {isAdmin && (
                <button className="btn btn-primary btn-sm" onClick={() => setShowEquipmentModal(true)}>
                  ➕ Add Asset
                </button>
              )}
            </div>
          </div>

          <div className="grid-3" style={{ gap: 16 }}>
            {equipmentList.map((eq) => (
              <div key={eq.id} className="card" style={{ padding: 16 }}>
                <div className="flex justify-between items-start mb-8">
                  <div>
                    <h4 style={{ margin: 0, fontWeight: 700, fontSize: '1.05rem' }}>{eq.name}</h4>
                    <span className="text-xs text-muted">{eq.asset_tag}</span>
                  </div>
                  <span className={`badge ${eq.status === 'available' ? 'badge-success' : 'badge-warning'}`}>
                    {eq.status.toUpperCase()}
                  </span>
                </div>
                <div className="text-xs text-secondary mt-8">
                  <div>Type: <span style={{ textTransform: 'capitalize' }}>{eq.equipment_type.replace('_', ' ')}</span></div>
                  <div>Room: {eq.facility_id ? `Assigned to Room #${eq.facility_id}` : 'Portable Tech Depot'}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Booking Modal */}
      {showBookingModal && (
        <div className="modal-backdrop">
          <div className="modal-box" style={{ maxWidth: 540 }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontWeight: 700 }}>📅 Book Campus Venue</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowBookingModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateReservation}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div>
                  <label className="text-xs text-muted mb-4 block">Target Facility / Hall *</label>
                  <select
                    className="form-control w-full"
                    value={bookFacilityId}
                    onChange={(e) => setBookFacilityId(Number(e.target.value))}
                    required
                  >
                    {facilities.map((f) => (
                      <option key={f.id} value={f.id}>
                        {f.name} ({f.building_name} · Cap: {f.capacity})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid-2" style={{ gap: 12 }}>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Start Time *</label>
                    <input
                      type="datetime-local"
                      className="form-control w-full"
                      value={bookStartTime}
                      onChange={(e) => setBookStartTime(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted mb-4 block">End Time *</label>
                    <input
                      type="datetime-local"
                      className="form-control w-full"
                      value={bookEndTime}
                      onChange={(e) => setBookEndTime(e.target.value)}
                      required
                    />
                  </div>
                </div>
                <div className="grid-2" style={{ gap: 12 }}>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Purpose of Reservation *</label>
                    <input
                      className="form-control w-full"
                      placeholder="e.g. IEEE Hackathon Finals"
                      value={bookPurpose}
                      onChange={(e) => setBookPurpose(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Attendee Count</label>
                    <input
                      type="number"
                      className="form-control w-full"
                      value={bookAttendees}
                      onChange={(e) => setBookAttendees(Number(e.target.value))}
                      min={1}
                    />
                  </div>
                </div>
              </div>
              <div className="modal-footer flex justify-end gap-12 mt-16">
                <button type="button" className="btn btn-ghost" onClick={() => setShowBookingModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={submittingBooking}>
                  {submittingBooking ? 'Checking conflicts…' : 'Confirm Reservation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Facility Modal */}
      {showFacilityModal && (
        <div className="modal-backdrop">
          <div className="modal-box" style={{ maxWidth: 520 }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontWeight: 700 }}>🏛️ Register Campus Venue</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowFacilityModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateFacility}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <label className="text-xs text-muted mb-4 block">Facility Name *</label>
                  <input
                    className="form-control w-full"
                    placeholder="e.g. Alan Turing Computing Theatre"
                    value={newFacName}
                    onChange={(e) => setNewFacName(e.target.value)}
                    required
                  />
                </div>
                <div className="grid-2" style={{ gap: 12 }}>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Facility Code *</label>
                    <input
                      className="form-control w-full"
                      placeholder="e.g. FAC-TURING-01"
                      value={newFacCode}
                      onChange={(e) => setNewFacCode(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Venue Type</label>
                    <select className="form-control w-full" value={newFacType} onChange={(e) => setNewFacType(e.target.value)}>
                      <option value="auditorium">Auditorium</option>
                      <option value="lecture_hall">Lecture Hall</option>
                      <option value="computer_lab">Computer Lab</option>
                      <option value="conference_room">Conference Room</option>
                      <option value="seminar_room">Seminar Room</option>
                      <option value="study_pod">Study Pod</option>
                    </select>
                  </div>
                </div>
                <div className="grid-2" style={{ gap: 12 }}>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Building Complex *</label>
                    <input
                      className="form-control w-full"
                      placeholder="e.g. Faculty of Computing Complex"
                      value={newFacBuilding}
                      onChange={(e) => setNewFacBuilding(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Floor</label>
                    <input
                      type="number"
                      className="form-control w-full"
                      value={newFacFloor}
                      onChange={(e) => setNewFacFloor(Number(e.target.value))}
                      min={0}
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs text-muted mb-4 block">Seating Capacity</label>
                  <input
                    type="number"
                    className="form-control w-full"
                    value={newFacCapacity}
                    onChange={(e) => setNewFacCapacity(Number(e.target.value))}
                    min={1}
                  />
                </div>
              </div>
              <div className="modal-footer flex justify-end gap-12 mt-16">
                <button type="button" className="btn btn-ghost" onClick={() => setShowFacilityModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create Facility</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Equipment Modal */}
      {showEquipmentModal && (
        <div className="modal-backdrop">
          <div className="modal-box" style={{ maxWidth: 500 }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontWeight: 700 }}>📽️ Register Technical Equipment</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowEquipmentModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateEquipment}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <label className="text-xs text-muted mb-4 block">Asset Name *</label>
                  <input
                    className="form-control w-full"
                    placeholder="e.g. 4K Ultra-Short Throw Laser Projector"
                    value={newEqName}
                    onChange={(e) => setNewEqName(e.target.value)}
                    required
                  />
                </div>
                <div className="grid-2" style={{ gap: 12 }}>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Barcode / Asset Tag *</label>
                    <input
                      className="form-control w-full"
                      placeholder="e.g. EQ-PRJ-892"
                      value={newEqTag}
                      onChange={(e) => setNewEqTag(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Equipment Category</label>
                    <select className="form-control w-full" value={newEqType} onChange={(e) => setNewEqType(e.target.value)}>
                      <option value="av_projector">Projector System</option>
                      <option value="wireless_mic">Wireless Mic Kit</option>
                      <option value="smart_lectern">Smart Digital Lectern</option>
                      <option value="laptop_cart">Mobile Laptop Cart</option>
                      <option value="sound_mixer">Audio Console Mixer</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="text-xs text-muted mb-4 block">Default Assigned Venue (Optional)</label>
                  <select
                    className="form-control w-full"
                    value={newEqFacId}
                    onChange={(e) => setNewEqFacId(Number(e.target.value))}
                  >
                    <option value="">Portable Technical Pool</option>
                    {facilities.map((f) => (
                      <option key={f.id} value={f.id}>{f.name} ({f.facility_code})</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="modal-footer flex justify-end gap-12 mt-16">
                <button type="button" className="btn btn-ghost" onClick={() => setShowEquipmentModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Add Equipment</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
