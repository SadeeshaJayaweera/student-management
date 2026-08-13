import React, { useEffect, useRef, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import api from '@/api/client'
import type { AIMessage } from '@/types'

function formatMarkdown(text: string) {
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code style="background:rgba(255,255,255,.12);padding:2px 6px;border-radius:4px;font-family:monospace;font-size:.85em">$1</code>')
    .replace(/\n/g, '<br />')
}

const SUGGESTIONS = [
  '📚 What are the library borrowing rules?',
  '📊 Explain the NSBM grading system',
  '🎓 What programs does NSBM offer?',
  '⚽ What clubs can I join?',
  '💰 Tell me about scholarships',
  '📝 What are the exam regulations?',
]

export default function AIChat() {
  const { user } = useAuth()
  const [messages, setMessages] = useState<AIMessage[]>([])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const token = localStorage.getItem('token')

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  useEffect(scrollToBottom, [messages, isTyping])

  const sendMessage = async (question: string) => {
    if (!question.trim() || isTyping) return
    setInput('')
    if (textareaRef.current) { textareaRef.current.style.height = 'auto' }

    const userMsg: AIMessage = { role: 'user', content: question, timestamp: new Date() }
    setMessages(prev => [...prev, userMsg])
    setIsTyping(true)

    const aiMsg: AIMessage = { role: 'ai', content: '', timestamp: new Date() }
    setMessages(prev => [...prev, aiMsg])

    try {
      const response = await fetch('/api/ai/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ question }),
      })

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let fullText = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        for (const line of chunk.split('\n')) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.type === 'chunk') {
                fullText += data.content
                setMessages(prev => {
                  const updated = [...prev]
                  updated[updated.length - 1] = { ...aiMsg, content: fullText }
                  return updated
                })
              }
            } catch { /* ignore parse errors */ }
          }
        }
      }
    } catch (e) {
      setMessages(prev => {
        const updated = [...prev]
        updated[updated.length - 1] = { ...aiMsg, content: '⚠️ Connection error. Please try again.' }
        return updated
      })
    } finally {
      setIsTyping(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(input) }
  }

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = `${Math.min(e.target.scrollHeight, 110)}px`
  }

  const initials = user ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) : 'U'

  return (
    <div className="fade-in">
      <div className="page-header">
        <div className="page-title">🤖 EduSphere AI Assistant</div>
        <div className="page-subtitle">Powered by RAG + MCP · Real-time university knowledge</div>
      </div>

      <div className="chat-wrap">
        {/* Header */}
        <div className="chat-header">
          <div style={{ width: 42, height: 42, borderRadius: 12, background: 'linear-gradient(135deg,#6C63FF,#00D4AA)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.3rem', flexShrink: 0 }}>🤖</div>
          <div>
            <div style={{ fontWeight: 700 }}>EduSphere AI</div>
            <div className="text-xs text-muted flex items-center gap-8">
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#00D4AA', display: 'inline-block' }} className="pulse" />
              RAG + MCP Active · Knowledge Base Loaded
            </div>
          </div>
          <button className="btn btn-ghost btn-sm" style={{ marginLeft: 'auto' }} onClick={() => setMessages([])}>🗑️ Clear</button>
        </div>

        {/* Suggestion chips */}
        <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', overflowX: 'auto' }}>
          <div className="flex gap-8" style={{ flexWrap: 'nowrap', whiteSpace: 'nowrap' }}>
            {SUGGESTIONS.map(s => (
              <button key={s} className="btn btn-ghost btn-sm" style={{ flexShrink: 0 }} onClick={() => sendMessage(s.slice(2).trim())}>{s}</button>
            ))}
          </div>
        </div>

        {/* Messages */}
        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="chat-msg ai">
              <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg,#6C63FF,#00D4AA)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>🤖</div>
              <div className="chat-bubble">
                <strong>👋 Hello, {user?.full_name.split(' ')[0]}!</strong><br /><br />
                I'm <strong>EduSphere AI</strong>, your intelligent university assistant powered by{' '}
                <span style={{ color: '#8B85FF' }}>RAG</span> and <span style={{ color: '#00D4AA' }}>MCP</span> technology.<br /><br />
                I can help you with grades, library searches, schedules, clubs, news, scholarships, and much more. Ask me anything! 😊
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`chat-msg ${msg.role}`}>
              {msg.role === 'ai'
                ? <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg,#6C63FF,#00D4AA)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>🤖</div>
                : <div className="avatar avatar-sm">{initials}</div>
              }
              <div className="chat-bubble"
                dangerouslySetInnerHTML={{ __html: msg.role === 'ai' ? formatMarkdown(msg.content) : msg.content }} />
            </div>
          ))}

          {isTyping && messages[messages.length - 1]?.role === 'ai' && messages[messages.length - 1]?.content === '' && (
            <div className="chat-msg ai">
              <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg,#6C63FF,#00D4AA)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>🤖</div>
              <div className="chat-bubble">
                <div className="flex gap-8 items-center">
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="chat-input-row">
          <div className="avatar avatar-sm">{initials}</div>
          <textarea
            ref={textareaRef}
            className="chat-textarea"
            placeholder="Ask me anything about NSBM… (Enter to send, Shift+Enter for newline)"
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            rows={1}
          />
          <button className="btn btn-primary btn-icon" onClick={() => sendMessage(input)} disabled={isTyping || !input.trim()}>➤</button>
        </div>
      </div>
    </div>
  )
}
