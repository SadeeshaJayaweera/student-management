import React, { useEffect, useState } from 'react'
import api from '@/api/client'
import toast from 'react-hot-toast'
import type {
  HostelBuilding,
  HostelRoom,
  HostelAllocation,
  HostelMaintenanceRequest,
  HostelOccupancySummary,
} from '@/types'
import { useAuth } from '@/contexts/AuthContext'

export default function Hostels() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<'buildings' | 'allocations' | 'maintenance'>('buildings')
  const [summary, setSummary] = useState<HostelOccupancySummary | null>(null)
  const [buildings, setBuildings] = useState<HostelBuilding[]>([])
  const [selectedBuilding, setSelectedBuilding] = useState<HostelBuilding | null>(null)
  const [rooms, setRooms] = useState<HostelRoom[]>([])
  const [allocations, setAllocations] = useState<HostelAllocation[]>([])
  const [myAllocation, setMyAllocation] = useState<HostelAllocation | null>(null)
  const [maintenanceRequests, setMaintenanceRequests] = useState<HostelMaintenanceRequest[]>([])
  const [loading, setLoading] = useState(true)

  // Filters
  const [roomFilterBuilding, setRoomFilterBuilding] = useState<string>('')
  const [roomFilterType, setRoomFilterType] = useState<string>('')
  const [roomFilterStatus, setRoomFilterStatus] = useState<string>('')

  // Modals
  const [showBuildingModal, setShowBuildingModal] = useState(false)
  const [showRoomModal, setShowRoomModal] = useState(false)
  const [showAllocationModal, setShowAllocationModal] = useState(false)
  const [showMaintenanceModal, setShowMaintenanceModal] = useState(false)

  // Building form
  const [newBldgName, setNewBldgName] = useState('')
  const [newBldgCode, setNewBldgCode] = useState('')
  const [newBldgGender, setNewBldgGender] = useState('mixed')
  const [newBldgFloors, setNewBldgFloors] = useState(4)
  const [newBldgWarden, setNewBldgWarden] = useState('')
  const [newBldgContact, setNewBldgContact] = useState('')
  const [newBldgLocation, setNewBldgLocation] = useState('')

  // Room form
  const [newRoomBldgId, setNewRoomBldgId] = useState<number>(0)
  const [newRoomNumber, setNewRoomNumber] = useState('')
  const [newRoomFloor, setNewRoomFloor] = useState(1)
  const [newRoomType, setNewRoomType] = useState('double')
  const [newRoomCapacity, setNewRoomCapacity] = useState(2)
  const [newRoomFee, setNewRoomFee] = useState(18000)

  // Allocation form
  const [allocStudentId, setAllocStudentId] = useState<number>(0)
  const [allocRoomId, setAllocRoomId] = useState<number>(0)
  const [allocYear, setAllocYear] = useState('2025/2026')
  const [allocSemester, setAllocSemester] = useState(1)
  const [allocCheckIn, setAllocCheckIn] = useState(new Date().toISOString().split('T')[0])
  const [allocEmergency, setAllocEmergency] = useState('')

  // Maintenance form
  const [maintRoomId, setMaintRoomId] = useState<number>(0)
  const [maintIssueType, setMaintIssueType] = useState('plumbing')
  const [maintDesc, setMaintDesc] = useState('')
  const [maintPriority, setMaintPriority] = useState('medium')

  const fetchSummary = async () => {
    try {
      const res = await api.get<HostelOccupancySummary>('/hostels/summary')
      setSummary(res.data)
    } catch {
      // Ignore
    }
  }

  const fetchBuildings = async () => {
    try {
      const res = await api.get<HostelBuilding[]>('/hostels/buildings')
      setBuildings(res.data)
      if (res.data.length > 0 && !selectedBuilding) {
        setSelectedBuilding(res.data[0])
        setNewRoomBldgId(res.data[0].id)
      }
    } catch {
      // Ignore
    }
  }

  const fetchRooms = async () => {
    try {
      const params = new URLSearchParams()
      if (roomFilterBuilding) params.set('building_id', roomFilterBuilding)
      if (roomFilterType) params.set('room_type', roomFilterType)
      if (roomFilterStatus) params.set('status_filter', roomFilterStatus)
      const res = await api.get<HostelRoom[]>(`/hostels/rooms?${params}`)
      setRooms(res.data)
    } catch {
      // Ignore
    }
  }

  const fetchAllocations = async () => {
    try {
      if (user?.role === 'student') {
        const resMy = await api.get<HostelAllocation | null>('/hostels/allocations/my')
        setMyAllocation(resMy.data)
      }
      const res = await api.get<HostelAllocation[]>('/hostels/allocations')
      setAllocations(res.data)
    } catch {
      // Ignore
    }
  }

  const fetchMaintenance = async () => {
    try {
      const res = await api.get<HostelMaintenanceRequest[]>('/hostels/maintenance')
      setMaintenanceRequests(res.data)
    } catch {
      // Ignore
    }
  }

  const refreshAll = async () => {
    setLoading(true)
    await Promise.all([fetchSummary(), fetchBuildings(), fetchRooms(), fetchAllocations(), fetchMaintenance()])
    setLoading(false)
  }

  useEffect(() => {
    refreshAll()
  }, [])

  useEffect(() => {
    fetchRooms()
  }, [roomFilterBuilding, roomFilterType, roomFilterStatus])

  // Handlers
  const handleCreateBuilding = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/hostels/buildings', {
        name: newBldgName.trim(),
        code: newBldgCode.trim().toUpperCase(),
        gender_type: newBldgGender,
        total_floors: Number(newBldgFloors),
        warden_name: newBldgWarden.trim(),
        warden_contact: newBldgContact.trim(),
        campus_location: newBldgLocation.trim(),
        amenities: ['High-speed Wi-Fi', 'Study Lounges', 'Laundry Facility', '24/7 Security'],
      })
      toast.success('🏢 Residence hall registered successfully!')
      setShowBuildingModal(false)
      setNewBldgName('')
      setNewBldgCode('')
      setNewBldgWarden('')
      setNewBldgContact('')
      setNewBldgLocation('')
      refreshAll()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to create building')
    }
  }

  const handleCreateRoom = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newRoomBldgId) {
      toast.error('Please select a building')
      return
    }
    try {
      await api.post('/hostels/rooms', {
        building_id: Number(newRoomBldgId),
        room_number: newRoomNumber.trim(),
        floor: Number(newRoomFloor),
        room_type: newRoomType,
        capacity: Number(newRoomCapacity),
        monthly_fee: Number(newRoomFee),
        status: 'available',
      })
      toast.success('🛏️ Room registered successfully!')
      setShowRoomModal(false)
      setNewRoomNumber('')
      fetchRooms()
      fetchBuildings()
      fetchSummary()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to create room')
    }
  }

  const handleCreateAllocation = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!allocStudentId || !allocRoomId) {
      toast.error('Please specify student ID and room ID')
      return
    }
    try {
      await api.post('/hostels/allocations', {
        student_id: Number(allocStudentId),
        room_id: Number(allocRoomId),
        academic_year: allocYear,
        semester: Number(allocSemester),
        check_in_date: allocCheckIn,
        emergency_contact: allocEmergency.trim() || undefined,
        deposit_paid: 25000.0,
      })
      toast.success('🎉 Student successfully allocated to room!')
      setShowAllocationModal(false)
      refreshAll()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Allocation failed')
    }
  }

  const handleCheckOut = async (allocationId: number) => {
    if (!confirm('Confirm student check-out and bed release?')) return
    try {
      await api.put(`/hostels/allocations/${allocationId}`, {
        status: 'checked_out',
        check_out_date: new Date().toISOString().split('T')[0],
      })
      toast.success('Check-out processed and bed released!')
      refreshAll()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Check-out failed')
    }
  }

  const handleCreateMaintenance = async (e: React.FormEvent) => {
    e.preventDefault()
    const targetRoomId = maintRoomId || myAllocation?.room_id
    if (!targetRoomId) {
      toast.error('Please select or specify room number')
      return
    }
    try {
      await api.post('/hostels/maintenance', {
        room_id: Number(targetRoomId),
        issue_type: maintIssueType,
        description: maintDesc.trim(),
        priority: maintPriority,
      })
      toast.success('🛠️ Maintenance ticket submitted to facility staff!')
      setShowMaintenanceModal(false)
      setMaintDesc('')
      fetchMaintenance()
      fetchSummary()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to report issue')
    }
  }

  const handleResolveMaintenance = async (reqId: number) => {
    try {
      await api.put(`/hostels/maintenance/${reqId}`, {
        status: 'resolved',
        resolution_notes: 'Repaired and inspected by NSBM campus engineering maintenance team.',
      })
      toast.success('Ticket marked as resolved!')
      fetchMaintenance()
      fetchSummary()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to resolve ticket')
    }
  }

  const isAdmin = ['admin'].includes(user?.role ?? '')

  return (
    <div className="fade-in">
      {/* Header */}
      <div className="page-header mb-24">
        <div className="flex justify-between items-center" style={{ flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div className="page-title">🏢 NSBM Halls of Residence & Accommodation</div>
            <div className="page-subtitle">Campus student residential complexes, room allocation, and facility management</div>
          </div>
          <div className="flex gap-12">
            <button className="btn btn-secondary" onClick={() => setShowMaintenanceModal(true)}>
              🛠️ Report Room Repair
            </button>
            {isAdmin && (
              <>
                <button className="btn btn-secondary" onClick={() => setShowRoomModal(true)}>
                  ➕ Add Room
                </button>
                <button className="btn btn-primary" onClick={() => setShowBuildingModal(true)}>
                  🏢 Add Residence Hall
                </button>
              </>
            )}
          </div>
        </div>

        {/* Occupancy Stats Banner */}
        {summary && (
          <div className="grid-4 mt-20" style={{ gap: 14 }}>
            <div className="card text-center" style={{ padding: '16px' }}>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: '#6C63FF' }}>
                {summary.occupancy_rate}%
              </div>
              <div className="text-xs text-muted uppercase mt-4">Campus Occupancy Rate</div>
            </div>
            <div className="card text-center" style={{ padding: '16px' }}>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: '#00D4AA' }}>
                {summary.available_beds}
              </div>
              <div className="text-xs text-muted uppercase mt-4">Available Vacant Beds</div>
            </div>
            <div className="card text-center" style={{ padding: '16px' }}>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: '#FFB347' }}>
                {summary.occupied_beds} / {summary.total_capacity}
              </div>
              <div className="text-xs text-muted uppercase mt-4">Beds Occupied</div>
            </div>
            <div className="card text-center" style={{ padding: '16px' }}>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: '#FF6B6B' }}>
                {summary.active_maintenance_issues}
              </div>
              <div className="text-xs text-muted uppercase mt-4">Pending Repairs</div>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex gap-16 mt-20" style={{ borderBottom: '1px solid var(--border)' }}>
          <button
            className={`btn btn-sm ${activeTab === 'buildings' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setActiveTab('buildings')}
            style={{ borderRadius: '6px 6px 0 0' }}
          >
            🏢 Residence Blocks & Rooms
          </button>
          <button
            className={`btn btn-sm ${activeTab === 'allocations' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setActiveTab('allocations')}
            style={{ borderRadius: '6px 6px 0 0' }}
          >
            🛏️ {user?.role === 'student' ? 'My Accommodation' : 'Student Allocations'}
          </button>
          <button
            className={`btn btn-sm ${activeTab === 'maintenance' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setActiveTab('maintenance')}
            style={{ borderRadius: '6px 6px 0 0' }}
          >
            🔧 Facility Maintenance ({maintenanceRequests.filter((m) => m.status !== 'resolved').length})
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center" style={{ height: 300 }}>
          <div className="spinner" />
        </div>
      ) : activeTab === 'buildings' ? (
        <div className="fade-in">
          {/* Buildings Overview */}
          <div className="grid-3 mb-24" style={{ gap: 16 }}>
            {buildings.map((b) => (
              <div
                key={b.id}
                className="card"
                style={{
                  border: selectedBuilding?.id === b.id ? '2px solid var(--primary)' : '1px solid var(--border)',
                  cursor: 'pointer',
                }}
                onClick={() => {
                  setSelectedBuilding(b)
                  setRoomFilterBuilding(String(b.id))
                }}
              >
                <div className="flex justify-between items-start mb-8">
                  <div>
                    <h4 style={{ margin: 0, fontWeight: 700, fontSize: '1.1rem' }}>{b.name}</h4>
                    <span className="text-xs text-muted">{b.code} · {b.campus_location}</span>
                  </div>
                  <span className={`badge ${b.gender_type === 'female' ? 'badge-info' : b.gender_type === 'male' ? 'badge-primary' : 'badge-gold'}`}>
                    {b.gender_type.toUpperCase()}
                  </span>
                </div>
                <div className="text-xs text-secondary mt-8">
                  <div>👤 Warden: {b.warden_name} ({b.warden_contact})</div>
                  <div>🏢 {b.total_floors} Floors · {b.total_rooms} Rooms</div>
                </div>
                <div className="flex justify-between items-center text-xs mt-12 pt-8" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                  <span>Occupancy: {b.occupied_beds}/{b.total_capacity} beds</span>
                  <span className="badge badge-success">{b.available_beds} Vacant</span>
                </div>
              </div>
            ))}
          </div>

          {/* Rooms Grid & Filter */}
          <div className="card mb-20" style={{ background: 'rgba(255,255,255,0.02)' }}>
            <div className="flex justify-between items-center mb-16 flex-wrap gap-12">
              <h3 style={{ margin: 0, fontWeight: 700, fontSize: '1.15rem' }}>
                🛏️ Room Roster {selectedBuilding ? `— ${selectedBuilding.name}` : ''}
              </h3>
              <div className="flex gap-12 flex-wrap">
                <select
                  className="form-control"
                  value={roomFilterBuilding}
                  onChange={(e) => setRoomFilterBuilding(e.target.value)}
                  style={{ width: 180 }}
                >
                  <option value="">All Buildings</option>
                  {buildings.map((b) => (
                    <option key={b.id} value={b.id}>{b.name}</option>
                  ))}
                </select>
                <select
                  className="form-control"
                  value={roomFilterType}
                  onChange={(e) => setRoomFilterType(e.target.value)}
                  style={{ width: 140 }}
                >
                  <option value="">All Types</option>
                  <option value="single">Single</option>
                  <option value="double">Double</option>
                  <option value="triple">Triple</option>
                  <option value="quad">Quad</option>
                </select>
                <select
                  className="form-control"
                  value={roomFilterStatus}
                  onChange={(e) => setRoomFilterStatus(e.target.value)}
                  style={{ width: 140 }}
                >
                  <option value="">All Statuses</option>
                  <option value="available">Available</option>
                  <option value="full">Full</option>
                  <option value="maintenance">Maintenance</option>
                </select>
              </div>
            </div>

            <div className="grid-4" style={{ gap: 14 }}>
              {rooms.map((r) => {
                const isFull = r.occupied_count >= r.capacity
                return (
                  <div
                    key={r.id}
                    className="card"
                    style={{
                      padding: 14,
                      background: r.status === 'maintenance' ? 'rgba(255,107,107,0.08)' : 'rgba(255,255,255,0.03)',
                      borderColor: r.status === 'maintenance' ? 'rgba(255,107,107,0.3)' : 'var(--border)',
                    }}
                  >
                    <div className="flex justify-between items-center mb-8">
                      <span style={{ fontWeight: 800, fontSize: '1.1rem' }}>Room {r.room_number}</span>
                      <span
                        className={`badge ${
                          r.status === 'maintenance'
                            ? 'badge-danger'
                            : isFull
                            ? 'badge-secondary'
                            : 'badge-success'
                        }`}
                      >
                        {r.status === 'maintenance' ? 'Under Repair' : isFull ? 'Full' : 'Vacant'}
                      </span>
                    </div>
                    <div className="text-xs text-muted mb-4">{r.building_name || 'Building'} · Floor {r.floor}</div>
                    <div className="text-xs text-secondary mb-8">
                      Type: <span style={{ textTransform: 'capitalize', fontWeight: 600 }}>{r.room_type}</span> ({r.capacity} bed)
                    </div>
                    <div className="text-xs mb-8">
                      Occupancy: <strong>{r.occupied_count} / {r.capacity}</strong>
                    </div>
                    <div className="flex justify-between items-center pt-8 text-xs text-muted" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                      <span>LKR {r.monthly_fee.toLocaleString()}/mo</span>
                      {isAdmin && !isFull && r.status !== 'maintenance' && (
                        <button
                          className="btn btn-primary btn-xs"
                          onClick={() => {
                            setAllocRoomId(r.id)
                            setShowAllocationModal(true)
                          }}
                        >
                          Allocate
                        </button>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      ) : activeTab === 'allocations' ? (
        <div className="fade-in">
          {/* Student's Personal Allocation (if student) */}
          {user?.role === 'student' && (
            <div className="card mb-24" style={{ background: 'linear-gradient(135deg, rgba(108,99,255,.15), rgba(0,212,170,.05))' }}>
              <h3 style={{ fontWeight: 700, fontSize: '1.25rem', marginBottom: 12 }}>
                🏠 Your Current Campus Residence
              </h3>
              {myAllocation ? (
                <div className="grid-3" style={{ gap: 16 }}>
                  <div>
                    <div className="text-xs text-muted">Building & Room</div>
                    <div style={{ fontWeight: 700, fontSize: '1.15rem' }}>
                      {myAllocation.building_name} — Room {myAllocation.room_number}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-muted">Academic Term & Check-In</div>
                    <div style={{ fontWeight: 600 }}>
                      {myAllocation.academic_year} (Sem {myAllocation.semester}) · {new Date(myAllocation.check_in_date).toLocaleDateString()}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-muted">Allocation Status</div>
                    <span className="badge badge-success">ACTIVE RESIDENT</span>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted">
                  You are not currently allocated a campus hostel room for this semester. To apply or request housing, please consult the Student Affairs & Housing Office.
                </p>
              )}
            </div>
          )}

          {/* Allocation Records Table */}
          <div className="card">
            <div className="flex justify-between items-center mb-16">
              <h3 style={{ margin: 0, fontWeight: 700 }}>🛏️ Campus Housing Allocations</h3>
              {isAdmin && (
                <button className="btn btn-primary btn-sm" onClick={() => setShowAllocationModal(true)}>
                  ➕ Assign Bed
                </button>
              )}
            </div>
            <div className="table-responsive">
              <table className="table">
                <thead>
                  <tr>
                    <th>Student</th>
                    <th>Building / Room</th>
                    <th>Term</th>
                    <th>Check In</th>
                    <th>Check Out</th>
                    <th>Status</th>
                    {isAdmin && <th>Actions</th>}
                  </tr>
                </thead>
                <tbody>
                  {allocations.map((a) => (
                    <tr key={a.id}>
                      <td style={{ fontWeight: 600 }}>
                        {a.student_name || `Student #${a.student_id}`}
                        {a.student_reg_number && <span className="text-xs text-muted block">{a.student_reg_number}</span>}
                      </td>
                      <td>{a.building_name} - Room {a.room_number}</td>
                      <td className="text-sm">{a.academic_year} (S{a.semester})</td>
                      <td className="text-sm">{new Date(a.check_in_date).toLocaleDateString()}</td>
                      <td className="text-sm">{a.check_out_date ? new Date(a.check_out_date).toLocaleDateString() : '—'}</td>
                      <td>
                        <span className={`badge ${a.status === 'active' ? 'badge-success' : a.status === 'checked_out' ? 'badge-secondary' : 'badge-warning'}`}>
                          {a.status}
                        </span>
                      </td>
                      {isAdmin && (
                        <td>
                          {a.status === 'active' && (
                            <button className="btn btn-ghost btn-xs text-danger" onClick={() => handleCheckOut(a.id)}>
                              Check Out
                            </button>
                          )}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        /* Maintenance Tab */
        <div className="fade-in">
          <div className="card mb-20" style={{ background: 'rgba(255,255,255,0.02)' }}>
            <div className="flex justify-between items-center">
              <div>
                <h3 style={{ margin: 0, fontWeight: 700, fontSize: '1.15rem' }}>
                  🔧 Residence Maintenance & Facilities Support
                </h3>
                <p className="text-xs text-muted mt-4">
                  Log electrical, plumbing, furniture, and cleanliness requests directly to campus engineering dispatch.
                </p>
              </div>
              <button className="btn btn-primary btn-sm" onClick={() => setShowMaintenanceModal(true)}>
                ➕ Submit Request
              </button>
            </div>
          </div>

          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Building & Room</th>
                  <th>Issue Type</th>
                  <th>Description</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Reported</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {maintenanceRequests.map((m) => (
                  <tr key={m.id}>
                    <td style={{ fontWeight: 600 }}>
                      {m.building_name} - Room {m.room_number}
                    </td>
                    <td>
                      <span className="badge badge-info" style={{ textTransform: 'capitalize' }}>
                        {m.issue_type}
                      </span>
                    </td>
                    <td className="text-sm" style={{ maxWidth: 280 }}>
                      <div className="truncate">{m.description}</div>
                      {m.resolution_notes && (
                        <div className="text-xs text-muted mt-4">📝 {m.resolution_notes}</div>
                      )}
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          m.priority === 'urgent'
                            ? 'badge-danger'
                            : m.priority === 'high'
                            ? 'badge-warning'
                            : 'badge-secondary'
                        }`}
                      >
                        {m.priority.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          m.status === 'resolved'
                            ? 'badge-success'
                            : m.status === 'in_progress'
                            ? 'badge-warning'
                            : 'badge-secondary'
                        }`}
                      >
                        {m.status}
                      </span>
                    </td>
                    <td className="text-xs text-muted">
                      {new Date(m.reported_at).toLocaleDateString()}
                    </td>
                    <td>
                      {isAdmin && m.status !== 'resolved' && (
                        <button className="btn btn-success btn-xs" onClick={() => handleResolveMaintenance(m.id)}>
                          Resolve
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Building Modal */}
      {showBuildingModal && (
        <div className="modal-backdrop">
          <div className="modal-box" style={{ maxWidth: 520 }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontWeight: 700 }}>🏢 Add Residence Complex</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowBuildingModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateBuilding}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <label className="text-xs text-muted mb-4 block">Building Name *</label>
                  <input
                    className="form-control w-full"
                    placeholder="e.g. Lavender Student Residence"
                    value={newBldgName}
                    onChange={(e) => setNewBldgName(e.target.value)}
                    required
                  />
                </div>
                <div className="grid-2" style={{ gap: 12 }}>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Building Code *</label>
                    <input
                      className="form-control w-full"
                      placeholder="e.g. BLD-LAV"
                      value={newBldgCode}
                      onChange={(e) => setNewBldgCode(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Gender Restriction</label>
                    <select className="form-control w-full" value={newBldgGender} onChange={(e) => setNewBldgGender(e.target.value)}>
                      <option value="mixed">Co-ed / Mixed</option>
                      <option value="male">Male Only</option>
                      <option value="female">Female Only</option>
                    </select>
                  </div>
                </div>
                <div className="grid-2" style={{ gap: 12 }}>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Warden Name *</label>
                    <input
                      className="form-control w-full"
                      placeholder="e.g. Mr. S. Alwis"
                      value={newBldgWarden}
                      onChange={(e) => setNewBldgWarden(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Warden Contact *</label>
                    <input
                      className="form-control w-full"
                      placeholder="e.g. +94 77 123 4567"
                      value={newBldgContact}
                      onChange={(e) => setNewBldgContact(e.target.value)}
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs text-muted mb-4 block">Campus Location *</label>
                  <input
                    className="form-control w-full"
                    placeholder="e.g. North Campus Residential Zone"
                    value={newBldgLocation}
                    onChange={(e) => setNewBldgLocation(e.target.value)}
                    required
                  />
                </div>
              </div>
              <div className="modal-footer flex justify-end gap-12 mt-16">
                <button type="button" className="btn btn-ghost" onClick={() => setShowBuildingModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create Hall</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Room Modal */}
      {showRoomModal && (
        <div className="modal-backdrop">
          <div className="modal-box" style={{ maxWidth: 520 }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontWeight: 700 }}>🛏️ Register Room</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowRoomModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateRoom}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <label className="text-xs text-muted mb-4 block">Residence Building *</label>
                  <select
                    className="form-control w-full"
                    value={newRoomBldgId}
                    onChange={(e) => setNewRoomBldgId(Number(e.target.value))}
                    required
                  >
                    {buildings.map((b) => (
                      <option key={b.id} value={b.id}>{b.name} ({b.code})</option>
                    ))}
                  </select>
                </div>
                <div className="grid-2" style={{ gap: 12 }}>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Room Number *</label>
                    <input
                      className="form-control w-full"
                      placeholder="e.g. A-204"
                      value={newRoomNumber}
                      onChange={(e) => setNewRoomNumber(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Floor</label>
                    <input
                      type="number"
                      className="form-control w-full"
                      value={newRoomFloor}
                      onChange={(e) => setNewRoomFloor(Number(e.target.value))}
                      min={0}
                    />
                  </div>
                </div>
                <div className="grid-2" style={{ gap: 12 }}>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Room Type</label>
                    <select className="form-control w-full" value={newRoomType} onChange={(e) => setNewRoomType(e.target.value)}>
                      <option value="single">Single Bed</option>
                      <option value="double">Double Sharing</option>
                      <option value="triple">Triple Sharing</option>
                      <option value="quad">Quad Bed</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Bed Capacity</label>
                    <input
                      type="number"
                      className="form-control w-full"
                      value={newRoomCapacity}
                      onChange={(e) => setNewRoomCapacity(Number(e.target.value))}
                      min={1}
                      max={10}
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs text-muted mb-4 block">Monthly Fee (LKR)</label>
                  <input
                    type="number"
                    className="form-control w-full"
                    value={newRoomFee}
                    onChange={(e) => setNewRoomFee(Number(e.target.value))}
                    min={0}
                  />
                </div>
              </div>
              <div className="modal-footer flex justify-end gap-12 mt-16">
                <button type="button" className="btn btn-ghost" onClick={() => setShowRoomModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Add Room</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Allocation Modal */}
      {showAllocationModal && (
        <div className="modal-backdrop">
          <div className="modal-box" style={{ maxWidth: 520 }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontWeight: 700 }}>🛏️ Assign Student to Room</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowAllocationModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateAllocation}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <label className="text-xs text-muted mb-4 block">Student ID Number *</label>
                  <input
                    type="number"
                    className="form-control w-full"
                    placeholder="Enter Student Database ID (e.g. 1)"
                    value={allocStudentId || ''}
                    onChange={(e) => setAllocStudentId(Number(e.target.value))}
                    required
                  />
                </div>
                <div>
                  <label className="text-xs text-muted mb-4 block">Target Room *</label>
                  <select
                    className="form-control w-full"
                    value={allocRoomId}
                    onChange={(e) => setAllocRoomId(Number(e.target.value))}
                    required
                  >
                    <option value="">Select Available Room</option>
                    {rooms.filter((r) => r.status === 'available').map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.building_name} - Room {r.room_number} ({r.occupied_count}/{r.capacity} beds)
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid-2" style={{ gap: 12 }}>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Academic Year</label>
                    <input
                      className="form-control w-full"
                      value={allocYear}
                      onChange={(e) => setAllocYear(e.target.value)}
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Semester</label>
                    <select className="form-control w-full" value={allocSemester} onChange={(e) => setAllocSemester(Number(e.target.value))}>
                      <option value={1}>Semester 1</option>
                      <option value={2}>Semester 2</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="text-xs text-muted mb-4 block">Check-In Date *</label>
                  <input
                    type="date"
                    className="form-control w-full"
                    value={allocCheckIn}
                    onChange={(e) => setAllocCheckIn(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="text-xs text-muted mb-4 block">Emergency Contact</label>
                  <input
                    className="form-control w-full"
                    placeholder="Guardian name & mobile..."
                    value={allocEmergency}
                    onChange={(e) => setAllocEmergency(e.target.value)}
                  />
                </div>
              </div>
              <div className="modal-footer flex justify-end gap-12 mt-16">
                <button type="button" className="btn btn-ghost" onClick={() => setShowAllocationModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Confirm Allocation</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Maintenance Request Modal */}
      {showMaintenanceModal && (
        <div className="modal-backdrop">
          <div className="modal-box" style={{ maxWidth: 520 }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontWeight: 700 }}>🛠️ Report Facility / Room Issue</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowMaintenanceModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateMaintenance}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <label className="text-xs text-muted mb-4 block">Room *</label>
                  <select
                    className="form-control w-full"
                    value={maintRoomId || (myAllocation ? myAllocation.room_id : '')}
                    onChange={(e) => setMaintRoomId(Number(e.target.value))}
                    required
                  >
                    <option value="">Select Room</option>
                    {rooms.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.building_name} - Room {r.room_number}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid-2" style={{ gap: 12 }}>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Issue Category</label>
                    <select className="form-control w-full" value={maintIssueType} onChange={(e) => setMaintIssueType(e.target.value)}>
                      <option value="plumbing">Plumbing / Water</option>
                      <option value="electrical">Electrical & Lighting</option>
                      <option value="furniture">Furniture / Bed</option>
                      <option value="cleanliness">Sanitation / Cleaning</option>
                      <option value="hvac">Air Conditioning / Fan</option>
                      <option value="other">Other Repairs</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Urgency / Priority</label>
                    <select className="form-control w-full" value={maintPriority} onChange={(e) => setMaintPriority(e.target.value)}>
                      <option value="low">Low Priority</option>
                      <option value="medium">Medium Priority</option>
                      <option value="high">High Priority</option>
                      <option value="urgent">Urgent</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="text-xs text-muted mb-4 block">Description of Problem *</label>
                  <textarea
                    className="form-control w-full"
                    rows={4}
                    placeholder="Describe the maintenance or repair needed in detail..."
                    value={maintDesc}
                    onChange={(e) => setMaintDesc(e.target.value)}
                    required
                  />
                </div>
              </div>
              <div className="modal-footer flex justify-end gap-12 mt-16">
                <button type="button" className="btn btn-ghost" onClick={() => setShowMaintenanceModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Submit Ticket</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
