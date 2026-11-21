import React, { useEffect, useState } from 'react'
import api from '@/api/client'
import { useAuth } from '@/contexts/AuthContext'
import {
  StudentInvoice,
  BillingSummary,
  FeeStructure,
} from '@/types'
import toast from 'react-hot-toast'

export default function Billing() {
  const { user } = useAuth()
  const isFinanceStaff = user?.role === 'admin' || user?.role === 'accountant'

  // Data states
  const [invoices, setInvoices] = useState<StudentInvoice[]>([])
  const [summary, setSummary] = useState<BillingSummary | null>(null)
  const [feeStructures, setFeeStructures] = useState<FeeStructure[]>([])
  const [loading, setLoading] = useState<boolean>(true)

  // Modals
  const [selectedInvoice, setSelectedInvoice] = useState<StudentInvoice | null>(null)
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false)
  const [creating, setCreating] = useState<boolean>(false)

  // Invoice creation form
  const [newStudentId, setNewStudentId] = useState<number | ''>('')
  const [newFeeStructId, setNewFeeStructId] = useState<number | ''>('')
  const [newTerm, setNewTerm] = useState<string>('Year 1 - Semester 1')
  const [newTotalAmount, setNewTotalAmount] = useState<number>(180000)
  const [newDiscount, setNewDiscount] = useState<number>(0)
  const [newDueDate, setNewDueDate] = useState<string>('')
  const [newPlanType, setNewPlanType] = useState<string>('full')
  const [newNotes, setNewNotes] = useState<string>('')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      if (isFinanceStaff) {
        const [invRes, sumRes, structRes] = await Promise.all([
          api.get<StudentInvoice[]>('/billing/admin/invoices'),
          api.get<BillingSummary>('/billing/summary'),
          api.get<FeeStructure[]>('/billing/fee-structures'),
        ])
        setInvoices(invRes.data)
        setSummary(sumRes.data)
        setFeeStructures(structRes.data)
      } else {
        const invRes = await api.get<StudentInvoice[]>('/billing/invoices/my')
        setInvoices(invRes.data)
      }
    } catch (err: any) {
      console.error('Failed to load billing data:', err)
      toast.error('Could not load billing records.')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateInvoice = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newStudentId || !newDueDate || creating) return

    try {
      setCreating(true)
      const payload = {
        student_id: Number(newStudentId),
        fee_structure_id: newFeeStructId ? Number(newFeeStructId) : undefined,
        academic_term: newTerm,
        total_amount: Number(newTotalAmount),
        discount_amount: Number(newDiscount) || 0,
        due_date: newDueDate,
        payment_plan_type: newPlanType,
        notes: newNotes.trim() || undefined,
      }
      await api.post('/billing/invoices', payload)
      toast.success('Invoice generated successfully!')
      setShowCreateModal(false)
      loadData()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to generate invoice.')
    } finally {
      setCreating(false)
    }
  }

  const formatCurrency = (amount: number, currency: string = 'LKR') => {
    return `${currency} ${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'paid':
        return { label: '✓ PAID', bg: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.3)' }
      case 'partially_paid':
        return { label: 'PARTIALLY PAID', bg: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.3)' }
      case 'overdue':
        return { label: '⚠️ OVERDUE', bg: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', border: '1px solid rgba(239, 68, 68, 0.3)' }
      default:
        return { label: 'UNPAID', bg: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.3)' }
    }
  }

  // Calculate student balance totals
  const studentTotalBalance = invoices.reduce((acc, i) => acc + i.balance_due, 0)
  const studentTotalPaid = invoices.reduce((acc, i) => acc + i.paid_amount, 0)

  return (
    <div className="fade-in" style={{ maxWidth: 1200, margin: '0 auto', paddingBottom: 40 }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.85rem', fontWeight: 800, fontFamily: "'Outfit', sans-serif" }}>
            Student Billing & Fee Management
          </h1>
          <p className="text-muted" style={{ margin: '4px 0 0 0', fontSize: '0.92rem' }}>
            Institutional tuition billing, installment schedules, and official financial receipts.
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {isFinanceStaff && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: 6 }}
            >
              <span>🧾</span> Generate Student Invoice
            </button>
          )}
        </div>
      </div>

      {/* KPI Cards Banner */}
      {isFinanceStaff && summary ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, marginBottom: 24 }}>
          <div className="card" style={{ padding: 18 }}>
            <div className="text-muted" style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase' }}>
              Total Invoiced
            </div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, marginTop: 4, color: '#60a5fa' }}>
              {formatCurrency(summary.total_invoiced)}
            </div>
            <div className="text-muted" style={{ fontSize: '0.8rem', marginTop: 2 }}>
              Across {summary.invoices_count} invoices
            </div>
          </div>

          <div className="card" style={{ padding: 18 }}>
            <div className="text-muted" style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase' }}>
              Total Collected
            </div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, marginTop: 4, color: '#34d399' }}>
              {formatCurrency(summary.total_collected)}
            </div>
            <div className="text-muted" style={{ fontSize: '0.8rem', marginTop: 2 }}>
              {summary.paid_invoices_count} fully paid
            </div>
          </div>

          <div className="card" style={{ padding: 18 }}>
            <div className="text-muted" style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase' }}>
              Outstanding Balance
            </div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, marginTop: 4, color: '#fbbf24' }}>
              {formatCurrency(summary.total_outstanding)}
            </div>
            <div className="text-muted" style={{ fontSize: '0.8rem', marginTop: 2 }}>
              Active receivables
            </div>
          </div>

          <div className="card" style={{ padding: 18 }}>
            <div className="text-muted" style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase' }}>
              Overdue Amount
            </div>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, marginTop: 4, color: '#ef4444' }}>
              {formatCurrency(summary.total_overdue)}
            </div>
            <div className="text-muted" style={{ fontSize: '0.8rem', marginTop: 2 }}>
              {summary.overdue_invoices_count} past due date
            </div>
          </div>
        </div>
      ) : (
        /* Student KPI banner */
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16, marginBottom: 24 }}>
          <div className="card" style={{ padding: 18 }}>
            <div className="text-muted" style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase' }}>
              Outstanding Balance
            </div>
            <div
              style={{
                fontSize: '1.8rem',
                fontWeight: 800,
                marginTop: 4,
                color: studentTotalBalance > 0 ? '#fbbf24' : '#34d399',
              }}
            >
              {formatCurrency(studentTotalBalance)}
            </div>
            <div className="text-muted" style={{ fontSize: '0.8rem', marginTop: 2 }}>
              {studentTotalBalance === 0 ? 'All fees settled' : 'Payment due'}
            </div>
          </div>

          <div className="card" style={{ padding: 18 }}>
            <div className="text-muted" style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase' }}>
              Total Fees Settled
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: 4, color: '#34d399' }}>
              {formatCurrency(studentTotalPaid)}
            </div>
            <div className="text-muted" style={{ fontSize: '0.8rem', marginTop: 2 }}>
              Verified institutional payments
            </div>
          </div>

          <div className="card" style={{ padding: 18 }}>
            <div className="text-muted" style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase' }}>
              Total Issued Invoices
            </div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: 4, color: '#60a5fa' }}>
              {invoices.length}
            </div>
            <div className="text-muted" style={{ fontSize: '0.8rem', marginTop: 2 }}>
              Semester tuition & facility fees
            </div>
          </div>
        </div>
      )}

      {/* Invoices Ledger Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid var(--border-color)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor: 'rgba(255, 255, 255, 0.02)',
          }}
        >
          <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700 }}>
            {isFinanceStaff ? 'Institutional Fee Invoices' : 'Your Fee Invoices'}
          </h3>
          <span className="text-muted" style={{ fontSize: '0.84rem' }}>
            Showing {invoices.length} invoice{invoices.length !== 1 ? 's' : ''}
          </span>
        </div>

        {loading ? (
          <div style={{ padding: 48, textAlign: 'center' }} className="text-muted">Loading fee records...</div>
        ) : invoices.length === 0 ? (
          <div style={{ padding: 48, textAlign: 'center' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: 10 }}>🧾</div>
            <h4 style={{ margin: 0, fontWeight: 700 }}>No Invoices Found</h4>
            <p className="text-muted" style={{ margin: '6px 0 0 0', fontSize: '0.88rem' }}>
              There are no billing records registered for your account.
            </p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', color: '#94a3b8', fontSize: '0.8rem', textTransform: 'uppercase' }}>
                  <th style={{ padding: '12px 18px' }}>Invoice #</th>
                  {isFinanceStaff && <th style={{ padding: '12px 18px' }}>Student</th>}
                  <th style={{ padding: '12px 18px' }}>Academic Term</th>
                  <th style={{ padding: '12px 18px' }}>Total Amount</th>
                  <th style={{ padding: '12px 18px' }}>Paid</th>
                  <th style={{ padding: '12px 18px' }}>Balance Due</th>
                  <th style={{ padding: '12px 18px' }}>Due Date</th>
                  <th style={{ padding: '12px 18px' }}>Status</th>
                  <th style={{ padding: '12px 18px', textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((inv) => {
                  const sBadge = getStatusBadge(inv.status)
                  return (
                    <tr
                      key={inv.id}
                      style={{
                        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                        transition: 'background 0.15s',
                      }}
                    >
                      <td style={{ padding: '14px 18px', fontWeight: 700, color: '#60a5fa' }}>
                        {inv.invoice_number}
                      </td>
                      {isFinanceStaff && (
                        <td style={{ padding: '14px 18px' }}>
                          <div>{inv.student_name || 'Student'}</div>
                          <div className="text-muted" style={{ fontSize: '0.75rem' }}>{inv.student_number}</div>
                        </td>
                      )}
                      <td style={{ padding: '14px 18px' }}>{inv.academic_term}</td>
                      <td style={{ padding: '14px 18px', fontWeight: 600 }}>{formatCurrency(inv.total_amount, inv.currency)}</td>
                      <td style={{ padding: '14px 18px', color: '#34d399' }}>{formatCurrency(inv.paid_amount, inv.currency)}</td>
                      <td style={{ padding: '14px 18px', fontWeight: 700, color: inv.balance_due > 0 ? '#fbbf24' : '#94a3b8' }}>
                        {formatCurrency(inv.balance_due, inv.currency)}
                      </td>
                      <td style={{ padding: '14px 18px', fontSize: '0.85rem' }}>
                        {new Date(inv.due_date).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}
                      </td>
                      <td style={{ padding: '14px 18px' }}>
                        <span
                          style={{
                            fontSize: '0.72rem',
                            fontWeight: 700,
                            padding: '3px 8px',
                            borderRadius: 6,
                            backgroundColor: sBadge.bg,
                            color: sBadge.color,
                            border: sBadge.border,
                          }}
                        >
                          {sBadge.label}
                        </span>
                      </td>
                      <td style={{ padding: '14px 18px', textAlign: 'right' }}>
                        <button
                          onClick={() => setSelectedInvoice(inv)}
                          className="btn btn-secondary"
                          style={{ fontSize: '0.8rem', padding: '4px 10px' }}
                        >
                          View Details 👁
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Invoice Detail / Receipt Modal */}
      {selectedInvoice && (
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
              maxWidth: 620,
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: 24,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
              <div>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#60a5fa' }}>NSBM EDUSPHERE OFFICIAL INVOICE</span>
                <h3 style={{ margin: '4px 0 0 0', fontSize: '1.4rem', fontWeight: 800 }}>
                  {selectedInvoice.invoice_number}
                </h3>
                <div className="text-muted" style={{ fontSize: '0.82rem', marginTop: 2 }}>
                  Term: {selectedInvoice.academic_term} • Issued: {selectedInvoice.issue_date}
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelectedInvoice(null)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '1.3rem' }}
              >
                ✕
              </button>
            </div>

            {/* Student & Status Info */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 12,
                backgroundColor: 'rgba(255, 255, 255, 0.02)',
                padding: 14,
                borderRadius: 8,
                marginBottom: 20,
              }}
            >
              <div>
                <div className="text-muted" style={{ fontSize: '0.75rem' }}>Billed To:</div>
                <div style={{ fontWeight: 700, fontSize: '0.92rem' }}>{selectedInvoice.student_name || 'Enrolled Student'}</div>
                <div className="text-muted" style={{ fontSize: '0.8rem' }}>{selectedInvoice.student_number}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div className="text-muted" style={{ fontSize: '0.75rem' }}>Payment Status:</div>
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: 6,
                    ...getStatusBadge(selectedInvoice.status),
                  }}
                >
                  {selectedInvoice.status.toUpperCase()}
                </span>
                <div className="text-muted" style={{ fontSize: '0.8rem', marginTop: 4 }}>
                  Due by: {selectedInvoice.due_date}
                </div>
              </div>
            </div>

            {/* Line Items Breakdown */}
            <h4 style={{ margin: '0 0 10px 0', fontSize: '0.95rem', fontWeight: 700 }}>Fee Component Breakdown</h4>
            <div style={{ border: '1px solid var(--border-color)', borderRadius: 8, overflow: 'hidden', marginBottom: 20 }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
                <thead>
                  <tr style={{ backgroundColor: 'rgba(255, 255, 255, 0.03)', borderBottom: '1px solid var(--border-color)', color: '#94a3b8' }}>
                    <th style={{ padding: '10px 14px', textAlign: 'left' }}>Description</th>
                    <th style={{ padding: '10px 14px', textAlign: 'right' }}>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedInvoice.items && selectedInvoice.items.length > 0 ? (
                    selectedInvoice.items.map((it) => (
                      <tr key={it.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                        <td style={{ padding: '10px 14px' }}>{it.component_name}</td>
                        <td style={{ padding: '10px 14px', textAlign: 'right', fontWeight: 600 }}>
                          {formatCurrency(it.amount, selectedInvoice.currency)}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td style={{ padding: '10px 14px' }}>Tuition & Academic Module Delivery</td>
                      <td style={{ padding: '10px 14px', textAlign: 'right', fontWeight: 600 }}>
                        {formatCurrency(selectedInvoice.total_amount, selectedInvoice.currency)}
                      </td>
                    </tr>
                  )}
                  {selectedInvoice.discount_amount > 0 && (
                    <tr style={{ color: '#34d399' }}>
                      <td style={{ padding: '10px 14px' }}>Scholarship / Institutional Discount</td>
                      <td style={{ padding: '10px 14px', textAlign: 'right', fontWeight: 600 }}>
                        - {formatCurrency(selectedInvoice.discount_amount, selectedInvoice.currency)}
                      </td>
                    </tr>
                  )}
                  <tr style={{ backgroundColor: 'rgba(59, 130, 246, 0.06)', fontWeight: 800 }}>
                    <td style={{ padding: '12px 14px' }}>Total Balance Due</td>
                    <td style={{ padding: '12px 14px', textAlign: 'right', color: '#60a5fa' }}>
                      {formatCurrency(selectedInvoice.balance_due, selectedInvoice.currency)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Installments Breakdown if any */}
            {selectedInvoice.installments && selectedInvoice.installments.length > 1 && (
              <div style={{ marginBottom: 20 }}>
                <h4 style={{ margin: '0 0 10px 0', fontSize: '0.95rem', fontWeight: 700 }}>
                  Installment Payment Schedule
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {selectedInvoice.installments.map((inst) => (
                    <div
                      key={inst.id}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '10px 14px',
                        backgroundColor: 'rgba(255, 255, 255, 0.02)',
                        borderRadius: 6,
                        border: '1px solid var(--border-color)',
                      }}
                    >
                      <div>
                        <span style={{ fontWeight: 700, fontSize: '0.85rem' }}>Installment {inst.installment_number}:</span>{' '}
                        <span style={{ fontSize: '0.82rem', color: '#94a3b8' }}>Due on {inst.due_date}</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>
                          {formatCurrency(inst.amount, selectedInvoice.currency)}
                        </span>
                        <span
                          style={{
                            fontSize: '0.7rem',
                            fontWeight: 700,
                            padding: '2px 6px',
                            borderRadius: 4,
                            backgroundColor: inst.status === 'paid' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                            color: inst.status === 'paid' ? '#34d399' : '#fbbf24',
                          }}
                        >
                          {inst.status.toUpperCase()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 16 }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setSelectedInvoice(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Staff Generate Invoice Modal */}
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
              <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800 }}>Generate Student Invoice</h3>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '1.2rem' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateInvoice}>
              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Student ID (Numeric Profile ID) *
                </label>
                <input
                  type="number"
                  placeholder="e.g. 1"
                  className="form-control"
                  value={newStudentId}
                  onChange={(e) => setNewStudentId(Number(e.target.value) || '')}
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                    Fee Structure Template
                  </label>
                  <select
                    className="form-control"
                    value={newFeeStructId}
                    onChange={(e) => {
                      const id = Number(e.target.value) || ''
                      setNewFeeStructId(id)
                      const found = feeStructures.find((f) => f.id === id)
                      if (found) setNewTotalAmount(found.total_amount)
                    }}
                  >
                    <option value="">Custom Fee</option>
                    {feeStructures.map((f) => (
                      <option key={f.id} value={f.id}>
                        {f.name} ({formatCurrency(f.total_amount)})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                    Academic Term *
                  </label>
                  <input
                    type="text"
                    className="form-control"
                    value={newTerm}
                    onChange={(e) => setNewTerm(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                    Total Fee Amount (LKR) *
                  </label>
                  <input
                    type="number"
                    className="form-control"
                    value={newTotalAmount}
                    onChange={(e) => setNewTotalAmount(Number(e.target.value) || 0)}
                    required
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                    Scholarship / Discount (LKR)
                  </label>
                  <input
                    type="number"
                    className="form-control"
                    value={newDiscount}
                    onChange={(e) => setNewDiscount(Number(e.target.value) || 0)}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                    Payment Plan
                  </label>
                  <select
                    className="form-control"
                    value={newPlanType}
                    onChange={(e) => setNewPlanType(e.target.value)}
                  >
                    <option value="full">Full Settlement</option>
                    <option value="installment_2">2 Installments</option>
                    <option value="installment_3">3 Installments</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                    Due Date *
                  </label>
                  <input
                    type="date"
                    className="form-control"
                    value={newDueDate}
                    onChange={(e) => setNewDueDate(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Notes (Optional)
                </label>
                <textarea
                  className="form-control"
                  rows={2}
                  placeholder="Additional invoice remarks..."
                  value={newNotes}
                  onChange={(e) => setNewNotes(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={creating}>
                  {creating ? 'Generating...' : 'Create Invoice'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
