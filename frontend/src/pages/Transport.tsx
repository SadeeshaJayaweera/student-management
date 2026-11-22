import React, { useEffect, useState } from 'react'
import api from '@/api/client'
import toast from 'react-hot-toast'
import type {
  TransportVehicle,
  ShuttleRoute,
  ShuttleSchedule,
  StudentTransportPass,
  TransportFleetSummary,
} from '@/types'
import { useAuth } from '@/contexts/AuthContext'

export default function Transport() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<'routes' | 'passes' | 'fleet'>('routes')
  const [summary, setSummary] = useState<TransportFleetSummary | null>(null)
  const [routes, setRoutes] = useState<ShuttleRoute[]>([])
  const [selectedRoute, setSelectedRoute] = useState<ShuttleRoute | null>(null)
  const [vehicles, setVehicles] = useState<TransportVehicle[]>([])
  const [passes, setPasses] = useState<StudentTransportPass[]>([])
  const [myPass, setMyPass] = useState<StudentTransportPass | null>(null)
  const [loading, setLoading] = useState(true)

  // Modals
  const [showVehicleModal, setShowVehicleModal] = useState(false)
  const [showRouteModal, setShowRouteModal] = useState(false)
  const [showScheduleModal, setShowScheduleModal] = useState(false)
  const [showPassModal, setShowPassModal] = useState(false)

  // Vehicle form
  const [newVehNum, setNewVehNum] = useState('')
  const [newVehType, setNewVehType] = useState('bus')
  const [newVehCapacity, setNewVehCapacity] = useState(54)
  const [newVehDriver, setNewVehDriver] = useState('')
  const [newVehContact, setNewVehContact] = useState('')

  // Route form
  const [newRouteName, setNewRouteName] = useState('')
  const [newRouteCode, setNewRouteCode] = useState('')
  const [newRouteOrigin, setNewRouteOrigin] = useState('')
  const [newRouteDest, setNewRouteDest] = useState('NSBM Green University, Homagama')
  const [newRouteDist, setNewRouteDist] = useState(28.5)
  const [newRouteDuration, setNewRouteDuration] = useState(50)
  const [newRouteFare, setNewRouteFare] = useState(150)

  // Schedule form
  const [newSchedRouteId, setNewSchedRouteId] = useState<number>(0)
  const [newSchedVehId, setNewSchedVehId] = useState<number>(0)
  const [newSchedDep, setNewSchedDep] = useState('07:15')
  const [newSchedArr, setNewSchedArr] = useState('08:15')
  const [newSchedShift, setNewSchedShift] = useState('morning_inbound')

  // Pass form
  const [newPassStudentId, setNewPassStudentId] = useState<number>(0)
  const [newPassRouteId, setNewPassRouteId] = useState<number>(0)
  const [newPassType, setNewPassType] = useState('semester')
  const [newPassValidFrom, setNewPassValidFrom] = useState(new Date().toISOString().split('T')[0])
  const [newPassValidUntil, setNewPassValidUntil] = useState('2027-06-30')
  const [newPassFare, setNewPassFare] = useState(12000)

  const fetchSummary = async () => {
    try {
      const res = await api.get<TransportFleetSummary>('/transport/summary')
      setSummary(res.data)
    } catch {
      // Ignore
    }
  }

  const fetchRoutes = async () => {
    try {
      const res = await api.get<ShuttleRoute[]>('/transport/routes')
      setRoutes(res.data)
      if (res.data.length > 0 && !selectedRoute) {
        setSelectedRoute(res.data[0])
        setNewSchedRouteId(res.data[0].id)
        setNewPassRouteId(res.data[0].id)
      }
    } catch {
      // Ignore
    }
  }

  const fetchVehicles = async () => {
    try {
      const res = await api.get<TransportVehicle[]>('/transport/vehicles')
      setVehicles(res.data)
      if (res.data.length > 0 && !newSchedVehId) {
        setNewSchedVehId(res.data[0].id)
      }
    } catch {
      // Ignore
    }
  }

  const fetchPasses = async () => {
    try {
      if (user?.role === 'student') {
        const resMy = await api.get<StudentTransportPass | null>('/transport/passes/my')
        setMyPass(resMy.data)
      }
      const res = await api.get<StudentTransportPass[]>('/transport/passes')
      setPasses(res.data)
    } catch {
      // Ignore
    }
  }

  const refreshAll = async () => {
    setLoading(true)
    await Promise.all([fetchSummary(), fetchRoutes(), fetchVehicles(), fetchPasses()])
    setLoading(false)
  }

  useEffect(() => {
    refreshAll()
  }, [])

  // Handlers
  const handleCreateVehicle = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/transport/vehicles', {
        vehicle_number: newVehNum.trim().toUpperCase(),
        vehicle_type: newVehType,
        capacity: Number(newVehCapacity),
        driver_name: newVehDriver.trim(),
        driver_contact: newVehContact.trim(),
        status: 'active',
      })
      toast.success('🚌 Fleet vehicle registered!')
      setShowVehicleModal(false)
      setNewVehNum('')
      setNewVehDriver('')
      setNewVehContact('')
      refreshAll()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to add vehicle')
    }
  }

  const handleCreateRoute = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.post('/transport/routes', {
        route_name: newRouteName.trim(),
        route_code: newRouteCode.trim().toUpperCase(),
        origin: newRouteOrigin.trim(),
        destination: newRouteDest.trim(),
        distance_km: Number(newRouteDist),
        estimated_duration_mins: Number(newRouteDuration),
        fare_amount: Number(newRouteFare),
        is_active: true,
      })
      toast.success('🗺️ Shuttle route established!')
      setShowRouteModal(false)
      setNewRouteName('')
      setNewRouteCode('')
      setNewRouteOrigin('')
      refreshAll()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to add route')
    }
  }

  const handleCreateSchedule = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newSchedRouteId) {
      toast.error('Please select route')
      return
    }
    try {
      await api.post('/transport/schedules', {
        route_id: Number(newSchedRouteId),
        vehicle_id: newSchedVehId ? Number(newSchedVehId) : undefined,
        departure_time: newSchedDep,
        arrival_time: newSchedArr,
        days_of_week: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
        shift_type: newSchedShift,
        is_active: true,
      })
      toast.success('⏰ Timetable trip added!')
      setShowScheduleModal(false)
      refreshAll()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to schedule trip')
    }
  }

  const handleCreatePass = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newPassStudentId || !newPassRouteId) {
      toast.error('Please specify student and route')
      return
    }
    try {
      await api.post('/transport/passes', {
        student_id: Number(newPassStudentId),
        route_id: Number(newPassRouteId),
        pass_type: newPassType,
        valid_from: newPassValidFrom,
        valid_until: newPassValidUntil,
        fare_paid: Number(newPassFare),
      })
      toast.success('🎟️ Digital student transit pass issued!')
      setShowPassModal(false)
      refreshAll()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to issue pass')
    }
  }

  const handleSimulateGPS = async (vehicleId: number) => {
    // Generate slight random delta around NSBM
    const lat = 6.8211 + (Math.random() - 0.5) * 0.05
    const lng = 80.0416 + (Math.random() - 0.5) * 0.05
    try {
      await api.put(`/transport/vehicles/${vehicleId}/telemetry`, {
        current_lat: Number(lat.toFixed(6)),
        current_lng: Number(lng.toFixed(6)),
      })
      toast.success('📍 Live GPS telemetry pulse updated!')
      fetchVehicles()
    } catch (err: any) {
      toast.error('Failed to update telemetry')
    }
  }

  const isAdmin = ['admin'].includes(user?.role ?? '')

  return (
    <div className="fade-in">
      {/* Header */}
      <div className="page-header mb-24">
        <div className="flex justify-between items-center" style={{ flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div className="page-title">🚌 NSBM Campus Shuttle & Transport Network</div>
            <div className="page-subtitle">University passenger fleet, commuter routes, digital transit passes, and live bus tracking</div>
          </div>
          <div className="flex gap-12">
            {isAdmin && (
              <>
                <button className="btn btn-secondary" onClick={() => setShowScheduleModal(true)}>
                  ⏰ Add Schedule
                </button>
                <button className="btn btn-secondary" onClick={() => setShowVehicleModal(true)}>
                  ➕ Add Vehicle
                </button>
                <button className="btn btn-primary" onClick={() => setShowRouteModal(true)}>
                  🗺️ Add Route
                </button>
              </>
            )}
          </div>
        </div>

        {/* Fleet KPI Banner */}
        {summary && (
          <div className="grid-4 mt-20" style={{ gap: 14 }}>
            <div className="card text-center" style={{ padding: '16px' }}>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: '#6C63FF' }}>
                {summary.total_routes}
              </div>
              <div className="text-xs text-muted uppercase mt-4">Active Commuter Routes</div>
            </div>
            <div className="card text-center" style={{ padding: '16px' }}>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: '#00D4AA' }}>
                {summary.active_vehicles} / {summary.total_vehicles}
              </div>
              <div className="text-xs text-muted uppercase mt-4">Buses in Service</div>
            </div>
            <div className="card text-center" style={{ padding: '16px' }}>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: '#FFB347' }}>
                {summary.active_schedules}
              </div>
              <div className="text-xs text-muted uppercase mt-4">Daily Scheduled Trips</div>
            </div>
            <div className="card text-center" style={{ padding: '16px' }}>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: '#FF64C8' }}>
                {summary.fleet_capacity} seats
              </div>
              <div className="text-xs text-muted uppercase mt-4">Fleet Commuter Capacity</div>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex gap-16 mt-20" style={{ borderBottom: '1px solid var(--border)' }}>
          <button
            className={`btn btn-sm ${activeTab === 'routes' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setActiveTab('routes')}
            style={{ borderRadius: '6px 6px 0 0' }}
          >
            🗺️ Routes & Timetables
          </button>
          <button
            className={`btn btn-sm ${activeTab === 'passes' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setActiveTab('passes')}
            style={{ borderRadius: '6px 6px 0 0' }}
          >
            🎟️ {user?.role === 'student' ? 'My Transit Pass' : 'Student Transit Passes'}
          </button>
          <button
            className={`btn btn-sm ${activeTab === 'fleet' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setActiveTab('fleet')}
            style={{ borderRadius: '6px 6px 0 0' }}
          >
            🚌 Fleet & Telemetry ({vehicles.length})
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center" style={{ height: 300 }}>
          <div className="spinner" />
        </div>
      ) : activeTab === 'routes' ? (
        <div className="fade-in">
          <div className="grid-3 mb-24" style={{ gap: 16 }}>
            {routes.map((r) => (
              <div
                key={r.id}
                className="card"
                style={{
                  border: selectedRoute?.id === r.id ? '2px solid var(--primary)' : '1px solid var(--border)',
                  cursor: 'pointer',
                }}
                onClick={() => setSelectedRoute(r)}
              >
                <div className="flex justify-between items-start mb-8">
                  <div>
                    <h4 style={{ margin: 0, fontWeight: 700, fontSize: '1.1rem' }}>{r.route_name}</h4>
                    <span className="text-xs text-muted">{r.route_code}</span>
                  </div>
                  <span className="badge badge-success">LKR {r.fare_amount}/trip</span>
                </div>
                <div className="text-xs text-secondary mt-8">
                  <div>📍 Origin: <strong>{r.origin}</strong></div>
                  <div>🏁 Destination: <strong>{r.destination}</strong></div>
                </div>
                <div className="flex justify-between items-center text-xs mt-12 pt-8 text-muted" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                  <span>🛣️ {r.distance_km} km · ⏱️ ~{r.estimated_duration_mins} mins</span>
                  <span>{r.schedules?.length ?? 0} daily trips</span>
                </div>
              </div>
            ))}
          </div>

          {/* Selected Route Timetable & Stops */}
          {selectedRoute && (
            <div className="card">
              <div className="flex justify-between items-center mb-16 flex-wrap gap-12">
                <div>
                  <h3 style={{ margin: 0, fontWeight: 700, fontSize: '1.25rem' }}>
                    🚌 {selectedRoute.route_name} ({selectedRoute.route_code})
                  </h3>
                  <div className="text-xs text-muted mt-4">
                    {selectedRoute.origin} ➔ {selectedRoute.destination} · {selectedRoute.distance_km} km
                  </div>
                </div>
                {isAdmin && (
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={() => {
                      setNewSchedRouteId(selectedRoute.id)
                      setShowScheduleModal(true)
                    }}
                  >
                    ➕ Add Trip to Timetable
                  </button>
                )}
              </div>

              {/* Timetable Trips Table */}
              <h4 style={{ fontWeight: 600, fontSize: '.95rem', marginBottom: 12 }}>
                ⏰ Scheduled Daily Departures
              </h4>
              <div className="table-responsive mb-24">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Shift</th>
                      <th>Departure</th>
                      <th>Arrival (Est.)</th>
                      <th>Days of Service</th>
                      <th>Assigned Bus</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedRoute.schedules && selectedRoute.schedules.length > 0 ? (
                      selectedRoute.schedules.map((sch) => (
                        <tr key={sch.id}>
                          <td>
                            <span className="badge badge-info" style={{ textTransform: 'capitalize' }}>
                              {sch.shift_type.replace('_', ' ')}
                            </span>
                          </td>
                          <td style={{ fontWeight: 700, fontSize: '1.05rem', color: '#00D4AA' }}>
                            {sch.departure_time}
                          </td>
                          <td style={{ fontWeight: 600 }}>{sch.arrival_time}</td>
                          <td className="text-xs text-muted">
                            {sch.days_of_week ? sch.days_of_week.map((d) => d.slice(0, 3).toUpperCase()).join(', ') : 'Mon - Fri'}
                          </td>
                          <td>
                            {sch.vehicle_number ? (
                              <span className="badge badge-primary">{sch.vehicle_number}</span>
                            ) : (
                              <span className="text-muted text-xs">Standby Pool</span>
                            )}
                          </td>
                          <td>
                            <span className={`badge ${sch.is_active ? 'badge-success' : 'badge-secondary'}`}>
                              {sch.is_active ? 'Operating' : 'Suspended'}
                            </span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="text-center py-20 text-muted">
                          No scheduled trips yet for this route.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Intermediate Stops */}
              {selectedRoute.stops && selectedRoute.stops.length > 0 && (
                <div>
                  <h4 style={{ fontWeight: 600, fontSize: '.95rem', marginBottom: 12 }}>
                    🚏 Boarding & Intermediate Stops
                  </h4>
                  <div className="flex gap-12" style={{ flexWrap: 'wrap' }}>
                    {selectedRoute.stops.map((st) => (
                      <div
                        key={st.id}
                        style={{
                          padding: '10px 14px',
                          background: 'rgba(255,255,255,0.03)',
                          borderRadius: 8,
                          border: '1px solid var(--border)',
                          fontSize: '.85rem',
                        }}
                      >
                        <div style={{ fontWeight: 700 }}>
                          #{st.stop_order} {st.stop_name}
                        </div>
                        <div className="text-xs text-muted mt-2">
                          +{st.estimated_time_offset_mins} mins from origin
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ) : activeTab === 'passes' ? (
        <div className="fade-in">
          {/* Student's Personal Digital Pass */}
          {user?.role === 'student' && (
            <div className="card mb-24" style={{ background: 'linear-gradient(135deg, rgba(0,212,170,.12), rgba(108,99,255,.08))' }}>
              <h3 style={{ fontWeight: 700, fontSize: '1.25rem', marginBottom: 14 }}>
                🎟️ Your Digital Student Transit Pass
              </h3>
              {myPass ? (
                <div className="grid-3 items-center" style={{ gap: 20 }}>
                  <div>
                    <div className="text-xs text-muted uppercase">Commuter Transit Route</div>
                    <div style={{ fontWeight: 800, fontSize: '1.25rem' }}>
                      {myPass.route_name}
                    </div>
                    <div className="text-xs text-secondary mt-2">Code: {myPass.route_code}</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted uppercase">Validity Period</div>
                    <div style={{ fontWeight: 600 }}>
                      {new Date(myPass.valid_from).toLocaleDateString()} ➔ {new Date(myPass.valid_until).toLocaleDateString()}
                    </div>
                    <span className="badge badge-success mt-4">VALID & ACTIVE</span>
                  </div>
                  <div className="card text-center" style={{ background: 'rgba(0,0,0,0.3)', padding: 14 }}>
                    <div style={{ fontSize: '2.5rem' }}>📱</div>
                    <div style={{ fontFamily: 'monospace', fontWeight: 800, fontSize: '.95rem', color: '#00D4AA' }}>
                      {myPass.qr_code_token}
                    </div>
                    <div className="text-xs text-muted mt-2">Scan at bus entrance validator</div>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted">
                  You do not have an active semester bus pass. You can register for the university shuttle network through the campus Transport & Logistics Bureau.
                </p>
              )}
            </div>
          )}

          {/* Admin Passes Table */}
          <div className="card">
            <div className="flex justify-between items-center mb-16">
              <h3 style={{ margin: 0, fontWeight: 700 }}>🎟️ Registered Student Commuter Passes</h3>
              {isAdmin && (
                <button className="btn btn-primary btn-sm" onClick={() => setShowPassModal(true)}>
                  ➕ Issue Transit Pass
                </button>
              )}
            </div>
            <div className="table-responsive">
              <table className="table">
                <thead>
                  <tr>
                    <th>Student</th>
                    <th>Route</th>
                    <th>Pass Type</th>
                    <th>Validity</th>
                    <th>Digital Pass ID</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {passes.map((p) => (
                    <tr key={p.id}>
                      <td style={{ fontWeight: 600 }}>
                        {p.student_name || `Student #${p.student_id}`}
                        {p.student_reg_number && <span className="text-xs text-muted block">{p.student_reg_number}</span>}
                      </td>
                      <td>{p.route_name} ({p.route_code})</td>
                      <td style={{ textTransform: 'capitalize' }}>{p.pass_type}</td>
                      <td className="text-xs">
                        {new Date(p.valid_from).toLocaleDateString()} - {new Date(p.valid_until).toLocaleDateString()}
                      </td>
                      <td>
                        <code style={{ fontSize: '.8rem', color: '#00D4AA' }}>{p.qr_code_token}</code>
                      </td>
                      <td>
                        <span className={`badge ${p.status === 'active' ? 'badge-success' : 'badge-danger'}`}>
                          {p.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        /* Fleet & Telemetry Tab */
        <div className="fade-in">
          <div className="card mb-20" style={{ background: 'rgba(255,255,255,0.02)' }}>
            <div className="flex justify-between items-center">
              <div>
                <h3 style={{ margin: 0, fontWeight: 700, fontSize: '1.15rem' }}>
                  🚌 University Transport Fleet Roster & Telemetry
                </h3>
                <p className="text-xs text-muted mt-4">
                  GPS telemetry coordinates, maintenance logs, and capacity inspection across all coaches and vans.
                </p>
              </div>
              {isAdmin && (
                <button className="btn btn-primary btn-sm" onClick={() => setShowVehicleModal(true)}>
                  ➕ Add Vehicle
                </button>
              )}
            </div>
          </div>

          <div className="grid-3" style={{ gap: 16 }}>
            {vehicles.map((v) => (
              <div key={v.id} className="card" style={{ padding: 16 }}>
                <div className="flex justify-between items-start mb-8">
                  <div>
                    <h4 style={{ margin: 0, fontWeight: 800, fontSize: '1.15rem' }}>{v.vehicle_number}</h4>
                    <span className="text-xs text-muted" style={{ textTransform: 'capitalize' }}>
                      {v.vehicle_type} · {v.capacity} Seats
                    </span>
                  </div>
                  <span className={`badge ${v.status === 'active' ? 'badge-success' : 'badge-warning'}`}>
                    {v.status.toUpperCase()}
                  </span>
                </div>
                <div className="text-xs text-secondary mt-8">
                  <div>👤 Driver: <strong>{v.driver_name}</strong></div>
                  <div>📞 Contact: {v.driver_contact}</div>
                </div>
                <div className="mt-12 pt-8" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                  <div className="text-xs text-muted mb-4">
                    📍 GPS: {v.current_lat ?? 6.8211}, {v.current_lng ?? 80.0416}
                  </div>
                  {isAdmin && (
                    <button
                      className="btn btn-ghost btn-xs w-full mt-4"
                      onClick={() => handleSimulateGPS(v.id)}
                    >
                      📡 Pulse GPS Ping
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Vehicle Modal */}
      {showVehicleModal && (
        <div className="modal-backdrop">
          <div className="modal-box" style={{ maxWidth: 500 }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontWeight: 700 }}>🚌 Register Transport Vehicle</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowVehicleModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateVehicle}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <label className="text-xs text-muted mb-4 block">License Plate Number *</label>
                  <input
                    className="form-control w-full"
                    placeholder="e.g. WP ND-4821"
                    value={newVehNum}
                    onChange={(e) => setNewVehNum(e.target.value)}
                    required
                  />
                </div>
                <div className="grid-2" style={{ gap: 12 }}>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Vehicle Type</label>
                    <select className="form-control w-full" value={newVehType} onChange={(e) => setNewVehType(e.target.value)}>
                      <option value="bus">Large Transit Bus</option>
                      <option value="coaster">Coaster Mini Bus</option>
                      <option value="van">Passenger Van</option>
                      <option value="shuttle">Campus Internal Shuttle</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Passenger Capacity</label>
                    <input
                      type="number"
                      className="form-control w-full"
                      value={newVehCapacity}
                      onChange={(e) => setNewVehCapacity(Number(e.target.value))}
                      min={4}
                      max={100}
                    />
                  </div>
                </div>
                <div className="grid-2" style={{ gap: 12 }}>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Assigned Driver Name *</label>
                    <input
                      className="form-control w-full"
                      placeholder="e.g. K. Somapala"
                      value={newVehDriver}
                      onChange={(e) => setNewVehDriver(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Driver Contact Number *</label>
                    <input
                      className="form-control w-full"
                      placeholder="e.g. +94 77 456 7890"
                      value={newVehContact}
                      onChange={(e) => setNewVehContact(e.target.value)}
                      required
                    />
                  </div>
                </div>
              </div>
              <div className="modal-footer flex justify-end gap-12 mt-16">
                <button type="button" className="btn btn-ghost" onClick={() => setShowVehicleModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Add Vehicle</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Route Modal */}
      {showRouteModal && (
        <div className="modal-backdrop">
          <div className="modal-box" style={{ maxWidth: 520 }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontWeight: 700 }}>🗺️ Establish Shuttle Route</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowRouteModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateRoute}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <label className="text-xs text-muted mb-4 block">Route Display Name *</label>
                  <input
                    className="form-control w-full"
                    placeholder="e.g. Colombo Fort Express Shuttle"
                    value={newRouteName}
                    onChange={(e) => setNewRouteName(e.target.value)}
                    required
                  />
                </div>
                <div className="grid-2" style={{ gap: 12 }}>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Route Identifier Code *</label>
                    <input
                      className="form-control w-full"
                      placeholder="e.g. RT-CMB-01"
                      value={newRouteCode}
                      onChange={(e) => setNewRouteCode(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Single Trip Fare (LKR)</label>
                    <input
                      type="number"
                      className="form-control w-full"
                      value={newRouteFare}
                      onChange={(e) => setNewRouteFare(Number(e.target.value))}
                      min={0}
                    />
                  </div>
                </div>
                <div className="grid-2" style={{ gap: 12 }}>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Origin Point *</label>
                    <input
                      className="form-control w-full"
                      placeholder="e.g. Colombo Fort Railway Station"
                      value={newRouteOrigin}
                      onChange={(e) => setNewRouteOrigin(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Destination *</label>
                    <input
                      className="form-control w-full"
                      value={newRouteDest}
                      onChange={(e) => setNewRouteDest(e.target.value)}
                      required
                    />
                  </div>
                </div>
                <div className="grid-2" style={{ gap: 12 }}>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Distance (Kilometers)</label>
                    <input
                      type="number"
                      step="0.1"
                      className="form-control w-full"
                      value={newRouteDist}
                      onChange={(e) => setNewRouteDist(Number(e.target.value))}
                      min={1}
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Est. Duration (Minutes)</label>
                    <input
                      type="number"
                      className="form-control w-full"
                      value={newRouteDuration}
                      onChange={(e) => setNewRouteDuration(Number(e.target.value))}
                      min={5}
                    />
                  </div>
                </div>
              </div>
              <div className="modal-footer flex justify-end gap-12 mt-16">
                <button type="button" className="btn btn-ghost" onClick={() => setShowRouteModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create Route</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Schedule Modal */}
      {showScheduleModal && (
        <div className="modal-backdrop">
          <div className="modal-box" style={{ maxWidth: 500 }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontWeight: 700 }}>⏰ Add Timetable Departure</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowScheduleModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateSchedule}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <label className="text-xs text-muted mb-4 block">Shuttle Route *</label>
                  <select
                    className="form-control w-full"
                    value={newSchedRouteId}
                    onChange={(e) => setNewSchedRouteId(Number(e.target.value))}
                    required
                  >
                    {routes.map((r) => (
                      <option key={r.id} value={r.id}>{r.route_name} ({r.route_code})</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-muted mb-4 block">Assign Fleet Vehicle</label>
                  <select
                    className="form-control w-full"
                    value={newSchedVehId}
                    onChange={(e) => setNewSchedVehId(Number(e.target.value))}
                  >
                    <option value="">Pool / Unassigned</option>
                    {vehicles.filter((v) => v.status === 'active').map((v) => (
                      <option key={v.id} value={v.id}>{v.vehicle_number} ({v.driver_name})</option>
                    ))}
                  </select>
                </div>
                <div className="grid-2" style={{ gap: 12 }}>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Departure Time (HH:MM) *</label>
                    <input
                      type="time"
                      className="form-control w-full"
                      value={newSchedDep}
                      onChange={(e) => setNewSchedDep(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Arrival Time (HH:MM) *</label>
                    <input
                      type="time"
                      className="form-control w-full"
                      value={newSchedArr}
                      onChange={(e) => setNewSchedArr(e.target.value)}
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs text-muted mb-4 block">Shift Type</label>
                  <select className="form-control w-full" value={newSchedShift} onChange={(e) => setNewSchedShift(e.target.value)}>
                    <option value="morning_inbound">Morning Inbound (to Campus)</option>
                    <option value="evening_outbound">Evening Outbound (from Campus)</option>
                    <option value="midday_shuttle">Midday Shuttle</option>
                    <option value="special">Special Academic Event</option>
                  </select>
                </div>
              </div>
              <div className="modal-footer flex justify-end gap-12 mt-16">
                <button type="button" className="btn btn-ghost" onClick={() => setShowScheduleModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Schedule Trip</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Transit Pass Modal */}
      {showPassModal && (
        <div className="modal-backdrop">
          <div className="modal-box" style={{ maxWidth: 500 }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontWeight: 700 }}>🎟️ Issue Student Transit Pass</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowPassModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreatePass}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <label className="text-xs text-muted mb-4 block">Student Database ID *</label>
                  <input
                    type="number"
                    className="form-control w-full"
                    placeholder="Enter Student ID (e.g. 1)"
                    value={newPassStudentId || ''}
                    onChange={(e) => setNewPassStudentId(Number(e.target.value))}
                    required
                  />
                </div>
                <div>
                  <label className="text-xs text-muted mb-4 block">Assigned Route *</label>
                  <select
                    className="form-control w-full"
                    value={newPassRouteId}
                    onChange={(e) => setNewPassRouteId(Number(e.target.value))}
                    required
                  >
                    {routes.map((r) => (
                      <option key={r.id} value={r.id}>{r.route_name} ({r.route_code})</option>
                    ))}
                  </select>
                </div>
                <div className="grid-2" style={{ gap: 12 }}>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Valid From *</label>
                    <input
                      type="date"
                      className="form-control w-full"
                      value={newPassValidFrom}
                      onChange={(e) => setNewPassValidFrom(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Valid Until *</label>
                    <input
                      type="date"
                      className="form-control w-full"
                      value={newPassValidUntil}
                      onChange={(e) => setNewPassValidUntil(e.target.value)}
                      required
                    />
                  </div>
                </div>
                <div className="grid-2" style={{ gap: 12 }}>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Pass Duration</label>
                    <select className="form-control w-full" value={newPassType} onChange={(e) => setNewPassType(e.target.value)}>
                      <option value="semester">Semester Pass</option>
                      <option value="monthly">Monthly Pass</option>
                      <option value="single_trip">Single Trip</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Fee Paid (LKR)</label>
                    <input
                      type="number"
                      className="form-control w-full"
                      value={newPassFare}
                      onChange={(e) => setNewPassFare(Number(e.target.value))}
                      min={0}
                    />
                  </div>
                </div>
              </div>
              <div className="modal-footer flex justify-end gap-12 mt-16">
                <button type="button" className="btn btn-ghost" onClick={() => setShowPassModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Issue Pass</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
