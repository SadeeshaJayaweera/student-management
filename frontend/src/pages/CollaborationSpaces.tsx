import React, { useState, useEffect } from 'react'
import api from '@/api/client'
import { useAuth } from '@/contexts/AuthContext'
import type { CollaborationWorkspace, CollaborationWorkspaceDetail } from '@/types'
import toast from 'react-hot-toast'

export default function CollaborationSpaces() {
  const { user } = useAuth()
  const [workspaces, setWorkspaces] = useState<CollaborationWorkspace[]>([])
  const [selectedWorkspace, setSelectedWorkspace] = useState<CollaborationWorkspaceDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'chat' | 'assets' | 'members'>('chat')

  // Chat message state
  const [chatMessage, setChatMessage] = useState('')
  const [sendingMsg, setSendingMsg] = useState(false)

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showJoinModal, setShowJoinModal] = useState(false)
  const [showAssetModal, setShowAssetModal] = useState(false)
  const [joinCodeInput, setJoinCodeInput] = useState('')

  const [newWorkspace, setNewWorkspace] = useState({
    name: '',
    description: '',
    topic: '',
    visibility: 'course_public',
    meeting_link: '',
  })

  const [newAsset, setNewAsset] = useState({
    title: '',
    asset_type: 'note',
    content: '',
  })

  const loadWorkspaces = async () => {
    try {
      setLoading(true)
      const res = await api.get<CollaborationWorkspace[]>('/collaboration/workspaces')
      setWorkspaces(res.data || [])
    } catch {
      toast.error('Failed to load collaboration spaces')
    } finally {
      setLoading(false)
    }
  }

  const selectWorkspace = async (id: number) => {
    try {
      setDetailLoading(true)
      const res = await api.get<CollaborationWorkspaceDetail>(`/collaboration/workspaces/${id}`)
      setSelectedWorkspace(res.data)
    } catch {
      toast.error('Failed to load workspace details')
    } finally {
      setDetailLoading(false)
    }
  }

  useEffect(() => {
    loadWorkspaces()
  }, [])

  const handleJoinByCode = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!joinCodeInput.trim()) return
    try {
      const res = await api.post<CollaborationWorkspace>('/collaboration/workspaces/join', {
        join_code: joinCodeInput.trim(),
      })
      toast.success(`Joined ${res.data.name}!`)
      setShowJoinModal(false)
      setJoinCodeInput('')
      await loadWorkspaces()
      selectWorkspace(res.data.id)
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Invalid join code')
    }
  }

  const handleCreateWorkspace = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const res = await api.post<CollaborationWorkspace>('/collaboration/workspaces', newWorkspace)
      toast.success('Workspace created successfully!')
      setShowCreateModal(false)
      setNewWorkspace({
        name: '',
        description: '',
        topic: '',
        visibility: 'course_public',
        meeting_link: '',
      })
      await loadWorkspaces()
      selectWorkspace(res.data.id)
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to create workspace')
    }
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!chatMessage.trim() || !selectedWorkspace) return
    try {
      setSendingMsg(true)
      await api.post(`/collaboration/workspaces/${selectedWorkspace.id}/messages`, {
        content: chatMessage.trim(),
        pinned: false,
      })
      setChatMessage('')
      selectWorkspace(selectedWorkspace.id)
    } catch {
      toast.error('Failed to post message')
    } finally {
      setSendingMsg(false)
    }
  }

  const handleAddAsset = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedWorkspace) return
    try {
      await api.post(`/collaboration/workspaces/${selectedWorkspace.id}/assets`, newAsset)
      toast.success('Asset shared with workspace!')
      setShowAssetModal(false)
      setNewAsset({ title: '', asset_type: 'note', content: '' })
      selectWorkspace(selectedWorkspace.id)
    } catch {
      toast.error('Failed to add asset')
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center" style={{ height: 320 }}>
        <div className="spinner" />
      </div>
    )
  }

  return (
    <div className="fade-in">
      {/* Page Header */}
      <div className="flex justify-between items-center mb-24 flex-wrap gap-12">
        <div>
          <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 800 }}>👥 Student Collaboration Spaces</h1>
          <p className="text-muted text-sm" style={{ marginTop: 4 }}>
            Project workspaces, study group whiteboards, shared notes, and live team chat
          </p>
        </div>
        <div className="flex items-center gap-12">
          <button className="btn btn-secondary btn-sm" onClick={() => setShowJoinModal(true)}>
            🔑 Join by Code
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => setShowCreateModal(true)}>
            ➕ Create Space
          </button>
        </div>
      </div>

      <div className="grid-3 gap-24" style={{ gridTemplateColumns: selectedWorkspace ? '1fr 2fr' : '1fr' }}>
        {/* Workspaces List Column */}
        <div className="flex flex-col gap-12">
          <div className="text-xs text-muted mb-4 font-bold uppercase tracking-wider">
            Your Active Spaces ({workspaces.length})
          </div>
          {workspaces.length === 0 ? (
            <div className="card text-center text-muted" style={{ padding: 32 }}>
              No collaboration spaces yet. Create or join one to collaborate on projects!
            </div>
          ) : (
            workspaces.map((w) => (
              <div
                key={w.id}
                onClick={() => selectWorkspace(w.id)}
                className="card"
                style={{
                  cursor: 'pointer',
                  borderColor: selectedWorkspace?.id === w.id ? '#4F46E5' : 'rgba(255,255,255,0.08)',
                  background: selectedWorkspace?.id === w.id ? 'rgba(79,70,229,0.08)' : 'inherit',
                  transition: 'all .2s ease',
                  padding: 16,
                }}
              >
                <div className="flex justify-between items-start mb-6">
                  <div style={{ fontWeight: 700, fontSize: '.95rem' }}>{w.name}</div>
                  <span className="badge badge-info text-xs">{w.visibility.replace('_', ' ')}</span>
                </div>
                {w.topic && <div className="text-xs text-muted mb-8">💡 {w.topic}</div>}
                <div className="flex justify-between items-center text-xs text-muted">
                  <span>👥 {w.members_count} members</span>
                  <span>📄 {w.assets_count} files</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Selected Workspace Detail View */}
        {selectedWorkspace && (
          <div className="card">
            {detailLoading ? (
              <div className="flex justify-center items-center" style={{ height: 260 }}>
                <div className="spinner" />
              </div>
            ) : (
              <div>
                {/* Space Header */}
                <div className="flex justify-between items-start mb-20 flex-wrap gap-12" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: 16 }}>
                  <div>
                    <div className="flex items-center gap-8 mb-4">
                      <h2 style={{ margin: 0, fontSize: '1.3rem', fontWeight: 800 }}>{selectedWorkspace.name}</h2>
                      <span className="badge badge-primary text-xs">PIN: {selectedWorkspace.join_code}</span>
                    </div>
                    <div className="text-xs text-muted">
                      Created by {selectedWorkspace.owner_name} · Topic: {selectedWorkspace.topic || 'General study'}
                    </div>
                  </div>
                  <div className="flex items-center gap-8">
                    {selectedWorkspace.meeting_link && (
                      <a
                        href={selectedWorkspace.meeting_link}
                        target="_blank"
                        rel="noreferrer"
                        className="btn btn-primary btn-sm"
                      >
                        📹 Video Call
                      </a>
                    )}
                    <button className="btn btn-ghost btn-sm" onClick={() => setSelectedWorkspace(null)}>
                      ✕ Close
                    </button>
                  </div>
                </div>

                {/* Navigation Tabs */}
                <div className="flex gap-8 mb-16">
                  <button
                    className={`btn btn-sm ${activeTab === 'chat' ? 'btn-primary' : 'btn-ghost'}`}
                    onClick={() => setActiveTab('chat')}
                  >
                    💬 Team Chat ({selectedWorkspace.recent_messages.length})
                  </button>
                  <button
                    className={`btn btn-sm ${activeTab === 'assets' ? 'btn-primary' : 'btn-ghost'}`}
                    onClick={() => setActiveTab('assets')}
                  >
                    📄 Shared Files ({selectedWorkspace.assets.length})
                  </button>
                  <button
                    className={`btn btn-sm ${activeTab === 'members' ? 'btn-primary' : 'btn-ghost'}`}
                    onClick={() => setActiveTab('members')}
                  >
                    👥 Members ({selectedWorkspace.members.length})
                  </button>
                </div>

                {/* Tab: Chat */}
                {activeTab === 'chat' && (
                  <div>
                    <div
                      style={{
                        height: 280,
                        overflowY: 'auto',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 12,
                        padding: 12,
                        background: 'rgba(0,0,0,0.15)',
                        borderRadius: 8,
                        marginBottom: 16,
                      }}
                    >
                      {selectedWorkspace.recent_messages.length === 0 ? (
                        <div className="text-center text-muted text-xs" style={{ margin: 'auto' }}>
                          No messages yet. Say hello to your team! 👋
                        </div>
                      ) : (
                        selectedWorkspace.recent_messages.map((m) => (
                          <div
                            key={m.id}
                            style={{
                              background: 'rgba(255,255,255,0.03)',
                              padding: '8px 12px',
                              borderRadius: 8,
                              borderLeft: '3px solid #4F46E5',
                            }}
                          >
                            <div className="flex justify-between items-center text-xs mb-2">
                              <span style={{ fontWeight: 700, color: '#8B85FF' }}>{m.sender_name}</span>
                              <span className="text-muted">{new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                            </div>
                            <div className="text-sm">{m.content}</div>
                          </div>
                        ))
                      )}
                    </div>

                    <form onSubmit={handleSendMessage} className="flex gap-8">
                      <input
                        type="text"
                        placeholder="Type a message or share an update..."
                        className="input w-full"
                        value={chatMessage}
                        onChange={(e) => setChatMessage(e.target.value)}
                      />
                      <button type="submit" className="btn btn-primary" disabled={sendingMsg || !chatMessage.trim()}>
                        Send
                      </button>
                    </form>
                  </div>
                )}

                {/* Tab: Assets */}
                {activeTab === 'assets' && (
                  <div>
                    <div className="flex justify-between items-center mb-16">
                      <div className="text-xs text-muted">Shared documents, notes, and code snippets</div>
                      <button className="btn btn-secondary btn-sm" onClick={() => setShowAssetModal(true)}>
                        ➕ Add Resource
                      </button>
                    </div>

                    <div className="flex flex-col gap-10">
                      {selectedWorkspace.assets.length === 0 ? (
                        <div className="text-muted text-center text-sm" style={{ padding: 24 }}>
                          No shared files or notes yet.
                        </div>
                      ) : (
                        selectedWorkspace.assets.map((a) => (
                          <div
                            key={a.id}
                            style={{
                              padding: 12,
                              background: 'rgba(255,255,255,0.02)',
                              borderRadius: 6,
                              border: '1px solid rgba(255,255,255,0.05)',
                            }}
                          >
                            <div className="flex justify-between items-center mb-4">
                              <div style={{ fontWeight: 700, fontSize: '.9rem' }}>{a.title}</div>
                              <span className="badge badge-info text-xs">{a.asset_type.toUpperCase()}</span>
                            </div>
                            <div className="text-xs text-muted mb-6">Shared by {a.author_name} · v{a.version}</div>
                            <div
                              className="text-xs"
                              style={{
                                background: 'rgba(0,0,0,0.2)',
                                padding: 8,
                                borderRadius: 4,
                                whiteSpace: 'pre-wrap',
                                fontFamily: a.asset_type === 'code_snippet' ? 'monospace' : 'inherit',
                              }}
                            >
                              {a.content}
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}

                {/* Tab: Members */}
                {activeTab === 'members' && (
                  <div className="flex flex-col gap-10">
                    {selectedWorkspace.members.map((m) => (
                      <div
                        key={m.id}
                        className="flex justify-between items-center"
                        style={{
                          padding: '10px 14px',
                          background: 'rgba(255,255,255,0.02)',
                          borderRadius: 6,
                        }}
                      >
                        <div>
                          <div style={{ fontWeight: 600, fontSize: '.9rem' }}>{m.student_name}</div>
                          {m.student_reg_id && <div className="text-xs text-muted">{m.student_reg_id}</div>}
                        </div>
                        <span className={`badge ${m.role === 'owner' ? 'badge-success' : 'badge-info'}`}>
                          {m.role.toUpperCase()}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Join Space Modal */}
      {showJoinModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: 16 }}>
          <div className="card" style={{ maxWidth: 400, width: '100%' }}>
            <div className="flex justify-between items-center mb-16">
              <div style={{ fontWeight: 700, fontSize: '1.2rem' }}>Join Collaboration Space</div>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowJoinModal(false)}>✕</button>
            </div>
            <form onSubmit={handleJoinByCode} className="flex flex-col gap-12">
              <div>
                <label className="text-xs text-muted block mb-4">Enter 8-Character Join PIN</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 7A8B9C1D"
                  className="input w-full"
                  style={{ textAlign: 'center', letterSpacing: 4, fontWeight: 700, textTransform: 'uppercase' }}
                  value={joinCodeInput}
                  onChange={(e) => setJoinCodeInput(e.target.value)}
                />
              </div>
              <div className="flex justify-end gap-12 mt-12">
                <button type="button" className="btn btn-ghost" onClick={() => setShowJoinModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Join Space</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Space Modal */}
      {showCreateModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: 16 }}>
          <div className="card" style={{ maxWidth: 480, width: '100%' }}>
            <div className="flex justify-between items-center mb-16">
              <div style={{ fontWeight: 700, fontSize: '1.2rem' }}>Create Collaboration Space</div>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowCreateModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateWorkspace} className="flex flex-col gap-12">
              <div>
                <label className="text-xs text-muted block mb-4">Space Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Distributed Systems Lab Team 4"
                  className="input w-full"
                  value={newWorkspace.name}
                  onChange={(e) => setNewWorkspace({ ...newWorkspace, name: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs text-muted block mb-4">Topic / Focus</label>
                <input
                  type="text"
                  placeholder="e.g. Raft Consensus Implementation"
                  className="input w-full"
                  value={newWorkspace.topic}
                  onChange={(e) => setNewWorkspace({ ...newWorkspace, topic: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs text-muted block mb-4">Description</label>
                <textarea
                  rows={2}
                  className="input w-full"
                  placeholder="Goals, team deliverables, and expectations..."
                  value={newWorkspace.description}
                  onChange={(e) => setNewWorkspace({ ...newWorkspace, description: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs text-muted block mb-4">Video Meeting Link (Optional)</label>
                <input
                  type="url"
                  placeholder="https://meet.google.com/..."
                  className="input w-full"
                  value={newWorkspace.meeting_link}
                  onChange={(e) => setNewWorkspace({ ...newWorkspace, meeting_link: e.target.value })}
                />
              </div>
              <div className="flex justify-end gap-12 mt-12">
                <button type="button" className="btn btn-ghost" onClick={() => setShowCreateModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create Space</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Asset Modal */}
      {showAssetModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: 16 }}>
          <div className="card" style={{ maxWidth: 480, width: '100%' }}>
            <div className="flex justify-between items-center mb-16">
              <div style={{ fontWeight: 700, fontSize: '1.2rem' }}>Share Resource / Document</div>
              <button className="btn btn-ghost btn-sm" onClick={() => setShowAssetModal(false)}>✕</button>
            </div>
            <form onSubmit={handleAddAsset} className="flex flex-col gap-12">
              <div>
                <label className="text-xs text-muted block mb-4">Resource Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Raft Leader Election State Machine"
                  className="input w-full"
                  value={newAsset.title}
                  onChange={(e) => setNewAsset({ ...newAsset, title: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs text-muted block mb-4">Type</label>
                <select
                  className="input w-full"
                  value={newAsset.asset_type}
                  onChange={(e) => setNewAsset({ ...newAsset, asset_type: e.target.value })}
                >
                  <option value="note">Shared Note</option>
                  <option value="code_snippet">Code Snippet</option>
                  <option value="document">Document / Specification</option>
                  <option value="link">Reference Link</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-muted block mb-4">Content</label>
                <textarea
                  rows={4}
                  required
                  className="input w-full"
                  placeholder="Paste text, code, or link..."
                  value={newAsset.content}
                  onChange={(e) => setNewAsset({ ...newAsset, content: e.target.value })}
                />
              </div>
              <div className="flex justify-end gap-12 mt-12">
                <button type="button" className="btn btn-ghost" onClick={() => setShowAssetModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Share</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
