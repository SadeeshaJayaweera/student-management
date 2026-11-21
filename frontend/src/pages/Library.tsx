import React, { useEffect, useState } from 'react'
import api from '@/api/client'
import toast from 'react-hot-toast'
import type { Book, BorrowRecord, Paginated, DigitalLibraryResource, LibrarySubjectCollection, LibraryBookmark, DigitalLibraryStats } from '@/types'
import { useAuth } from '@/contexts/AuthContext'

const BOOK_EMOJI: Record<string, string> = {
  'Computer Science': '💻', 'AI/ML': '🤖', Business: '💼', Engineering: '⚙️',
  Databases: '🗄️', Networking: '🌐', 'Data Science': '📊',
  'Software Engineering': '🔧', Mathematics: '📐', Physics: '⚗️',
}

const RESOURCE_ICONS: Record<string, string> = {
  ebook: '📘',
  research_paper: '📑',
  journal_article: '📄',
  thesis: '🎓',
  video_lecture: '🎥',
  audio_resource: '🎧',
}

function BookCard({
  book,
  canBorrow,
  onBorrow,
  onReserve,
}: {
  book: Book
  canBorrow: boolean
  onBorrow: (id: number, title: string) => void
  onReserve: (id: number, title: string) => void
}) {
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
            : <button className="btn btn-secondary btn-sm btn-full" onClick={() => onReserve(book.id, book.title)}>🔖 Reserve Priority Queue</button>
        )}
      </div>
    </div>
  )
}

function DigitalResourceCard({
  res,
  onBookmark,
  onDownload,
  onView,
}: {
  res: DigitalLibraryResource
  onBookmark: (id: number) => void
  onDownload: (id: number, url: string, title: string) => void
  onView: (resource: DigitalLibraryResource) => void
}) {
  const icon = RESOURCE_ICONS[res.resource_type] || '📄'

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      <div
        style={{
          height: 140,
          background: 'linear-gradient(135deg, rgba(59,130,246,0.2) 0%, rgba(147,51,234,0.2) 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '3rem',
          position: 'relative',
        }}
      >
        <span>{icon}</span>
        <button
          onClick={() => onBookmark(res.id)}
          style={{
            position: 'absolute',
            top: 10,
            right: 10,
            background: 'rgba(0,0,0,0.4)',
            border: 'none',
            borderRadius: '50%',
            width: 32,
            height: 32,
            cursor: 'pointer',
            fontSize: '1rem',
            color: res.is_bookmarked ? '#fbbf24' : '#fff',
          }}
          title={res.is_bookmarked ? 'Remove from reading list' : 'Save to reading list'}
        >
          {res.is_bookmarked ? '★' : '☆'}
        </button>
        <span
          style={{
            position: 'absolute',
            bottom: 8,
            left: 10,
            fontSize: '0.68rem',
            fontWeight: 700,
            padding: '2px 6px',
            borderRadius: 4,
            backgroundColor: 'rgba(0,0,0,0.6)',
            color: '#38bdf8',
            textTransform: 'uppercase',
          }}
        >
          {res.file_format} • {res.resource_type.replace('_', ' ')}
        </span>
      </div>

      <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 6, flex: 1 }}>
        <div style={{ fontWeight: 700, fontSize: '0.92rem', lineHeight: 1.3 }}>{res.title}</div>
        <div className="text-xs text-muted">by {res.author} {res.published_year ? `(${res.published_year})` : ''}</div>
        {res.abstract && (
          <p
            className="text-muted"
            style={{
              fontSize: '0.8rem',
              margin: '4px 0 0 0',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
            }}
          >
            {res.abstract}
          </p>
        )}

        <div style={{ marginTop: 'auto', paddingTop: 10 }}>
          <div className="flex gap-6 mb-8" style={{ flexWrap: 'wrap' }}>
            <span className="badge badge-info" style={{ fontSize: '0.7rem' }}>{res.subject_category}</span>
            {res.is_open_access && <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>Open Access</span>}
            <span className="text-muted" style={{ fontSize: '0.7rem', alignSelf: 'center', marginLeft: 'auto' }}>
              👁 {res.view_count} · ⬇ {res.download_count}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => onView(res)}
              style={{ fontSize: '0.78rem' }}
            >
              Preview 📖
            </button>
            <button
              className="btn btn-primary btn-sm"
              onClick={() => onDownload(res.id, res.file_url, res.title)}
              style={{ fontSize: '0.78rem' }}
            >
              Download ⬇
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function Library() {
  const { user } = useAuth()
  const isLibrarianOrAdmin = user?.role === 'librarian' || user?.role === 'admin'

  // Tab: 'books' | 'digital' | 'reading_list'
  const [activeTab, setActiveTab] = useState<'books' | 'digital' | 'reading_list'>('digital')

  // Classic books state
  const [books, setBooks] = useState<Book[]>([])
  const [total, setTotal] = useState(0)
  const [borrows, setBorrows] = useState<BorrowRecord[]>([])
  const [categories, setCategories] = useState<{ category: string; count: number }[]>([])
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [availableOnly, setAvailableOnly] = useState(false)

  // Digital repository state
  const [digitalResources, setDigitalResources] = useState<DigitalLibraryResource[]>([])
  const [digitalType, setDigitalType] = useState<string>('all')
  const [digitalFormat, setDigitalFormat] = useState<string>('all')
  const [digitalQuery, setDigitalQuery] = useState<string>('')
  const [collections, setCollections] = useState<LibrarySubjectCollection[]>([])
  const [selectedCollection, setSelectedCollection] = useState<number | null>(null)
  const [bookmarks, setBookmarks] = useState<LibraryBookmark[]>([])
  const [stats, setStats] = useState<DigitalLibraryStats | null>(null)

  // Modals & view state
  const [loading, setLoading] = useState(true)
  const [previewResource, setPreviewResource] = useState<DigitalLibraryResource | null>(null)
  const [showAddModal, setShowAddModal] = useState<boolean>(false)

  // New digital resource form
  const [newTitle, setNewTitle] = useState('')
  const [newAuthor, setNewAuthor] = useState('')
  const [newType, setNewType] = useState('ebook')
  const [newCategory, setNewCategory] = useState('Computer Science')
  const [newFormat, setNewFormat] = useState('pdf')
  const [newUrl, setNewUrl] = useState('')
  const [newAbstract, setNewAbstract] = useState('')
  const [newYear, setNewYear] = useState<number>(2026)
  const [savingResource, setSavingResource] = useState(false)

  const fetchBooks = async (s = search, c = category, a = availableOnly) => {
    const params = new URLSearchParams({ page: '1', size: '12' })
    if (s) params.set('search', s)
    if (c) params.set('category', c)
    if (a) params.set('available_only', 'true')
    try {
      const r = await api.get<Paginated<Book>>(`/library/catalog?${params}`)
      setBooks(r.data.items)
      setTotal(r.data.total)
    } catch (e) {
      console.error(e)
    }
  }

  const fetchDigitalResources = async () => {
    try {
      const params = new URLSearchParams({ limit: '30' })
      if (digitalQuery) params.set('query', digitalQuery)
      if (digitalType && digitalType !== 'all') params.set('resource_type', digitalType)
      if (digitalFormat && digitalFormat !== 'all') params.set('file_format', digitalFormat)
      if (selectedCollection) params.set('collection_id', String(selectedCollection))

      const [resR, colR, statsR] = await Promise.all([
        api.get<DigitalLibraryResource[]>(`/digital-library/catalog?${params}`),
        api.get<LibrarySubjectCollection[]>('/digital-library/collections'),
        api.get<DigitalLibraryStats>('/digital-library/stats'),
      ])
      setDigitalResources(resR.data)
      setCollections(colR.data)
      setStats(statsR.data)
    } catch (e) {
      console.error('Failed to load digital resources', e)
    }
  }

  const fetchBookmarks = async () => {
    try {
      const r = await api.get<LibraryBookmark[]>('/digital-library/my-bookmarks')
      setBookmarks(r.data)
    } catch (e) {
      console.error('Failed to load bookmarks', e)
    }
  }

  useEffect(() => {
    setLoading(true)
    Promise.all([
      fetchBooks(),
      fetchDigitalResources(),
      fetchBookmarks(),
      api.get<{ category: string; count: number }[]>('/library/categories').then(r => setCategories(r.data)).catch(() => {}),
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
      api.get<BorrowRecord[]>('/library/my-borrows').then(r => setBorrows(r.data)).catch(() => {})
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Cannot borrow')
    }
  }

  const handleRenew = async (borrowId: number) => {
    try {
      await api.post(`/circulation/renew/${borrowId}`)
      toast.success('Book loan renewed for an additional 14 days!')
      api.get<BorrowRecord[]>('/library/my-borrows').then(r => setBorrows(r.data)).catch(() => {})
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Cannot renew loan.')
    }
  }

  const handleReturn = async (borrowId: number) => {
    try {
      await api.post(`/circulation/return/${borrowId}`)
      toast.success('Book returned successfully!')
      fetchBooks()
      api.get<BorrowRecord[]>('/library/my-borrows').then(r => setBorrows(r.data)).catch(() => {})
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to process return.')
    }
  }

  const handleReserve = async (bookId: number, title: string) => {
    try {
      const res = await api.post<{ priority_number: number }>(`/circulation/reserve/${bookId}`)
      toast.success(`Book reserved! You are priority #${res.data.priority_number} in queue.`)
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to place reservation.')
    }
  }

  const handleBookmarkToggle = async (resourceId: number) => {
    try {
      const res = await api.post<{ bookmarked: boolean; message: string }>(`/digital-library/catalog/${resourceId}/bookmark`)
      toast.success(res.data.message)
      setDigitalResources(prev =>
        prev.map(r => r.id === resourceId ? { ...r, is_bookmarked: res.data.bookmarked } : r)
      )
      fetchBookmarks()
    } catch (e: any) {
      toast.error('Failed to update bookmark')
    }
  }

  const handleDownload = async (resourceId: number, url: string, title: string) => {
    try {
      await api.post(`/digital-library/catalog/${resourceId}/download`)
      toast.success(`Downloading ${title}`)
      setDigitalResources(prev =>
        prev.map(r => r.id === resourceId ? { ...r, download_count: r.download_count + 1 } : r)
      )
      window.open(url, '_blank')
    } catch (e) {
      window.open(url, '_blank')
    }
  }

  const handleViewPreview = async (res: DigitalLibraryResource) => {
    try {
      const updated = await api.get<DigitalLibraryResource>(`/digital-library/catalog/${res.id}`)
      setPreviewResource(updated.data)
      setDigitalResources(prev =>
        prev.map(r => r.id === res.id ? { ...r, view_count: updated.data.view_count } : r)
      )
    } catch {
      setPreviewResource(res)
    }
  }

  const handleCreateResource = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTitle.trim() || !newAuthor.trim() || !newUrl.trim() || savingResource) return

    try {
      setSavingResource(true)
      await api.post('/digital-library/catalog', {
        title: newTitle.trim(),
        author: newAuthor.trim(),
        resource_type: newType,
        subject_category: newCategory,
        file_format: newFormat,
        file_url: newUrl.trim(),
        abstract: newAbstract.trim() || undefined,
        published_year: newYear,
        is_open_access: true,
      })
      toast.success('Digital asset published successfully!')
      setShowAddModal(false)
      fetchDigitalResources()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to publish resource.')
    } finally {
      setSavingResource(false)
    }
  }

  const activeBorrows = borrows.filter(b => b.status === 'active').length

  if (loading) return <div className="flex justify-center items-center" style={{ height: 300 }}><div className="spinner" /></div>

  return (
    <div className="fade-in" style={{ maxWidth: 1200, margin: '0 auto', paddingBottom: 40 }}>
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <div className="page-title">📚 NSBM Modern Digital Library & Repository</div>
          <div className="page-subtitle">
            Academic physical library, digital research papers, open-access e-books, and multimedia archives.
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          {isLibrarianOrAdmin && (
            <button
              className="btn btn-primary"
              onClick={() => setShowAddModal(true)}
              style={{ display: 'flex', alignItems: 'center', gap: 6 }}
            >
              <span>➕</span> Publish Digital Asset
            </button>
          )}
        </div>
      </div>

      {/* KPI Stats Banner */}
      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', marginBottom: 24 }}>
        <div className="stat-card stat-purple">
          <div className="stat-icon" style={{ background: 'rgba(108,99,255,.18)' }}>📚</div>
          <div>
            <div className="stat-value" style={{ color: '#8B85FF' }}>
              {(stats?.total_resources || 0) + total}
            </div>
            <div className="stat-label">Catalog Holdings</div>
          </div>
        </div>
        <div className="stat-card stat-teal">
          <div className="stat-icon" style={{ background: 'rgba(0,212,170,.15)' }}>👁</div>
          <div>
            <div className="stat-value" style={{ color: '#00D4AA' }}>{stats?.total_views || 0}</div>
            <div className="stat-label">Repository Views</div>
          </div>
        </div>
        <div className="stat-card stat-coral">
          <div className="stat-icon" style={{ background: 'rgba(255,107,107,.18)' }}>⬇</div>
          <div>
            <div className="stat-value" style={{ color: '#FF6B6B' }}>{stats?.total_downloads || 0}</div>
            <div className="stat-label">Downloads & Streams</div>
          </div>
        </div>
        <div className="stat-card stat-gold">
          <div className="stat-icon" style={{ background: 'rgba(255,215,0,.1)' }}>🔖</div>
          <div>
            <div className="stat-value" style={{ color: '#FFD700' }}>{bookmarks.length}</div>
            <div className="stat-label">My Reading List</div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div style={{ display: 'flex', gap: 10, borderBottom: '1px solid var(--border-color)', marginBottom: 20 }}>
        <button
          onClick={() => setActiveTab('digital')}
          style={{
            padding: '10px 18px',
            border: 'none',
            background: 'none',
            fontWeight: 700,
            fontSize: '0.92rem',
            cursor: 'pointer',
            borderBottom: activeTab === 'digital' ? '2px solid #38bdf8' : '2px solid transparent',
            color: activeTab === 'digital' ? '#38bdf8' : 'var(--text-muted)',
          }}
        >
          🌐 Digital Repository & E-Books ({digitalResources.length})
        </button>
        <button
          onClick={() => setActiveTab('books')}
          style={{
            padding: '10px 18px',
            border: 'none',
            background: 'none',
            fontWeight: 700,
            fontSize: '0.92rem',
            cursor: 'pointer',
            borderBottom: activeTab === 'books' ? '2px solid #38bdf8' : '2px solid transparent',
            color: activeTab === 'books' ? '#38bdf8' : 'var(--text-muted)',
          }}
        >
          📖 Physical Library & Circulation ({total})
        </button>
        <button
          onClick={() => setActiveTab('reading_list')}
          style={{
            padding: '10px 18px',
            border: 'none',
            background: 'none',
            fontWeight: 700,
            fontSize: '0.92rem',
            cursor: 'pointer',
            borderBottom: activeTab === 'reading_list' ? '2px solid #38bdf8' : '2px solid transparent',
            color: activeTab === 'reading_list' ? '#38bdf8' : 'var(--text-muted)',
          }}
        >
          ★ Saved Reading List ({bookmarks.length})
        </button>
      </div>

      {/* TAB 1: Digital Repository */}
      {activeTab === 'digital' && (
        <div>
          {/* Institutional Collections Drawer */}
          {collections.length > 0 && (
            <div style={{ display: 'flex', gap: 10, overflowX: 'auto', paddingBottom: 12, marginBottom: 16 }}>
              <button
                onClick={() => { setSelectedCollection(null); fetchDigitalResources(); }}
                style={{
                  padding: '6px 14px',
                  borderRadius: 20,
                  border: selectedCollection === null ? '1px solid #38bdf8' : '1px solid var(--border-color)',
                  backgroundColor: selectedCollection === null ? 'rgba(56,189,248,0.15)' : 'transparent',
                  color: selectedCollection === null ? '#38bdf8' : 'var(--text-muted)',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                }}
              >
                All Collections
              </button>
              {collections.map(c => (
                <button
                  key={c.id}
                  onClick={() => { setSelectedCollection(c.id); fetchDigitalResources(); }}
                  style={{
                    padding: '6px 14px',
                    borderRadius: 20,
                    border: selectedCollection === c.id ? '1px solid #38bdf8' : '1px solid var(--border-color)',
                    backgroundColor: selectedCollection === c.id ? 'rgba(56,189,248,0.15)' : 'transparent',
                    color: selectedCollection === c.id ? '#38bdf8' : 'var(--text-muted)',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {c.icon} {c.title}
                </button>
              ))}
            </div>
          )}

          {/* Search and Filters */}
          <div className="card mb-20" style={{ padding: 16 }}>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
              <input
                className="form-control"
                placeholder="🔍 Search digital papers, e-books, theses, keywords..."
                value={digitalQuery}
                onChange={e => setDigitalQuery(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && fetchDigitalResources()}
                style={{ flex: 1, minWidth: 240 }}
              />
              <select
                className="form-control"
                value={digitalType}
                onChange={e => { setDigitalType(e.target.value); }}
                style={{ width: 170 }}
              >
                <option value="all">All Types</option>
                <option value="ebook">E-Books</option>
                <option value="research_paper">Research Papers</option>
                <option value="journal_article">Journal Articles</option>
                <option value="thesis">Theses & Dissertations</option>
                <option value="video_lecture">Video Lectures</option>
              </select>
              <select
                className="form-control"
                value={digitalFormat}
                onChange={e => { setDigitalFormat(e.target.value); }}
                style={{ width: 130 }}
              >
                <option value="all">All Formats</option>
                <option value="pdf">PDF</option>
                <option value="epub">ePub</option>
                <option value="mp4">MP4 Video</option>
              </select>
              <button className="btn btn-primary" onClick={fetchDigitalResources}>
                Filter Catalog
              </button>
            </div>
          </div>

          {/* Digital Resources Grid */}
          {digitalResources.length === 0 ? (
            <div className="card" style={{ padding: 48, textAlign: 'center' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: 10 }}>📑</div>
              <h4 style={{ margin: 0, fontWeight: 700 }}>No Digital Resources Found</h4>
              <p className="text-muted" style={{ margin: '6px 0 0 0', fontSize: '0.88rem' }}>
                Try adjusting your search criteria or filter options.
              </p>
            </div>
          ) : (
            <div className="grid-4">
              {digitalResources.map(r => (
                <DigitalResourceCard
                  key={r.id}
                  res={r}
                  onBookmark={handleBookmarkToggle}
                  onDownload={handleDownload}
                  onView={handleViewPreview}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Physical Library */}
      {activeTab === 'books' && (
        <div>
          <div className="card mb-24">
            <div className="flex gap-12" style={{ flexWrap: 'wrap', alignItems: 'center' }}>
              <input
                className="form-control"
                placeholder="🔍 Search title, author, ISBN..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && fetchBooks(search, category, availableOnly)}
                style={{ flex: 1, minWidth: 220 }}
              />
              <select className="form-control" value={category} onChange={e => { setCategory(e.target.value); fetchBooks(search, e.target.value, availableOnly); }} style={{ width: 200 }}>
                <option value="">All Categories</option>
                {categories.map(c => <option key={c.category} value={c.category}>{c.category} ({c.count})</option>)}
              </select>
              <label className="flex items-center gap-8 text-sm text-secondary" style={{ cursor: 'pointer' }}>
                <input type="checkbox" checked={availableOnly} onChange={e => { setAvailableOnly(e.target.checked); fetchBooks(search, category, e.target.checked); }} />
                Available only
              </label>
              <button className="btn btn-primary" onClick={() => fetchBooks(search, category, availableOnly)}>Search</button>
            </div>
          </div>

          <div className="grid-4">
            {books.map(b => (
              <BookCard
                key={b.id}
                book={b}
                canBorrow={user?.role === 'student'}
                onBorrow={handleBorrow}
                onReserve={handleReserve}
              />
            ))}
          </div>

          {borrows.length > 0 && (
            <div className="card mt-24">
              <div className="card-title mb-16">📖 My Borrowed Books & Active Loans</div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Book</th>
                      <th>Author</th>
                      <th>Borrowed</th>
                      <th>Due Date</th>
                      <th>Status</th>
                      <th>Fine</th>
                      <th style={{ textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {borrows.map(b => (
                      <tr key={b.id}>
                        <td style={{ fontWeight: 600 }}>{b.book}</td>
                        <td className="text-muted">{b.author}</td>
                        <td className="text-sm">{new Date(b.borrowed_at).toLocaleDateString()}</td>
                        <td className="text-sm">{new Date(b.due_date).toLocaleDateString()}</td>
                        <td><span className={`badge ${b.status === 'active' ? 'badge-info' : b.status === 'overdue' ? 'badge-danger' : 'badge-success'}`}>{b.status}</span></td>
                        <td style={{ color: b.fine > 0 ? '#FF6B6B' : 'var(--text-muted)' }}>{b.fine > 0 ? `LKR ${b.fine}` : '—'}</td>
                        <td style={{ textAlign: 'right' }}>
                          <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
                            {b.status === 'active' && (
                              <button
                                onClick={() => handleRenew(b.id)}
                                className="btn btn-secondary btn-sm"
                                style={{ fontSize: '0.75rem', padding: '3px 8px' }}
                              >
                                Renew 🔄
                              </button>
                            )}
                            {(b.status === 'active' || b.status === 'overdue') && (
                              <button
                                onClick={() => handleReturn(b.id)}
                                className="btn btn-teal btn-sm"
                                style={{ fontSize: '0.75rem', padding: '3px 8px' }}
                              >
                                Return 📥
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
          )}
        </div>
      )}

      {/* TAB 3: Saved Reading List */}
      {activeTab === 'reading_list' && (
        <div>
          {bookmarks.length === 0 ? (
            <div className="card" style={{ padding: 48, textAlign: 'center' }}>
              <div style={{ fontSize: '2.5rem', marginBottom: 10 }}>🔖</div>
              <h4 style={{ margin: 0, fontWeight: 700 }}>Your Reading List is Empty</h4>
              <p className="text-muted" style={{ margin: '6px 0 0 0', fontSize: '0.88rem' }}>
                Save articles, e-books, and research papers from the Digital Repository to study later.
              </p>
            </div>
          ) : (
            <div className="grid-4">
              {bookmarks.map(bm => (
                <DigitalResourceCard
                  key={bm.id}
                  res={bm.resource}
                  onBookmark={handleBookmarkToggle}
                  onDownload={handleDownload}
                  onView={handleViewPreview}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* E-Reader / PDF Digital Asset Preview Modal */}
      {previewResource && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            backdropFilter: 'blur(5px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
          }}
        >
          <div className="card" style={{ width: '100%', maxWidth: 720, maxHeight: '90vh', overflowY: 'auto', padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
              <div>
                <span className="badge badge-info" style={{ textTransform: 'uppercase', fontSize: '0.75rem' }}>
                  {previewResource.resource_type.replace('_', ' ')} · {previewResource.file_format}
                </span>
                <h3 style={{ margin: '8px 0 4px 0', fontSize: '1.4rem', fontWeight: 800 }}>{previewResource.title}</h3>
                <div className="text-muted" style={{ fontSize: '0.85rem' }}>
                  by {previewResource.author} • {previewResource.publisher || 'NSBM Press'} ({previewResource.published_year})
                </div>
              </div>
              <button
                type="button"
                onClick={() => setPreviewResource(null)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '1.4rem' }}
              >
                ✕
              </button>
            </div>

            {previewResource.doi_or_issn && (
              <div style={{ fontSize: '0.8rem', color: '#38bdf8', marginBottom: 12 }}>
                DOI / Identifier: {previewResource.doi_or_issn}
              </div>
            )}

            <div style={{ marginBottom: 16, padding: 14, backgroundColor: 'rgba(255, 255, 255, 0.02)', borderRadius: 8, border: '1px solid var(--border-color)' }}>
              <div style={{ fontWeight: 700, fontSize: '0.88rem', marginBottom: 6 }}>Abstract / Synopsis</div>
              <p style={{ margin: 0, fontSize: '0.86rem', lineHeight: 1.5, color: '#cbd5e1' }}>
                {previewResource.abstract || 'No abstract available for this resource.'}
              </p>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 24 }}>
              <button
                type="button"
                onClick={() => handleBookmarkToggle(previewResource.id)}
                className="btn btn-secondary"
                style={{ fontSize: '0.85rem' }}
              >
                {previewResource.is_bookmarked ? '★ Remove from Reading List' : '☆ Save to Reading List'}
              </button>

              <div style={{ display: 'flex', gap: 10 }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setPreviewResource(null)}
                >
                  Close
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => handleDownload(previewResource.id, previewResource.file_url, previewResource.title)}
                >
                  Open / Download Document ⬇
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Librarian Publish Resource Modal */}
      {showAddModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            backdropFilter: 'blur(5px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
          }}
        >
          <div className="card" style={{ width: '100%', maxWidth: 560, padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ margin: 0, fontSize: '1.3rem', fontWeight: 800 }}>Publish Digital Asset</h3>
              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '1.2rem' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateResource}>
              <div style={{ marginBottom: 12 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Publication Title *
                </label>
                <input
                  type="text"
                  className="form-control"
                  value={newTitle}
                  onChange={e => setNewTitle(e.target.value)}
                  placeholder="e.g. Clean Architecture in Python"
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                    Author / Lead Researcher *
                  </label>
                  <input
                    type="text"
                    className="form-control"
                    value={newAuthor}
                    onChange={e => setNewAuthor(e.target.value)}
                    placeholder="e.g. Dr. Robert Martin"
                    required
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                    Resource Type
                  </label>
                  <select
                    className="form-control"
                    value={newType}
                    onChange={e => setNewType(e.target.value)}
                  >
                    <option value="ebook">E-Book</option>
                    <option value="research_paper">Research Paper</option>
                    <option value="journal_article">Journal Article</option>
                    <option value="thesis">Thesis</option>
                    <option value="video_lecture">Video Lecture</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                    Subject Category
                  </label>
                  <input
                    type="text"
                    className="form-control"
                    value={newCategory}
                    onChange={e => setNewCategory(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                    File Format
                  </label>
                  <select
                    className="form-control"
                    value={newFormat}
                    onChange={e => setNewFormat(e.target.value)}
                  >
                    <option value="pdf">PDF</option>
                    <option value="epub">ePub</option>
                    <option value="mp4">MP4 Video</option>
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: 12 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Digital Asset URL (or Cloud Storage Link) *
                </label>
                <input
                  type="url"
                  className="form-control"
                  value={newUrl}
                  onChange={e => setNewUrl(e.target.value)}
                  placeholder="https://edusphere.nsbm.ac.lk/assets/paper.pdf"
                  required
                />
              </div>

              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Abstract / Executive Summary
                </label>
                <textarea
                  className="form-control"
                  rows={3}
                  value={newAbstract}
                  onChange={e => setNewAbstract(e.target.value)}
                  placeholder="Overview of the publication..."
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowAddModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={savingResource}>
                  {savingResource ? 'Publishing...' : 'Publish Asset'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
