import React, { useEffect, useState } from 'react'
import api from '@/api/client'
import toast from 'react-hot-toast'
import type { NewsArticle, MediaGalleryItem, NewsPublicationStats } from '@/types'
import { useAuth } from '@/contexts/AuthContext'

const CAT_COLOR: Record<string, string> = {
  academic: '#6C63FF',
  sports: '#FF6B6B',
  events: '#00D4AA',
  alumni: '#FFD700',
  research: '#FF64C8',
  general: '#FFB347',
}

const CAT_EMOJI: Record<string, string> = {
  academic: '📖',
  sports: '⚽',
  events: '🎉',
  alumni: '🌐',
  research: '🔬',
  general: '📰',
}

function NewsCard({ article, onClick }: { article: NewsArticle; onClick: () => void }) {
  const color = CAT_COLOR[article.category] || '#6C63FF'
  const emoji = CAT_EMOJI[article.category] || '📰'
  const authorName = article.author_name || article.author || 'University Editorial Desk'
  const publishedDate = article.published_at ? new Date(article.published_at).toLocaleDateString() : 'Draft'

  return (
    <div className="news-card" onClick={onClick} style={{ cursor: 'pointer' }}>
      <div
        className="news-card-img"
        style={{
          background: article.cover_image_url
            ? `url(${article.cover_image_url}) center/cover no-repeat`
            : `linear-gradient(135deg, ${color}28, ${color}0d)`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          height: 160,
          borderRadius: '8px 8px 0 0',
        }}
      >
        {!article.cover_image_url && <span style={{ fontSize: '3rem' }}>{emoji}</span>}
      </div>
      <div className="news-card-body" style={{ padding: '16px' }}>
        <div className="flex justify-between items-center mb-8">
          <div className="news-card-category" style={{ color, fontWeight: 700, fontSize: '.75rem', textTransform: 'uppercase' }}>
            {article.category}
          </div>
          {article.is_featured && <span className="badge badge-gold" style={{ fontSize: '.7rem' }}>⭐ Featured</span>}
        </div>
        <div className="news-card-title" style={{ fontWeight: 700, fontSize: '1.05rem', marginBottom: 8, lineHeight: 1.35 }}>
          {article.title}
        </div>
        {article.summary && (
          <div className="text-sm text-muted mb-16" style={{ lineHeight: 1.5 }}>
            {article.summary.slice(0, 110)}...
          </div>
        )}
        <div className="news-card-meta flex justify-between items-center text-xs text-muted mt-12" style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 10 }}>
          <span>✍️ {authorName}</span>
          <div className="flex gap-8">
            <span>👁️ {article.views}</span>
            <span>❤️ {article.likes_count ?? 0}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function ArticleDetailView({
  articleId,
  onBack,
  onRefreshList,
}: {
  articleId: number
  onBack: () => void
  onRefreshList: () => void
}) {
  const { user } = useAuth()
  const [article, setArticle] = useState<NewsArticle | null>(null)
  const [comment, setComment] = useState('')
  const [submittingComment, setSubmittingComment] = useState(false)
  const [togglingReaction, setTogglingReaction] = useState(false)
  const [showMediaModal, setShowMediaModal] = useState(false)
  const [mediaTitle, setMediaTitle] = useState('')
  const [mediaUrl, setMediaUrl] = useState('')
  const [mediaType, setMediaType] = useState('image')
  const [mediaCaption, setMediaCaption] = useState('')

  const loadArticle = async () => {
    try {
      const res = await api.get<NewsArticle>(`/news-publication/articles/${articleId}`)
      setArticle(res.data)
    } catch {
      // Fallback
      try {
        const res2 = await api.get<NewsArticle>(`/news/${articleId}`)
        setArticle(res2.data)
      } catch (err: any) {
        toast.error(err.response?.data?.detail || 'Failed to load article')
      }
    }
  }

  useEffect(() => {
    loadArticle()
  }, [articleId])

  const handleToggleLike = async () => {
    if (togglingReaction || !article) return
    setTogglingReaction(true)
    try {
      const res = await api.post<{ liked: boolean; likes_count: number }>(`/news-publication/articles/${article.id}/react`)
      setArticle({
        ...article,
        user_has_liked: res.data.liked,
        likes_count: res.data.likes_count,
      })
      toast.success(res.data.liked ? '❤️ Applauded story!' : '🤍 Reaction removed')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Error toggling reaction')
    } finally {
      setTogglingReaction(false)
    }
  }

  const postComment = async () => {
    if (!comment.trim() || !article) return
    setSubmittingComment(true)
    try {
      await api.post(`/news-publication/articles/${article.id}/comments`, { content: comment.trim() })
      toast.success('💬 Comment published!')
      setComment('')
      loadArticle()
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Could not post comment')
    } finally {
      setSubmittingComment(false)
    }
  }

  const handlePublishStory = async () => {
    if (!article) return
    try {
      await api.put(`/news-publication/articles/${article.id}/publish`)
      toast.success('🎉 Article officially published to campus network!')
      loadArticle()
      onRefreshList()
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to publish story')
    }
  }

  const handleAddMedia = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!article || !mediaUrl.trim() || !mediaTitle.trim()) return
    try {
      await api.post(`/news-publication/articles/${article.id}/media`, {
        title: mediaTitle.trim(),
        media_url: mediaUrl.trim(),
        media_type: mediaType,
        caption: mediaCaption.trim() || undefined,
        sort_order: (article.gallery?.length ?? 0) + 1,
      })
      toast.success('📸 Rich media asset attached!')
      setShowMediaModal(false)
      setMediaTitle('')
      setMediaUrl('')
      setMediaCaption('')
      loadArticle()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to attach media')
    }
  }

  if (!article) {
    return (
      <div className="flex justify-center items-center" style={{ height: 350 }}>
        <div className="spinner" />
      </div>
    )
  }

  const color = CAT_COLOR[article.category] || '#6C63FF'
  const authorName = article.author_name || article.author || 'University Press Team'
  const canManage = ['admin', 'lecturer'].includes(user?.role ?? '') || article.author_id === user?.id

  return (
    <div className="fade-in">
      <div className="flex justify-between items-center mb-16">
        <button className="btn btn-ghost btn-sm" onClick={onBack}>
          ← Back to Campus News
        </button>
        <div className="flex gap-8">
          {canManage && (
            <button className="btn btn-secondary btn-sm" onClick={() => setShowMediaModal(true)}>
              📷 Add Photo / Video
            </button>
          )}
          {['admin', 'lecturer'].includes(user?.role ?? '') && article.status !== 'published' && (
            <button className="btn btn-primary btn-sm" onClick={handlePublishStory}>
              🚀 Approve & Publish
            </button>
          )}
        </div>
      </div>

      <div className="card" style={{ maxWidth: 860, margin: '0 auto', overflow: 'hidden' }}>
        {article.cover_image_url && (
          <div style={{ margin: '-24px -24px 24px -24px', maxHeight: 340, overflow: 'hidden' }}>
            <img src={article.cover_image_url} alt={article.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          </div>
        )}

        <div className="flex items-center gap-8 mb-16 flex-wrap">
          <span className="badge" style={{ background: `${color}20`, color, borderColor: `${color}44` }}>
            {article.category.toUpperCase()}
          </span>
          <span className="badge badge-info">{article.target_audience ?? 'Campus Wide'}</span>
          {article.is_featured && <span className="badge badge-gold">⭐ Featured Spotlight</span>}
          {article.status && article.status !== 'published' && (
            <span className="badge badge-warning">Status: {article.status}</span>
          )}
        </div>

        <h1 style={{ fontFamily: "'Outfit',sans-serif", fontSize: '2.1rem', fontWeight: 800, lineHeight: 1.3, marginBottom: 16 }}>
          {article.title}
        </h1>

        <div className="flex gap-16 mb-24 text-sm text-muted" style={{ flexWrap: 'wrap', borderBottom: '1px solid var(--border)', paddingBottom: 16 }}>
          <span>✍️ {authorName}</span>
          <span>📅 {article.published_at ? new Date(article.published_at).toLocaleDateString() : 'Draft'}</span>
          <span>👁️ {article.views} reads</span>
          <span>❤️ {article.likes_count ?? 0} applauds</span>
        </div>

        {article.summary && (
          <div
            style={{
              padding: '14px 18px',
              borderRadius: 8,
              background: 'rgba(255,255,255,0.03)',
              borderLeft: `4px solid ${color}`,
              marginBottom: 24,
              fontStyle: 'italic',
              fontSize: '1.05rem',
              color: 'rgba(255,255,255,0.85)',
            }}
          >
            {article.summary}
          </div>
        )}

        <div
          style={{
            lineHeight: 1.9,
            color: 'rgba(255,255,255,.88)',
            fontSize: '1rem',
            whiteSpace: 'pre-line',
            marginBottom: 32,
          }}
        >
          {article.content}
        </div>

        {/* Media Gallery */}
        {article.gallery && article.gallery.length > 0 && (
          <div style={{ marginTop: 28, marginBottom: 32, borderTop: '1px solid var(--border)', paddingTop: 24 }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: 16 }}>📸 Media Gallery</h3>
            <div className="grid-3" style={{ gap: 14 }}>
              {article.gallery.map((item: MediaGalleryItem) => (
                <div key={item.id} className="card" style={{ padding: 10, background: 'rgba(255,255,255,0.02)' }}>
                  {item.media_type === 'video' ? (
                    <video controls src={item.media_url} style={{ width: '100%', borderRadius: 6, maxHeight: 180 }} />
                  ) : (
                    <img src={item.media_url} alt={item.title} style={{ width: '100%', height: 140, objectFit: 'cover', borderRadius: 6 }} />
                  )}
                  <div style={{ fontWeight: 600, fontSize: '.85rem', marginTop: 8 }}>{item.title}</div>
                  {item.caption && <div className="text-xs text-muted mt-4">{item.caption}</div>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Reactions Section */}
        <div className="flex justify-between items-center py-16" style={{ borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)' }}>
          <div className="flex items-center gap-12">
            <button
              className={`btn btn-sm ${article.user_has_liked ? 'btn-primary' : 'btn-secondary'}`}
              onClick={handleToggleLike}
              disabled={togglingReaction}
            >
              {article.user_has_liked ? '❤️ Applauded' : '🤍 Applaud Story'} ({article.likes_count ?? 0})
            </button>
            <span className="text-sm text-muted">Join other readers in engaging with this story</span>
          </div>
          <span className="text-xs text-muted">Campus Press Editorial Code</span>
        </div>

        {/* Comments Section */}
        <div style={{ marginTop: 28 }}>
          <div style={{ fontWeight: 700, fontSize: '1.1rem', marginBottom: 18 }}>
            💬 Reader Discussion ({article.comments?.length ?? 0})
          </div>

          {article.comments && article.comments.length > 0 ? (
            article.comments.map((c) => {
              const commenterName = c.user_name || c.user?.full_name || 'Campus Reader'
              return (
                <div key={c.id} className="flex gap-12 mb-16 pb-16" style={{ borderBottom: '1px solid rgba(255,255,255,.05)' }}>
                  <div className="avatar avatar-sm" style={{ background: 'var(--primary)', color: '#fff' }}>
                    {commenterName[0].toUpperCase()}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: '.875rem' }}>
                      {commenterName} <span className="text-xs text-muted ml-8">{new Date(c.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="text-sm text-secondary mt-4" style={{ lineHeight: 1.5 }}>
                      {c.content}
                    </div>
                  </div>
                </div>
              )
            })
          ) : (
            <div className="text-sm text-muted mb-16">No comments yet. Share your thoughts below!</div>
          )}

          <div className="flex gap-12 mt-20">
            <input
              className="form-control"
              placeholder="Join the discussion… Write a comment"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              style={{ flex: 1 }}
              onKeyDown={(e) => e.key === 'Enter' && postComment()}
            />
            <button className="btn btn-primary" onClick={postComment} disabled={submittingComment || !comment.trim()}>
              {submittingComment ? 'Posting…' : 'Comment'}
            </button>
          </div>
        </div>
      </div>

      {/* Media Modal */}
      {showMediaModal && (
        <div className="modal-backdrop">
          <div className="modal-box" style={{ maxWidth: 520 }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontWeight: 700 }}>Attach Rich Media</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowMediaModal(false)}>✕</button>
            </div>
            <form onSubmit={handleAddMedia}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div>
                  <label className="text-xs text-muted mb-4 block">Asset Title *</label>
                  <input
                    className="form-control w-full"
                    placeholder="e.g. Campus Innovation Hub Ribbon Cutting"
                    value={mediaTitle}
                    onChange={(e) => setMediaTitle(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="text-xs text-muted mb-4 block">Asset Type</label>
                  <select className="form-control w-full" value={mediaType} onChange={(e) => setMediaType(e.target.value)}>
                    <option value="image">Image / Photograph</option>
                    <option value="video">Video Stream / MP4</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-muted mb-4 block">Asset Public URL *</label>
                  <input
                    className="form-control w-full"
                    placeholder="https://..."
                    value={mediaUrl}
                    onChange={(e) => setMediaUrl(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="text-xs text-muted mb-4 block">Caption / Credit (Optional)</label>
                  <input
                    className="form-control w-full"
                    placeholder="e.g. Photo by Campus Media Guild"
                    value={mediaCaption}
                    onChange={(e) => setMediaCaption(e.target.value)}
                  />
                </div>
              </div>
              <div className="modal-footer flex justify-end gap-12 mt-16">
                <button type="button" className="btn btn-ghost" onClick={() => setShowMediaModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Attach Asset
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default function News() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<'feed' | 'editorial' | 'stats'>('feed')
  const [articles, setArticles] = useState<NewsArticle[]>([])
  const [editorialArticles, setEditorialArticles] = useState<NewsArticle[]>([])
  const [stats, setStats] = useState<NewsPublicationStats | null>(null)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState<number | null>(null)

  // Write Article Modal
  const [showWriteModal, setShowWriteModal] = useState(false)
  const [writeTitle, setWriteTitle] = useState('')
  const [writeCategory, setWriteCategory] = useState('general')
  const [writeTargetAudience, setWriteTargetAudience] = useState('all')
  const [writeSummary, setWriteSummary] = useState('')
  const [writeContent, setWriteContent] = useState('')
  const [writeCoverUrl, setWriteCoverUrl] = useState('')
  const [writeIsFeatured, setWriteIsFeatured] = useState(false)
  const [submittingArticle, setSubmittingArticle] = useState(false)

  const fetchPublishedArticles = async (s = search, c = category) => {
    try {
      const params = new URLSearchParams()
      params.set('status_filter', 'published')
      if (s) params.set('query', s)
      if (c) params.set('category', c)
      const r = await api.get<NewsArticle[]>(`/news-publication/articles?${params}`)
      setArticles(r.data)
    } catch {
      // Fallback
      try {
        const params2 = new URLSearchParams({ page: '1', size: '20' })
        if (s) params2.set('search', s)
        if (c) params2.set('category', c)
        const r2 = await api.get<{ items: NewsArticle[] }>(`/news?${params2}`)
        setArticles(r2.data.items)
      } catch (e: any) {
        toast.error('Failed to load campus feed')
      }
    }
  }

  const fetchEditorialDesk = async () => {
    if (!['admin', 'lecturer'].includes(user?.role ?? '')) return
    try {
      const r = await api.get<NewsArticle[]>(`/news-publication/articles?status_filter=all`)
      setEditorialArticles(r.data)
    } catch {
      // Ignore
    }
  }

  const fetchStats = async () => {
    try {
      const r = await api.get<NewsPublicationStats>('/news-publication/stats')
      setStats(r.data)
    } catch {
      // Ignore
    }
  }

  const refreshAll = async () => {
    setLoading(true)
    await Promise.all([fetchPublishedArticles(), fetchEditorialDesk(), fetchStats()])
    setLoading(false)
  }

  useEffect(() => {
    refreshAll()
  }, [])

  const handleCreateArticle = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!writeTitle.trim() || !writeContent.trim()) {
      toast.error('Please fill in title and content')
      return
    }
    setSubmittingArticle(true)
    try {
      await api.post('/news-publication/articles', {
        title: writeTitle.trim(),
        content: writeContent.trim(),
        summary: writeSummary.trim() || undefined,
        category: writeCategory,
        target_audience: writeTargetAudience,
        cover_image_url: writeCoverUrl.trim() || undefined,
        is_featured: writeIsFeatured,
        status: ['admin', 'lecturer'].includes(user?.role ?? '') ? 'published' : 'submitted',
      })
      toast.success(
        ['admin', 'lecturer'].includes(user?.role ?? '')
          ? '🎉 Story published directly to campus feed!'
          : '📬 Story submitted to editorial board for review!'
      )
      setShowWriteModal(false)
      setWriteTitle('')
      setWriteSummary('')
      setWriteContent('')
      setWriteCoverUrl('')
      setWriteIsFeatured(false)
      refreshAll()
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to submit article')
    } finally {
      setSubmittingArticle(false)
    }
  }

  if (selectedId !== null) {
    return (
      <ArticleDetailView
        articleId={selectedId}
        onBack={() => setSelectedId(null)}
        onRefreshList={refreshAll}
      />
    )
  }

  const featured = articles.find((a) => a.is_featured)
  const regularArticles = articles.filter((a) => !featured || a.id !== featured.id)

  return (
    <div className="fade-in">
      <div className="page-header mb-24">
        <div className="flex justify-between items-center" style={{ flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div className="page-title">📰 NSBM Campus Media & News</div>
            <div className="page-subtitle">The official journalism, research bulletins, and student press portal</div>
          </div>
          <div className="flex gap-12">
            <button className="btn btn-primary" onClick={() => setShowWriteModal(true)}>
              ✏️ Write Article / Press Release
            </button>
          </div>
        </div>

        {/* Tab navigation */}
        <div className="flex gap-16 mt-20" style={{ borderBottom: '1px solid var(--border)' }}>
          <button
            className={`btn btn-sm ${activeTab === 'feed' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setActiveTab('feed')}
            style={{ borderRadius: '6px 6px 0 0' }}
          >
            🌐 Campus News Feed
          </button>
          {['admin', 'lecturer'].includes(user?.role ?? '') && (
            <button
              className={`btn btn-sm ${activeTab === 'editorial' ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => {
                setActiveTab('editorial')
                fetchEditorialDesk()
              }}
              style={{ borderRadius: '6px 6px 0 0' }}
            >
              📝 Editorial Desk ({editorialArticles.filter((a) => a.status !== 'published').length} pending)
            </button>
          )}
          <button
            className={`btn btn-sm ${activeTab === 'stats' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => {
              setActiveTab('stats')
              fetchStats()
            }}
            style={{ borderRadius: '6px 6px 0 0' }}
          >
            📊 Media Analytics
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center" style={{ height: 300 }}>
          <div className="spinner" />
        </div>
      ) : activeTab === 'feed' ? (
        <>
          {/* Filters */}
          <div className="flex gap-12 mb-24" style={{ flexWrap: 'wrap' }}>
            <input
              className="form-control"
              placeholder="🔍 Search stories, press releases, research..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ flex: 1, minWidth: 200 }}
              onKeyDown={(e) => e.key === 'Enter' && fetchPublishedArticles(search, category)}
            />
            <select
              className="form-control"
              value={category}
              onChange={(e) => {
                setCategory(e.target.value)
                fetchPublishedArticles(search, e.target.value)
              }}
              style={{ width: 190 }}
            >
              <option value="">All Categories</option>
              {Object.keys(CAT_EMOJI).map((k) => (
                <option key={k} value={k}>
                  {CAT_EMOJI[k]} {k.toUpperCase()}
                </option>
              ))}
            </select>
            <button className="btn btn-secondary" onClick={() => fetchPublishedArticles(search, category)}>
              Filter
            </button>
          </div>

          {/* Featured Hero */}
          {featured && (
            <div
              className="card mb-24"
              style={{
                background: 'linear-gradient(135deg, rgba(108,99,255,.16), rgba(0,212,170,.06))',
                borderColor: 'rgba(108,99,255,.3)',
                cursor: 'pointer',
                overflow: 'hidden',
              }}
              onClick={() => setSelectedId(featured.id)}
            >
              <div className="flex gap-20 items-center" style={{ flexWrap: 'wrap' }}>
                <div
                  style={{
                    width: 140,
                    height: 140,
                    borderRadius: 12,
                    background: featured.cover_image_url
                      ? `url(${featured.cover_image_url}) center/cover no-repeat`
                      : 'rgba(108,99,255,0.2)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '4rem',
                    flexShrink: 0,
                  }}
                >
                  {!featured.cover_image_url && (CAT_EMOJI[featured.category] || '📰')}
                </div>
                <div style={{ flex: 1, minWidth: 260 }}>
                  <div className="flex items-center gap-8 mb-10">
                    <span className="badge badge-gold">⭐ Featured Spotlight</span>
                    <span
                      style={{
                        color: CAT_COLOR[featured.category] || '#6C63FF',
                        fontSize: '.75rem',
                        fontWeight: 700,
                        textTransform: 'uppercase',
                      }}
                    >
                      {featured.category}
                    </span>
                  </div>
                  <div
                    style={{
                      fontFamily: "'Outfit',sans-serif",
                      fontSize: '1.45rem',
                      fontWeight: 800,
                      marginBottom: 8,
                      lineHeight: 1.3,
                    }}
                  >
                    {featured.title}
                  </div>
                  <div className="text-sm text-secondary" style={{ lineHeight: 1.6, marginBottom: 12 }}>
                    {featured.summary}
                  </div>
                  <div className="text-xs text-muted flex gap-16">
                    <span>✍️ {featured.author_name || featured.author || 'Press Office'}</span>
                    <span>📅 {featured.published_at ? new Date(featured.published_at).toLocaleDateString() : ''}</span>
                    <span>👁️ {featured.views} reads</span>
                    <span>❤️ {featured.likes_count ?? 0} applauds</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Grid */}
          {regularArticles.length > 0 ? (
            <div className="grid-3" style={{ gap: 20 }}>
              {regularArticles.map((a) => (
                <NewsCard key={a.id} article={a} onClick={() => setSelectedId(a.id)} />
              ))}
            </div>
          ) : (
            <div className="card text-center py-48 text-muted">
              📰 No articles matched your search filter.
            </div>
          )}
        </>
      ) : activeTab === 'editorial' ? (
        <div className="fade-in">
          <div className="card mb-20" style={{ background: 'rgba(255,255,255,0.02)' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: 6 }}>
              Editorial Queue & Press Moderation
            </h3>
            <p className="text-xs text-muted">
              Review student and department submissions, conduct fact-checking, and publish verified university communications.
            </p>
          </div>

          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Category</th>
                  <th>Author</th>
                  <th>Audience</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {editorialArticles.map((art) => (
                  <tr key={art.id}>
                    <td style={{ fontWeight: 600, maxWidth: 280 }}>
                      <div className="truncate">{art.title}</div>
                    </td>
                    <td>
                      <span className="badge" style={{ color: CAT_COLOR[art.category] }}>
                        {art.category}
                      </span>
                    </td>
                    <td className="text-sm">{art.author_name || 'Staff'}</td>
                    <td className="text-sm">{art.target_audience}</td>
                    <td>
                      <span
                        className={`badge ${
                          art.status === 'published'
                            ? 'badge-success'
                            : art.status === 'submitted'
                            ? 'badge-warning'
                            : 'badge-secondary'
                        }`}
                      >
                        {art.status}
                      </span>
                    </td>
                    <td className="text-xs text-muted">
                      {new Date(art.created_at || '').toLocaleDateString()}
                    </td>
                    <td>
                      <div className="flex gap-8">
                        <button className="btn btn-ghost btn-xs" onClick={() => setSelectedId(art.id)}>
                          View
                        </button>
                        {art.status !== 'published' && (
                          <button
                            className="btn btn-primary btn-xs"
                            onClick={async () => {
                              try {
                                await api.put(`/news-publication/articles/${art.id}/publish`)
                                toast.success('Published!')
                                fetchEditorialDesk()
                              } catch (e: any) {
                                toast.error(e.response?.data?.detail || 'Publish failed')
                              }
                            }}
                          >
                            Publish
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
      ) : (
        /* Analytics Tab */
        <div className="fade-in">
          <div className="grid-3 mb-24">
            <div className="card text-center">
              <div style={{ fontSize: '2.4rem', fontWeight: 800, color: '#6C63FF' }}>
                {stats?.total_articles ?? articles.length}
              </div>
              <div className="text-xs text-muted uppercase mt-4">Published Articles</div>
            </div>
            <div className="card text-center">
              <div style={{ fontSize: '2.4rem', fontWeight: 800, color: '#00D4AA' }}>
                {stats?.total_views ?? 0}
              </div>
              <div className="text-xs text-muted uppercase mt-4">Total Reader Impressions</div>
            </div>
            <div className="card text-center">
              <div style={{ fontSize: '2.4rem', fontWeight: 800, color: '#FF6B6B' }}>
                {stats?.total_likes ?? 0}
              </div>
              <div className="text-xs text-muted uppercase mt-4">Total Reader Reactions</div>
            </div>
          </div>

          <div className="card">
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: 16 }}>
              Category Distribution
            </h3>
            <div className="grid-3" style={{ gap: 16 }}>
              {stats?.category_breakdown &&
                Object.entries(stats.category_breakdown).map(([cat, cnt]) => (
                  <div
                    key={cat}
                    style={{
                      padding: '12px 16px',
                      background: 'rgba(255,255,255,0.03)',
                      borderRadius: 8,
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>
                      {CAT_EMOJI[cat] || '📰'} {cat}
                    </span>
                    <span className="badge badge-info">{cnt} stories</span>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}

      {/* Write Article Modal */}
      {showWriteModal && (
        <div className="modal-backdrop">
          <div className="modal-box" style={{ maxWidth: 650 }}>
            <div className="modal-header">
              <h3 style={{ margin: 0, fontWeight: 700 }}>✏️ Draft Campus Story / Press Release</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowWriteModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateArticle}>
              <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div>
                  <label className="text-xs text-muted mb-4 block">Story Headline *</label>
                  <input
                    className="form-control w-full"
                    placeholder="e.g. NSBM Annual Research Symposium Keynote Announced"
                    value={writeTitle}
                    onChange={(e) => setWriteTitle(e.target.value)}
                    required
                  />
                </div>
                <div className="grid-2" style={{ gap: 12 }}>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Category *</label>
                    <select
                      className="form-control w-full"
                      value={writeCategory}
                      onChange={(e) => setWriteCategory(e.target.value)}
                    >
                      {Object.keys(CAT_EMOJI).map((k) => (
                        <option key={k} value={k}>
                          {CAT_EMOJI[k]} {k.toUpperCase()}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-muted mb-4 block">Target Audience</label>
                    <select
                      className="form-control w-full"
                      value={writeTargetAudience}
                      onChange={(e) => setWriteTargetAudience(e.target.value)}
                    >
                      <option value="all">Campus Wide (Everyone)</option>
                      <option value="students">Undergraduates & Students</option>
                      <option value="faculty">Academic Faculty & Lecturers</option>
                      <option value="public">Public Press & Alumni</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="text-xs text-muted mb-4 block">Summary / Teaser</label>
                  <input
                    className="form-control w-full"
                    placeholder="Brief 1-2 sentence lead paragraph..."
                    value={writeSummary}
                    onChange={(e) => setWriteSummary(e.target.value)}
                  />
                </div>
                <div>
                  <label className="text-xs text-muted mb-4 block">Full Article Body *</label>
                  <textarea
                    className="form-control w-full"
                    rows={6}
                    placeholder="Write your news article or press release details here..."
                    value={writeContent}
                    onChange={(e) => setWriteContent(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="text-xs text-muted mb-4 block">Cover Image URL (Optional)</label>
                  <input
                    className="form-control w-full"
                    placeholder="https://..."
                    value={writeCoverUrl}
                    onChange={(e) => setWriteCoverUrl(e.target.value)}
                  />
                </div>
                {['admin', 'lecturer'].includes(user?.role ?? '') && (
                  <div className="flex items-center gap-8 mt-4">
                    <input
                      type="checkbox"
                      id="feat-check"
                      checked={writeIsFeatured}
                      onChange={(e) => setWriteIsFeatured(e.target.checked)}
                    />
                    <label htmlFor="feat-check" className="text-sm">
                      Mark as Featured Spotlight story on homepage banner
                    </label>
                  </div>
                )}
              </div>
              <div className="modal-footer flex justify-end gap-12 mt-16">
                <button type="button" className="btn btn-ghost" onClick={() => setShowWriteModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submittingArticle}>
                  {submittingArticle
                    ? 'Submitting…'
                    : ['admin', 'lecturer'].includes(user?.role ?? '')
                    ? 'Publish Story'
                    : 'Submit for Review'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
