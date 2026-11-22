import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '@/api/client'
import toast from 'react-hot-toast'
import type { CampusOperationsOverview, CampusOperationalAlert } from '@/types'
import { useAuth } from '@/contexts/AuthContext'

export default function CampusOperations() {
  const { user } = useAuth()
  const [overview, setOverview] = useState<CampusOperationsOverview | null>(null)
  const [alerts, setAlerts] = useState<CampusOperationalAlert[]>([])
  const [loading, setLoading] = useState(true)

  const fetchData = async () => {
    setLoading(true)
    try {
      const [ovRes, alRes] = await Promise.all([
        api.get<CampusOperationsOverview>('/campus-operations/overview'),
        api.get<CampusOperationalAlert[]>('/campus-operations/alerts'),
      ])
      setOverview(ovRes.data)
      setAlerts(alRes.data)
    } catch {
      toast.error('Failed to load campus operations telemetry')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  return (
    <div className="fade-in">
      {/* Header */}
      <div className="page-header mb-24">
        <div className="flex justify-between items-center" style={{ flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div className="page-title">🎛️ NSBM Unified Campus Operations Command Center</div>
            <div className="page-subtitle">
              Real-time executive telemetry across Finance, Library, Athletics, Housing, Transit, Media, and Facilities
            </div>
          </div>
          <div className="flex gap-12 items-center">
            <span className="badge badge-success" style={{ padding: '8px 12px', fontSize: '.8rem' }}>
              ● CAMPUS NETWORK ONLINE
            </span>
            <button className="btn btn-secondary btn-sm" onClick={fetchData}>
              🔄 Refresh Telemetry
            </button>
          </div>
        </div>

        {/* Operational Alerts Ribbon */}
        {alerts.length > 0 && (
          <div className="mt-16" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {alerts.map((al) => (
              <div
                key={al.id}
                style={{
                  padding: '10px 16px',
                  borderRadius: 8,
                  fontSize: '.85rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  background:
                    al.level === 'warning'
                      ? 'rgba(255, 184, 77, 0.12)'
                      : al.level === 'critical'
                      ? 'rgba(255, 107, 107, 0.15)'
                      : 'rgba(0, 212, 170, 0.1)',
                  border:
                    al.level === 'warning'
                      ? '1px solid rgba(255, 184, 77, 0.3)'
                      : al.level === 'critical'
                      ? '1px solid rgba(255, 107, 107, 0.35)'
                      : '1px solid rgba(0, 212, 170, 0.25)',
                }}
              >
                <div>
                  <strong style={{ marginRight: 8 }}>
                    {al.level === 'warning' ? '⚠️' : al.level === 'critical' ? '🚨' : 'ℹ️'} {al.title}:
                  </strong>
                  <span>{al.message}</span>
                </div>
                <span className="text-xs text-muted">
                  {new Date(al.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {loading && !overview ? (
        <div className="flex justify-center items-center" style={{ height: 350 }}>
          <div className="spinner" />
        </div>
      ) : overview ? (
        <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* Quick Nav Command Bar */}
          <div className="card" style={{ padding: 14, background: 'rgba(255,255,255,0.02)' }}>
            <div className="flex justify-between items-center flex-wrap gap-8">
              <span style={{ fontWeight: 700, fontSize: '.9rem' }}>Direct Operational Desks:</span>
              <div className="flex gap-8 flex-wrap">
                <Link to="/billing" className="btn btn-ghost btn-xs">💳 Finance & Fees</Link>
                <Link to="/library" className="btn btn-ghost btn-xs">📚 Library & e-Reader</Link>
                <Link to="/sports" className="btn btn-ghost btn-xs">⚽ Sports & Athletics</Link>
                <Link to="/news" className="btn btn-ghost btn-xs">📰 Media & Press</Link>
                <Link to="/hostels" className="btn btn-ghost btn-xs">🏢 Housing & Hostels</Link>
                <Link to="/transport" className="btn btn-ghost btn-xs">🚌 Transport & Shuttles</Link>
                <Link to="/facilities" className="btn btn-ghost btn-xs">🏛️ Space Reservations</Link>
              </div>
            </div>
          </div>

          {/* Grid of the 7 Operational Domains */}
          <div className="grid-2" style={{ gap: 20 }}>
            {/* 1. Finance Domain */}
            <div className="card" style={{ borderLeft: '4px solid #6C63FF' }}>
              <div className="flex justify-between items-center mb-14">
                <h3 style={{ margin: 0, fontWeight: 700, fontSize: '1.15rem' }}>
                  💳 Finance & Institutional Billing
                </h3>
                <Link to="/billing" className="btn btn-ghost btn-xs">View Invoices →</Link>
              </div>
              <div className="grid-2" style={{ gap: 12 }}>
                <div className="card text-center" style={{ padding: 12, background: 'rgba(255,255,255,0.02)' }}>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#6C63FF' }}>
                    LKR {overview.finance.total_collected.toLocaleString()}
                  </div>
                  <div className="text-xs text-muted uppercase mt-2">Revenue Collected</div>
                </div>
                <div className="card text-center" style={{ padding: 12, background: 'rgba(255,255,255,0.02)' }}>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#00D4AA' }}>
                    {overview.finance.collection_rate}%
                  </div>
                  <div className="text-xs text-muted uppercase mt-2">Collection Rate</div>
                </div>
              </div>
              <div className="flex justify-between items-center text-xs text-muted mt-14 pt-10" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                <span>Total Invoiced: LKR {overview.finance.total_invoiced.toLocaleString()}</span>
                <span>Outstanding: LKR {overview.finance.outstanding_balance.toLocaleString()}</span>
              </div>
            </div>

            {/* 2. Library Domain */}
            <div className="card" style={{ borderLeft: '4px solid #00D4AA' }}>
              <div className="flex justify-between items-center mb-14">
                <h3 style={{ margin: 0, fontWeight: 700, fontSize: '1.15rem' }}>
                  📚 Digital & Physical Knowledge Hub
                </h3>
                <Link to="/library" className="btn btn-ghost btn-xs">Catalog & Circulation →</Link>
              </div>
              <div className="grid-2" style={{ gap: 12 }}>
                <div className="card text-center" style={{ padding: 12, background: 'rgba(255,255,255,0.02)' }}>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#00D4AA' }}>
                    {overview.library.total_digital_resources}
                  </div>
                  <div className="text-xs text-muted uppercase mt-2">e-Resources & Papers</div>
                </div>
                <div className="card text-center" style={{ padding: 12, background: 'rgba(255,255,255,0.02)' }}>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#FFB347' }}>
                    {overview.library.active_borrowings}
                  </div>
                  <div className="text-xs text-muted uppercase mt-2">Active Book Loans</div>
                </div>
              </div>
              <div className="flex justify-between items-center text-xs text-muted mt-14 pt-10" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                <span>Physical Books: {overview.library.total_physical_books} volumes</span>
                <span style={{ color: overview.library.overdue_loans > 0 ? '#FF6B6B' : 'inherit' }}>
                  Overdue Items: {overview.library.overdue_loans}
                </span>
              </div>
            </div>

            {/* 3. Housing Domain */}
            <div className="card" style={{ borderLeft: '4px solid #FFB347' }}>
              <div className="flex justify-between items-center mb-14">
                <h3 style={{ margin: 0, fontWeight: 700, fontSize: '1.15rem' }}>
                  🏢 Student Residential Complexes
                </h3>
                <Link to="/hostels" className="btn btn-ghost btn-xs">Hostel Roster →</Link>
              </div>
              <div className="grid-2" style={{ gap: 12 }}>
                <div className="card text-center" style={{ padding: 12, background: 'rgba(255,255,255,0.02)' }}>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#FFB347' }}>
                    {overview.accommodation.occupancy_rate}%
                  </div>
                  <div className="text-xs text-muted uppercase mt-2">Hostel Occupancy</div>
                </div>
                <div className="card text-center" style={{ padding: 12, background: 'rgba(255,255,255,0.02)' }}>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#00D4AA' }}>
                    {overview.accommodation.available_beds}
                  </div>
                  <div className="text-xs text-muted uppercase mt-2">Vacant Beds</div>
                </div>
              </div>
              <div className="flex justify-between items-center text-xs text-muted mt-14 pt-10" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                <span>Capacity: {overview.accommodation.occupied_beds} / {overview.accommodation.total_capacity} beds</span>
                <span>Active Repairs: {overview.accommodation.pending_repairs}</span>
              </div>
            </div>

            {/* 4. Transport Domain */}
            <div className="card" style={{ borderLeft: '4px solid #FF64C8' }}>
              <div className="flex justify-between items-center mb-14">
                <h3 style={{ margin: 0, fontWeight: 700, fontSize: '1.15rem' }}>
                  🚌 Campus Transit & Shuttle Network
                </h3>
                <Link to="/transport" className="btn btn-ghost btn-xs">Fleet & Routes →</Link>
              </div>
              <div className="grid-2" style={{ gap: 12 }}>
                <div className="card text-center" style={{ padding: 12, background: 'rgba(255,255,255,0.02)' }}>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#FF64C8' }}>
                    {overview.transport.fleet_vehicles}
                  </div>
                  <div className="text-xs text-muted uppercase mt-2">Active Fleet Coaches</div>
                </div>
                <div className="card text-center" style={{ padding: 12, background: 'rgba(255,255,255,0.02)' }}>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#6C63FF' }}>
                    {overview.transport.active_transit_passes}
                  </div>
                  <div className="text-xs text-muted uppercase mt-2">Active Transit Passes</div>
                </div>
              </div>
              <div className="flex justify-between items-center text-xs text-muted mt-14 pt-10" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                <span>Commuter Routes: {overview.transport.active_routes} lines</span>
                <span>Daily Scheduled Runs: {overview.transport.daily_trips} trips</span>
              </div>
            </div>

            {/* 5. Facilities Domain */}
            <div className="card" style={{ borderLeft: '4px solid #38EF7D' }}>
              <div className="flex justify-between items-center mb-14">
                <h3 style={{ margin: 0, fontWeight: 700, fontSize: '1.15rem' }}>
                  🏛️ Venues & Space Reservations
                </h3>
                <Link to="/facilities" className="btn btn-ghost btn-xs">Space Bookings →</Link>
              </div>
              <div className="grid-2" style={{ gap: 12 }}>
                <div className="card text-center" style={{ padding: 12, background: 'rgba(255,255,255,0.02)' }}>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#38EF7D' }}>
                    {overview.facilities.total_venues}
                  </div>
                  <div className="text-xs text-muted uppercase mt-2">Managed Venues</div>
                </div>
                <div className="card text-center" style={{ padding: 12, background: 'rgba(255,255,255,0.02)' }}>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#FFB347' }}>
                    {overview.facilities.reservations_today}
                  </div>
                  <div className="text-xs text-muted uppercase mt-2">Events Today</div>
                </div>
              </div>
              <div className="flex justify-between items-center text-xs text-muted mt-14 pt-10" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                <span>Total Seat Capacity: {overview.facilities.combined_capacity.toLocaleString()}</span>
                <span>Pending Approvals: {overview.facilities.pending_approvals}</span>
              </div>
            </div>

            {/* 6. Athletics & Media Composite Domain */}
            <div className="card" style={{ borderLeft: '4px solid #FF6B6B' }}>
              <div className="flex justify-between items-center mb-14">
                <h3 style={{ margin: 0, fontWeight: 700, fontSize: '1.15rem' }}>
                  ⚽ Athletics & Campus Journalism
                </h3>
                <div className="flex gap-4">
                  <Link to="/sports" className="btn btn-ghost btn-xs">Sports →</Link>
                  <Link to="/news" className="btn btn-ghost btn-xs">News →</Link>
                </div>
              </div>
              <div className="grid-2" style={{ gap: 12 }}>
                <div className="card text-center" style={{ padding: 12, background: 'rgba(255,255,255,0.02)' }}>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#FF6B6B' }}>
                    {overview.athletics.active_teams}
                  </div>
                  <div className="text-xs text-muted uppercase mt-2">Athletic Teams</div>
                </div>
                <div className="card text-center" style={{ padding: 12, background: 'rgba(255,255,255,0.02)' }}>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#6C63FF' }}>
                    {overview.media.total_views.toLocaleString()}
                  </div>
                  <div className="text-xs text-muted uppercase mt-2">News Readers</div>
                </div>
              </div>
              <div className="flex justify-between items-center text-xs text-muted mt-14 pt-10" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                <span>Athletes: {overview.athletics.roster_athletes} (Fixtures: {overview.athletics.upcoming_fixtures})</span>
                <span>Published Stories: {overview.media.published_articles}</span>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
