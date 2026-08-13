import React, { useEffect, useState } from 'react'
import api from '@/api/client'
import toast from 'react-hot-toast'
import type { NewsArticle, Paginated } from '@/types'
import { useAuth } from '@/contexts/AuthContext'

const CAT_COLOR: Record<string, string> = {
  academic: '#6C63FF', sports: '#FF6B6B', events: '#00D4AA',
  alumni: '#FFD700', research: '#FF64C8', general: '#FFB347',
}
const CAT_EMOJI: Record<string, string> = {
  academic: '📖', sports: '⚽', events: '🎉',
  alumni: '🌐', research: '🔬', general: '📰',
}

function NewsCard({ article, onClick }: { article: NewsArticle; onClick: () => void }) {
  const color = CAT_COLOR[article.category] || '#6C63FF'
  const emoji = CAT_EMOJI[article.category] || '📰'
  return (
    <div className="news-card" onClick={onClick}>
      <div className="news-card-img" style={{ background: `linear-gradient(135deg, ${color}28, ${color}0d)` }}>
        <span>{emoji}</span>
      </div>
      <div className="news-card-body">
        <div className="news-card-category" style={{ color }}>{article.category}</div>
        <div className="news-card-title">{article.title}</div>
        {article.summary && (
          <div className="text-sm text-muted mb-16" style={{ lineHeight: 1.5 }}>
            {article.summary.slice(0, 110)}...
          </div>
        )}
        <div className="news-card-meta">
          <span>✍️ {article.author}</span>
          <span>👁️ {article.views}</span>
          <span>📅 {new Date(article.published_at).toLocaleDateString()}</span>
        </div>
      </div>
    </div>
  )
}

function ArticleView({ articleId, onBack }: { articleId: number; onBack: () => void }) {
  const { user } = useAuth()
  const [article, setArticle] = useState<NewsArticle | null>(null)
  const [comment, setComment] = useState('')

  useEffect(() => {
    api.get<NewsArticle>(`/news/${articleId}`).then(r => setArticle(r.data))
  }, [articleId])

  const postComment = async () => {
    if (!comment.trim()) return
    try {
      await api.post(`/news/${articleId}/comments`, { content: comment })
      toast.success('💬 Comment posted!')
      setComment('')
      api.get<NewsArticle>(`/news/${articleId}`).then(r => setArticle(r.data))
    } catch (e: any) { toast.error(e.response?.data?.detail || 'Error') }
  }

  if (!article) return <div className="flex justify-center items-center" style={{ height: 300 }}><div className="spinner" /></div>

  const color = CAT_COLOR[article.category] || '#6C63FF'

  return (
    <div className="fade-in">
      <button className="btn btn-ghost btn-sm mb-16" onClick={onBack}>← Back to News</button>
      <div className="card" style={{ maxWidth: 820, margin: '0 auto' }}>
        <span className="badge mb-16" style={{ background: `${color}20`, color, borderColor: `${color}44` }}>
          {article.category}
        </span>
        <h1 style={{ fontFamily: "'Outfit',sans-serif", fontSize: '1.9rem', fontWeight: 800, lineHeight: 1.3, marginBottom: 14 }}>
          {article.title}
        </h1>
        <div className="flex gap-16 mb-24 text-sm text-muted" style={{ flexWrap: 'wrap' }}>
          <span>✍️ {article.author}</span>
          <span>📅 {new Date(article.published_at).toLocaleDateString()}</span>
          <span>👁️ {article.views} views</span>
        </div>
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: 24, lineHeight: 1.9, color: 'rgba(255,255,255,.82)', fontSize: '.95rem', whiteSpace: 'pre-line' }}>
          {article.content}
        </div>

        {/* Comments */}
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: 24, marginTop: 28 }}>
          <div style={{ fontWeight: 700, marginBottom: 18 }}>💬 Comments ({article.comments?.length ?? 0})</div>
          {article.comments?.map(c => (
            <div key={c.id} className="flex gap-12 mb-16 pb-16" style={{ borderBottom: '1px solid rgba(255,255,255,.04)' }}>
              <div className="avatar avatar-sm">{c.user.full_name[0]}</div>
              <div>
                <div style={{ fontWeight: 600, fontSize: '.875rem' }}>
                  {c.user.full_name} <span className="text-xs text-muted">{new Date(c.created_at).toLocaleDateString()}</span>
                </div>
                <div className="text-sm text-secondary mt-8">{c.content}</div>
              </div>
            </div>
          ))}
          <div className="flex gap-12 mt-16">
            <input className="form-control" placeholder="Add a comment…" value={comment} onChange={e => setComment(e.target.value)} style={{ flex: 1 }} onKeyDown={e => e.key === 'Enter' && postComment()} />
            <button className="btn btn-primary" onClick={postComment}>Post</button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function News() {
  const { user } = useAuth()
  const [articles, setArticles] = useState<NewsArticle[]>([])
  const [total, setTotal] = useState(0)
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const fetchNews = async (s = search, c = category) => {
    const params = new URLSearchParams({ page: '1', size: '12' })
    if (s) params.set('search', s)
    if (c) params.set('category', c)
    const r = await api.get<Paginated<NewsArticle>>(`/news?${params}`)
    setArticles(r.data.items); setTotal(r.data.total)
  }

  useEffect(() => {
    fetchNews().finally(() => setLoading(false))
  }, [])

  if (selectedId !== null) return <ArticleView articleId={selectedId} onBack={() => setSelectedId(null)} />

  const featured = articles.find(a => a.is_featured)
  const rest = articles.filter(a => !a.is_featured)

  if (loading) return <div className="flex justify-center items-center" style={{ height: 300 }}><div className="spinner" /></div>

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="flex justify-between items-center" style={{ flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div className="page-title">📰 News & Announcements</div>
            <div className="page-subtitle">{total} articles</div>
          </div>
          {['admin', 'lecturer'].includes(user?.role ?? '') && (
            <button className="btn btn-primary">✏️ Write Article</button>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-12 mb-24" style={{ flexWrap: 'wrap' }}>
        <input className="form-control" placeholder="🔍 Search news…" value={search}
          onChange={e => setSearch(e.target.value)} style={{ flex: 1, minWidth: 200 }}
          onKeyDown={e => e.key === 'Enter' && fetchNews()} />
        <select className="form-control" value={category} onChange={e => setCategory(e.target.value)} style={{ width: 180 }}>
          <option value="">All Categories</option>
          {Object.keys(CAT_EMOJI).map(k => <option key={k} value={k}>{CAT_EMOJI[k]} {k}</option>)}
        </select>
        <button className="btn btn-secondary" onClick={() => fetchNews()}>Filter</button>
      </div>

      {/* Featured */}
      {featured && (
        <div className="card mb-24" style={{
          background: 'linear-gradient(135deg,rgba(108,99,255,.14),rgba(0,212,170,.05))',
          borderColor: 'rgba(108,99,255,.3)', cursor: 'pointer',
        }} onClick={() => setSelectedId(featured.id)}>
          <div className="flex gap-16 items-center">
            <div style={{ fontSize: '3.5rem' }}>{CAT_EMOJI[featured.category] || '📰'}</div>
            <div style={{ flex: 1 }}>
              <div className="flex items-center gap-8 mb-12">
                <span className="badge badge-gold">⭐ Featured</span>
                <span style={{ color: CAT_COLOR[featured.category], fontSize: '.73rem', fontWeight: 700, textTransform: 'uppercase' }}>{featured.category}</span>
              </div>
              <div style={{ fontFamily: "'Outfit',sans-serif", fontSize: '1.35rem', fontWeight: 800, marginBottom: 8, lineHeight: 1.3 }}>
                {featured.title}
              </div>
              <div className="text-sm text-secondary" style={{ lineHeight: 1.6 }}>{featured.summary}</div>
              <div className="text-xs text-muted mt-12">✍️ {featured.author} · 📅 {new Date(featured.published_at).toLocaleDateString()} · 👁️ {featured.views}</div>
            </div>
          </div>
        </div>
      )}

      {/* Grid */}
      <div className="grid-3">
        {rest.map(a => <NewsCard key={a.id} article={a} onClick={() => setSelectedId(a.id)} />)}
      </div>
    </div>
  )
}
