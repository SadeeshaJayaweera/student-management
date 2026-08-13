import React, { useEffect, useState } from 'react'
import api from '@/api/client'
import toast from 'react-hot-toast'
import type { Book, BorrowRecord, Paginated } from '@/types'
import { useAuth } from '@/contexts/AuthContext'

const BOOK_EMOJI: Record<string, string> = {
  'Computer Science': '💻', 'AI/ML': '🤖', Business: '💼', Engineering: '⚙️',
  Databases: '🗄️', Networking: '🌐', 'Data Science': '📊',
  'Software Engineering': '🔧', Mathematics: '📐', Physics: '⚗️',
}

function BookCard({ book, canBorrow, onBorrow }: { book: Book; canBorrow: boolean; onBorrow: (id: number, title: string) => void }) {
  const emoji = BOOK_EMOJI[book.category] ?? '📖'
  const available = book.available_copies > 0
  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <div style={{
        height: 160, display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '3.5rem', background: 'var(--grad-primary)', opacity: 0.85,
      }}>{emoji}</div>
      <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ fontWeight: 700, fontSize: '.95rem', lineHeight: 1.3 }}>{book.title}</div>
        <div className="text-sm text-muted">by {book.author}</div>
        {book.year && <div className="text-xs text-muted">{book.publisher} · {book.year}</div>}
        <div className="flex gap-8" style={{ flexWrap: 'wrap' }}>
          <span className={`badge ${available ? 'badge-success' : 'badge-danger'}`}>
            {available ? '✅ Available' : '❌ Borrowed'}
          </span>
          <span className="badge badge-info">{book.category}</span>
        </div>
        <div className="text-xs text-muted">{book.available_copies}/{book.total_copies} copies · {book.location || 'Library'}</div>
        {canBorrow && (
          available
            ? <button className="btn btn-teal btn-sm btn-full" onClick={() => onBorrow(book.id, book.title)}>📖 Borrow</button>
            : <button className="btn btn-ghost btn-sm btn-full" disabled>🔖 Unavailable</button>
        )}
      </div>
    </div>
  )
}

export default function Library() {
  const { user } = useAuth()
  const [books, setBooks] = useState<Book[]>([])
  const [total, setTotal] = useState(0)
  const [borrows, setBorrows] = useState<BorrowRecord[]>([])
  const [categories, setCategories] = useState<{ category: string; count: number }[]>([])
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [availableOnly, setAvailableOnly] = useState(false)
  const [loading, setLoading] = useState(true)

  const fetchBooks = async (s = search, c = category, a = availableOnly) => {
    const params = new URLSearchParams({ page: '1', size: '12' })
    if (s) params.set('search', s)
    if (c) params.set('category', c)
    if (a) params.set('available_only', 'true')
    const r = await api.get<Paginated<Book>>(`/library/catalog?${params}`)
    setBooks(r.data.items); setTotal(r.data.total)
  }

  useEffect(() => {
    setLoading(true)
    Promise.all([
      fetchBooks(),
      api.get<{ category: string; count: number }[]>('/library/categories').then(r => setCategories(r.data)),
      user?.role === 'student'
        ? api.get<BorrowRecord[]>('/library/my-borrows').then(r => setBorrows(r.data)).catch(() => {})
        : Promise.resolve(),
    ]).finally(() => setLoading(false))
  }, [])

  const handleBorrow = async (bookId: number, title: string) => {
    try {
      const r = await api.post<{ message: string }>(`/library/borrow/${bookId}`)
      toast.success(`📚 ${r.data.message}`)
      fetchBooks()
      api.get<BorrowRecord[]>('/library/my-borrows').then(r => setBorrows(r.data))
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Cannot borrow')
    }
  }

  const handleSearch = () => fetchBooks(search, category, availableOnly)

  const activeBorrows = borrows.filter(b => b.status === 'active').length

  if (loading) return <div className="flex justify-center items-center" style={{ height: 300 }}><div className="spinner" /></div>

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-title">📚 Digital Library</div>
        <div className="page-subtitle">Explore {total} books and e-resources</div>
      </div>

      {/* Stats */}
      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(4,1fr)', marginBottom: 24 }}>
        {[
          { icon: '📚', val: total, label: 'Total Books', color: '#8B85FF', bg: 'rgba(108,99,255,.18)', cls: 'stat-purple' },
          { icon: '✅', val: books.filter(b => b.available_copies > 0).length, label: 'Available', color: '#00D4AA', bg: 'rgba(0,212,170,.15)', cls: 'stat-teal' },
          { icon: '📖', val: activeBorrows, label: 'My Borrows', color: '#FF6B6B', bg: 'rgba(255,107,107,.18)', cls: 'stat-coral' },
          { icon: '📂', val: categories.length, label: 'Categories', color: '#FFD700', bg: 'rgba(255,215,0,.1)', cls: 'stat-gold' },
        ].map(s => (
          <div key={s.label} className={`stat-card ${s.cls}`}>
            <div className="stat-icon" style={{ background: s.bg }}>{s.icon}</div>
            <div><div className="stat-value" style={{ color: s.color }}>{s.val}</div><div className="stat-label">{s.label}</div></div>
          </div>
        ))}
      </div>

      {/* Search Bar */}
      <div className="card mb-24">
        <div className="flex gap-12" style={{ flexWrap: 'wrap', alignItems: 'center' }}>
          <input className="form-control" placeholder="🔍 Search title, author, ISBN..."
            value={search} onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            style={{ flex: 1, minWidth: 220 }} />
          <select className="form-control" value={category} onChange={e => setCategory(e.target.value)} style={{ width: 200 }}>
            <option value="">All Categories</option>
            {categories.map(c => <option key={c.category} value={c.category}>{c.category} ({c.count})</option>)}
          </select>
          <label className="flex items-center gap-8 text-sm text-secondary" style={{ cursor: 'pointer' }}>
            <input type="checkbox" checked={availableOnly} onChange={e => setAvailableOnly(e.target.checked)} />
            Available only
          </label>
          <button className="btn btn-primary" onClick={handleSearch}>Search</button>
        </div>
      </div>

      {/* Book Grid */}
      <div className="grid-4">
        {books.map(b => (
          <BookCard key={b.id} book={b} canBorrow={user?.role === 'student'} onBorrow={handleBorrow} />
        ))}
      </div>

      {/* My Borrows Table */}
      {borrows.length > 0 && (
        <div className="card mt-24">
          <div className="card-title mb-16">📖 My Borrowed Books</div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Book</th><th>Author</th><th>Borrowed</th><th>Due Date</th><th>Status</th><th>Fine</th></tr></thead>
              <tbody>
                {borrows.map(b => (
                  <tr key={b.id}>
                    <td style={{ fontWeight: 600 }}>{b.book}</td>
                    <td className="text-muted">{b.author}</td>
                    <td className="text-sm">{new Date(b.borrowed_at).toLocaleDateString()}</td>
                    <td className="text-sm">{new Date(b.due_date).toLocaleDateString()}</td>
                    <td><span className={`badge ${b.status === 'active' ? 'badge-info' : b.status === 'overdue' ? 'badge-danger' : 'badge-success'}`}>{b.status}</span></td>
                    <td style={{ color: b.fine > 0 ? '#FF6B6B' : 'var(--text-muted)' }}>{b.fine > 0 ? `LKR ${b.fine}` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
