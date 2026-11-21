import React, { useEffect, useState, useRef } from 'react'
import api from '@/api/client'
import { useAuth } from '@/contexts/AuthContext'
import {
  ConversationItem,
  ConversationDetail,
  DirectMessage,
  MessagingContact,
} from '@/types'
import toast from 'react-hot-toast'

export default function Messaging() {
  const { user } = useAuth()
  const [conversations, setConversations] = useState<ConversationItem[]>([])
  const [activeConvId, setActiveConvId] = useState<number | null>(null)
  const [activeConv, setActiveConv] = useState<ConversationDetail | null>(null)
  const [unreadTotal, setUnreadTotal] = useState<number>(0)
  const [contacts, setContacts] = useState<MessagingContact[]>([])

  // UI state
  const [loadingList, setLoadingList] = useState<boolean>(true)
  const [loadingActive, setLoadingActive] = useState<boolean>(false)
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [newMessageText, setNewMessageText] = useState<string>('')
  const [attachmentUrl, setAttachmentUrl] = useState<string>('')
  const [attachmentName, setAttachmentName] = useState<string>('')
  const [sendingMessage, setSendingMessage] = useState<boolean>(false)

  // Modal: Start New Conversation
  const [showNewModal, setShowNewModal] = useState<boolean>(false)
  const [selectedRecipientId, setSelectedRecipientId] = useState<number | ''>('')
  const [newSubject, setNewSubject] = useState<string>('')
  const [newThreadType, setNewThreadType] = useState<string>('direct')
  const [newInitialMessage, setNewInitialMessage] = useState<string>('')
  const [creatingConv, setCreatingConv] = useState<boolean>(false)

  const messagesEndRef = useRef<HTMLDivElement | null>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    loadConversations()
    loadContacts()
    loadUnreadCount()
  }, [])

  useEffect(() => {
    if (activeConvId) {
      loadConversationDetail(activeConvId)
    } else {
      setActiveConv(null)
    }
  }, [activeConvId])

  useEffect(() => {
    if (activeConv?.messages) {
      scrollToBottom()
    }
  }, [activeConv?.messages])

  const loadConversations = async () => {
    try {
      setLoadingList(true)
      const res = await api.get<ConversationItem[]>('/messaging/conversations')
      setConversations(res.data)
      if (res.data.length > 0 && !activeConvId) {
        setActiveConvId(res.data[0].id)
      }
    } catch (err: any) {
      console.error('Failed to load conversations:', err)
      toast.error('Failed to load message threads.')
    } finally {
      setLoadingList(false)
    }
  }

  const loadContacts = async () => {
    try {
      const res = await api.get<MessagingContact[]>('/messaging/contacts')
      setContacts(res.data)
    } catch (err: any) {
      console.error('Failed to load contacts:', err)
    }
  }

  const loadUnreadCount = async () => {
    try {
      const res = await api.get<{ unread_count: number }>('/messaging/unread-count')
      setUnreadTotal(res.data.unread_count)
    } catch (err: any) {
      console.error('Failed to load unread count:', err)
    }
  }

  const loadConversationDetail = async (id: number) => {
    try {
      setLoadingActive(true)
      const res = await api.get<ConversationDetail>(`/messaging/conversations/${id}`)
      setActiveConv(res.data)
      // Update local unread counter on list
      setConversations((prev) =>
        prev.map((c) => (c.id === id ? { ...c, unread_count: 0 } : c))
      )
      loadUnreadCount()
    } catch (err: any) {
      console.error('Failed to load conversation messages:', err)
      toast.error('Could not load messages.')
    } finally {
      setLoadingActive(false)
    }
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!activeConvId || !newMessageText.trim() || sendingMessage) return

    try {
      setSendingMessage(true)
      const payload = {
        content: newMessageText.trim(),
        attachment_url: attachmentUrl.trim() || undefined,
        attachment_name: attachmentName.trim() || undefined,
      }
      const res = await api.post<DirectMessage>(
        `/messaging/conversations/${activeConvId}/messages`,
        payload
      )

      if (activeConv) {
        setActiveConv({
          ...activeConv,
          messages: [...activeConv.messages, res.data],
        })
      }

      setConversations((prev) =>
        prev.map((c) =>
          c.id === activeConvId
            ? {
                ...c,
                last_message_at: res.data.sent_at,
                latest_message_snippet:
                  res.data.content.length > 80
                    ? res.data.content.substring(0, 80) + '...'
                    : res.data.content,
              }
            : c
        )
      )

      setNewMessageText('')
      setAttachmentUrl('')
      setAttachmentName('')
    } catch (err: any) {
      console.error('Failed to send message:', err)
      toast.error(err.response?.data?.detail || 'Failed to send message.')
    } finally {
      setSendingMessage(false)
    }
  }

  const handleStartConversation = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedRecipientId || !newInitialMessage.trim() || creatingConv) return

    try {
      setCreatingConv(true)
      const payload = {
        recipient_id: Number(selectedRecipientId),
        subject: newSubject.trim() || undefined,
        thread_type: newThreadType,
        initial_message: newInitialMessage.trim(),
      }
      const res = await api.post<ConversationDetail>('/messaging/conversations', payload)
      toast.success('Conversation started!')
      setShowNewModal(false)
      setSelectedRecipientId('')
      setNewSubject('')
      setNewInitialMessage('')

      await loadConversations()
      setActiveConvId(res.data.id)
      setActiveConv(res.data)
    } catch (err: any) {
      console.error('Failed to start conversation:', err)
      toast.error(err.response?.data?.detail || 'Failed to create conversation.')
    } finally {
      setCreatingConv(false)
    }
  }

  const filteredConversations = conversations.filter((c) => {
    const q = searchQuery.toLowerCase()
    const subjMatch = (c.subject || '').toLowerCase().includes(q)
    const partMatch = c.participants.some((p) => p.name.toLowerCase().includes(q))
    return subjMatch || partMatch
  })

  return (
    <div className="fade-in" style={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.8rem', fontWeight: 800, fontFamily: "'Outfit', sans-serif" }}>
            Campus Direct Messaging
          </h1>
          <p className="text-muted" style={{ margin: '4px 0 0 0', fontSize: '0.9rem' }}>
            Instant communications between students, faculty members, advisors, and mentors.
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {unreadTotal > 0 && (
            <span
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.2)',
                color: '#ef4444',
                padding: '4px 10px',
                borderRadius: 16,
                fontWeight: 700,
                fontSize: '0.85rem',
                border: '1px solid rgba(239, 68, 68, 0.4)',
              }}
            >
              {unreadTotal} unread message{unreadTotal > 1 ? 's' : ''}
            </span>
          )}
          <button
            onClick={() => setShowNewModal(true)}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: 8 }}
          >
            <span>✉️</span> New Message
          </button>
        </div>
      </div>

      {/* Main Two-Pane Chat Container */}
      <div
        className="card"
        style={{
          flex: 1,
          display: 'grid',
          gridTemplateColumns: '320px 1fr',
          padding: 0,
          overflow: 'hidden',
          borderRadius: 14,
          border: '1px solid var(--border-color)',
        }}
      >
        {/* Left Pane: Conversation Threads */}
        <div
          style={{
            borderRight: '1px solid var(--border-color)',
            display: 'flex',
            flexDirection: 'column',
            backgroundColor: 'rgba(255, 255, 255, 0.02)',
          }}
        >
          {/* Thread Search */}
          <div style={{ padding: '12px 14px', borderBottom: '1px solid var(--border-color)' }}>
            <input
              type="text"
              placeholder="Search conversations..."
              className="form-control"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ fontSize: '0.88rem' }}
            />
          </div>

          {/* Conversations List */}
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {loadingList ? (
              <div style={{ padding: 24, textAlign: 'center' }} className="text-muted">
                Loading messages...
              </div>
            ) : filteredConversations.length === 0 ? (
              <div style={{ padding: 24, textAlign: 'center' }} className="text-muted">
                No conversations found.
              </div>
            ) : (
              filteredConversations.map((c) => {
                const isActive = c.id === activeConvId
                const otherParticipants = c.participants.filter((p) => p.user_id !== user?.id)
                const title = otherParticipants.map((p) => p.name).join(', ') || c.subject || 'Direct Message'
                const roleBadge = otherParticipants[0]?.role || 'user'

                return (
                  <div
                    key={c.id}
                    onClick={() => setActiveConvId(c.id)}
                    style={{
                      padding: '12px 16px',
                      cursor: 'pointer',
                      borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                      backgroundColor: isActive ? 'rgba(59, 130, 246, 0.12)' : 'transparent',
                      borderLeft: isActive ? '3px solid #3b82f6' : '3px solid transparent',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                      <span style={{ fontWeight: 600, fontSize: '0.92rem', color: isActive ? '#60a5fa' : 'inherit' }}>
                        {title}
                      </span>
                      <span className="text-muted" style={{ fontSize: '0.75rem' }}>
                        {new Date(c.last_message_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                      <span
                        style={{
                          fontSize: '0.7rem',
                          textTransform: 'uppercase',
                          padding: '1px 6px',
                          borderRadius: 4,
                          backgroundColor: 'rgba(255, 255, 255, 0.08)',
                          color: '#94a3b8',
                          fontWeight: 600,
                        }}
                      >
                        {roleBadge}
                      </span>
                      {c.course_code && (
                        <span
                          style={{
                            fontSize: '0.7rem',
                            padding: '1px 6px',
                            borderRadius: 4,
                            backgroundColor: 'rgba(16, 185, 129, 0.12)',
                            color: '#10b981',
                            fontWeight: 600,
                          }}
                        >
                          {c.course_code}
                        </span>
                      )}
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <p
                        className="text-muted"
                        style={{
                          margin: 0,
                          fontSize: '0.8rem',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          maxWidth: '220px',
                        }}
                      >
                        {c.latest_message_snippet || 'No messages yet'}
                      </p>
                      {c.unread_count > 0 && (
                        <span
                          style={{
                            backgroundColor: '#3b82f6',
                            color: '#fff',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            borderRadius: '50%',
                            width: 18,
                            height: 18,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                        >
                          {c.unread_count}
                        </span>
                      )}
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>

        {/* Right Pane: Message Thread Stream & Composer */}
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
          {activeConvId && activeConv ? (
            <>
              {/* Active Conversation Header */}
              <div
                style={{
                  padding: '14px 20px',
                  borderBottom: '1px solid var(--border-color)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  backgroundColor: 'rgba(255, 255, 255, 0.01)',
                }}
              >
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700 }}>
                    {activeConv.subject || 'Direct Conversation'}
                  </h3>
                  <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginTop: 4 }}>
                    <span className="text-muted" style={{ fontSize: '0.8rem' }}>
                      Participants:{' '}
                      {activeConv.participants.map((p) => `${p.name} (${p.role})`).join(', ')}
                    </span>
                    {activeConv.course_code && (
                      <span
                        style={{
                          fontSize: '0.75rem',
                          backgroundColor: 'rgba(59, 130, 246, 0.15)',
                          color: '#3b82f6',
                          padding: '2px 8px',
                          borderRadius: 6,
                          fontWeight: 600,
                        }}
                      >
                        Course: {activeConv.course_code}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Messages History Stream */}
              <div
                style={{
                  flex: 1,
                  padding: '16px 24px',
                  overflowY: 'auto',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 12,
                }}
              >
                {loadingActive ? (
                  <div style={{ textAlign: 'center', margin: 'auto' }} className="text-muted">
                    Loading conversation stream...
                  </div>
                ) : activeConv.messages.length === 0 ? (
                  <div style={{ textAlign: 'center', margin: 'auto' }} className="text-muted">
                    No messages in this conversation yet. Send the first message below.
                  </div>
                ) : (
                  activeConv.messages.map((m) => {
                    const isMe = m.sender_id === user?.id
                    return (
                      <div
                        key={m.id}
                        style={{
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: isMe ? 'flex-end' : 'flex-start',
                          maxWidth: '75%',
                          alignSelf: isMe ? 'flex-end' : 'flex-start',
                        }}
                      >
                        <div
                          style={{
                            fontSize: '0.75rem',
                            color: '#94a3b8',
                            marginBottom: 2,
                            paddingLeft: isMe ? 0 : 4,
                            paddingRight: isMe ? 4 : 0,
                          }}
                        >
                          {!isMe && <strong>{m.sender_name} • </strong>}
                          {new Date(m.sent_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>

                        <div
                          style={{
                            backgroundColor: isMe ? '#2563eb' : 'rgba(255, 255, 255, 0.08)',
                            color: isMe ? '#ffffff' : 'inherit',
                            padding: '10px 14px',
                            borderRadius: isMe ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
                            fontSize: '0.92rem',
                            lineHeight: 1.45,
                            wordBreak: 'break-word',
                            border: isMe ? 'none' : '1px solid rgba(255, 255, 255, 0.05)',
                          }}
                        >
                          {m.content}

                          {m.attachment_url && (
                            <div style={{ marginTop: 8, paddingTop: 6, borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                              <a
                                href={m.attachment_url}
                                target="_blank"
                                rel="noreferrer"
                                style={{
                                  color: isMe ? '#e0f2fe' : '#60a5fa',
                                  fontSize: '0.82rem',
                                  textDecoration: 'underline',
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: 4,
                                }}
                              >
                                📎 {m.attachment_name || 'Download Attachment'}
                              </a>
                            </div>
                          )}
                        </div>

                        {isMe && (
                          <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: 2, paddingRight: 4 }}>
                            {m.is_read ? '✓✓ Read' : '✓ Sent'}
                          </div>
                        )}
                      </div>
                    )
                  })
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Message Composer Form */}
              <form
                onSubmit={handleSendMessage}
                style={{
                  padding: '14px 20px',
                  borderTop: '1px solid var(--border-color)',
                  backgroundColor: 'rgba(255, 255, 255, 0.01)',
                }}
              >
                <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                  <input
                    type="text"
                    placeholder="Type a message..."
                    className="form-control"
                    value={newMessageText}
                    onChange={(e) => setNewMessageText(e.target.value)}
                    style={{ flex: 1 }}
                    disabled={sendingMessage}
                  />
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={!newMessageText.trim() || sendingMessage}
                  >
                    {sendingMessage ? 'Sending...' : 'Send'}
                  </button>
                </div>

                {/* Optional attachment fields */}
                <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
                  <input
                    type="text"
                    placeholder="Attachment URL (optional)"
                    className="form-control"
                    style={{ fontSize: '0.78rem', height: 28 }}
                    value={attachmentUrl}
                    onChange={(e) => setAttachmentUrl(e.target.value)}
                  />
                  <input
                    type="text"
                    placeholder="Attachment filename (optional)"
                    className="form-control"
                    style={{ fontSize: '0.78rem', height: 28 }}
                    value={attachmentName}
                    onChange={(e) => setAttachmentName(e.target.value)}
                  />
                </div>
              </form>
            </>
          ) : (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100%',
                color: '#64748b',
              }}
            >
              <div style={{ fontSize: '3rem', marginBottom: 12 }}>💬</div>
              <h3 style={{ margin: 0, fontWeight: 700 }}>No Conversation Selected</h3>
              <p style={{ marginTop: 6, fontSize: '0.9rem' }}>
                Select a message thread from the left or start a new conversation.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Start New Conversation Modal */}
      {showNewModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.65)',
            backdropFilter: 'blur(4px)',
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
              maxWidth: 520,
              padding: 24,
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 800 }}>Start Direct Conversation</h3>
              <button
                type="button"
                onClick={() => setShowNewModal(false)}
                style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '1.2rem' }}
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleStartConversation}>
              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Recipient *
                </label>
                <select
                  className="form-control"
                  value={selectedRecipientId}
                  onChange={(e) => setSelectedRecipientId(Number(e.target.value) || '')}
                  required
                >
                  <option value="">Select recipient...</option>
                  {contacts.map((c) => (
                    <option key={c.user_id} value={c.user_id}>
                      {c.name} ({c.role}) {c.context ? `— ${c.context}` : ''}
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Subject (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g., Question regarding Assignment 1"
                  className="form-control"
                  value={newSubject}
                  onChange={(e) => setNewSubject(e.target.value)}
                />
              </div>

              <div style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Thread Type
                </label>
                <select
                  className="form-control"
                  value={newThreadType}
                  onChange={(e) => setNewThreadType(e.target.value)}
                >
                  <option value="direct">Direct Message</option>
                  <option value="course_inquiry">Course Inquiry</option>
                  <option value="advisory">Academic Advising</option>
                </select>
              </div>

              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 4 }}>
                  Initial Message *
                </label>
                <textarea
                  className="form-control"
                  rows={4}
                  placeholder="Type your message here..."
                  value={newInitialMessage}
                  onChange={(e) => setNewInitialMessage(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowNewModal(false)}
                  disabled={creatingConv}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={!selectedRecipientId || !newInitialMessage.trim() || creatingConv}
                >
                  {creatingConv ? 'Starting...' : 'Send Message'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
