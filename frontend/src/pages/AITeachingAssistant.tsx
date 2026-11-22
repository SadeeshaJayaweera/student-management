import React, { useState, useEffect, useRef } from 'react';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import {
  AITeachingSession,
  AITeachingSessionDetail,
  AITeachingMessage,
  Course,
} from '../types';
import toast from 'react-hot-toast';

export const AITeachingAssistant: React.FC = () => {
  const { user } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]);
  const [sessions, setSessions] = useState<AITeachingSession[]>([]);
  const [currentSession, setCurrentSession] = useState<AITeachingSessionDetail | null>(null);
  const [inputMessage, setInputMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [showNewModal, setShowNewModal] = useState(false);
  const [newSessionData, setNewSessionData] = useState({
    course_id: 0,
    title: 'Tutoring Session',
    teaching_mode: 'socratic' as 'socratic' | 'explainer' | 'exam_prep' | 'code_mentor',
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchCoursesAndSessions();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentSession?.messages, isSending]);

  const fetchCoursesAndSessions = async () => {
    try {
      const [coursesRes, sessionsRes] = await Promise.all([
        api.get('/courses'),
        api.get('/ai/teaching/sessions'),
      ]);
      const coursesData = coursesRes.data?.data || coursesRes.data || [];
      setCourses(coursesData);
      if (coursesData.length > 0 && newSessionData.course_id === 0) {
        setNewSessionData((prev) => ({ ...prev, course_id: coursesData[0].id }));
      }

      const sessionsData = sessionsRes.data || [];
      setSessions(sessionsData);
      if (sessionsData.length > 0) {
        selectSession(sessionsData[0].id);
      }
    } catch (err) {
      toast.error('Failed to initialize teaching assistant');
    }
  };

  const selectSession = async (sessionId: number) => {
    try {
      const res = await api.get(`/ai/teaching/sessions/${sessionId}`);
      setCurrentSession(res.data);
    } catch (err) {
      toast.error('Failed to load session dialog');
    }
  };

  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSessionData.course_id) return;

    try {
      const res = await api.post('/ai/teaching/sessions', newSessionData);
      toast.success('Teaching session started');
      setShowNewModal(false);
      setSessions((prev) => [res.data, ...prev]);
      selectSession(res.data.id);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to create session');
    }
  };

  const handleSendMessage = async (contentToSend?: string) => {
    const text = (contentToSend || inputMessage).trim();
    if (!text || !currentSession || isSending) return;

    setIsSending(true);
    setInputMessage('');

    // Optimistically add student user message
    const tempUserMsg: AITeachingMessage = {
      id: Date.now(),
      session_id: currentSession.id,
      role: 'user',
      content: text,
      socratic_phase: 'inquiry',
      tokens_used: text.split(' ').length,
      guardrail_triggered: false,
      created_at: new Date().toISOString(),
    };

    setCurrentSession((prev) =>
      prev ? { ...prev, messages: [...prev.messages, tempUserMsg] } : prev
    );

    try {
      const res = await api.post(`/ai/teaching/sessions/${currentSession.id}/chat`, {
        content: text,
      });
      const botMsg: AITeachingMessage = res.data;
      setCurrentSession((prev) =>
        prev
          ? {
              ...prev,
              messages: [...prev.messages, botMsg],
              turn_count: prev.turn_count + 1,
            }
          : prev
      );
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to send message');
    } finally {
      setIsSending(false);
    }
  };

  const getPhaseBadgeColor = (phase: string) => {
    switch (phase) {
      case 'inquiry':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'hint':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'verification':
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'reflection':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      case 'summary':
        return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30';
      case 'guardrail':
        return 'bg-rose-500/20 text-rose-400 border-rose-500/30';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white/10 backdrop-blur-md p-6 rounded-2xl border border-white/20 shadow-xl">
        <div>
          <h1 className="text-3xl font-extrabold text-white flex items-center gap-3">
            <span>🎓</span> Socratic AI Teaching Assistant
          </h1>
          <p className="text-gray-300 mt-1">
            Reflective dialog, pedagogical scaffolding, course boundary guardrails & adaptive hint progression
          </p>
        </div>

        <button
          onClick={() => setShowNewModal(true)}
          className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-5 py-2.5 rounded-xl transition shadow flex items-center gap-2"
        >
          <span>➕</span> New Tutoring Session
        </button>
      </div>

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sessions Sidebar */}
        <div className="lg:col-span-1 bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-4 space-y-3 h-[680px] flex flex-col">
          <h3 className="text-sm font-bold text-gray-300 uppercase tracking-wider px-2">
            My Tutoring Sessions
          </h3>

          <div className="flex-1 overflow-y-auto space-y-2 pr-1">
            {sessions.length === 0 ? (
              <div className="text-center py-12 text-xs text-gray-400">
                No active tutoring sessions. Start a new one!
              </div>
            ) : (
              sessions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => selectSession(s.id)}
                  className={`w-full text-left p-3.5 rounded-xl transition flex flex-col gap-1 border ${
                    currentSession?.id === s.id
                      ? 'bg-indigo-600/30 border-indigo-400/40 text-white shadow'
                      : 'bg-black/20 border-white/5 text-gray-300 hover:bg-white/5'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm truncate">{s.title}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/10 font-mono capitalize">
                      {s.teaching_mode}
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-xs text-gray-400">
                    <span>Turns: {s.turn_count}</span>
                    <span className="text-[11px]">
                      {new Date(s.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Chat Thread */}
        <div className="lg:col-span-3 bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 flex flex-col h-[680px] overflow-hidden">
          {currentSession ? (
            <>
              {/* Chat Session Topbar */}
              <div className="p-4 border-b border-white/10 bg-white/5 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-white flex items-center gap-2">
                    <span>💬</span> {currentSession.title}
                  </h2>
                  <div className="text-xs text-gray-400 flex items-center gap-2 mt-0.5">
                    <span className="capitalize text-indigo-300 font-medium">
                      Mode: {currentSession.teaching_mode.replace('_', ' ')}
                    </span>
                    <span>·</span>
                    <span>{currentSession.turn_count} pedagogical turns completed</span>
                  </div>
                </div>

                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  Active Tutor
                </span>
              </div>

              {/* Message History */}
              <div className="flex-1 overflow-y-auto p-6 space-y-5">
                {currentSession.messages.map((m) => (
                  <div
                    key={m.id}
                    className={`flex flex-col ${
                      m.role === 'user' ? 'items-end' : 'items-start'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1 px-1">
                      <span className="text-xs text-gray-400">
                        {m.role === 'user' ? 'You' : 'Socratic AI Tutor'}
                      </span>
                      {m.role === 'assistant' && (
                        <span
                          className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-full border ${getPhaseBadgeColor(
                            m.socratic_phase
                          )}`}
                        >
                          {m.socratic_phase}
                        </span>
                      )}
                    </div>

                    <div
                      className={`max-w-2xl p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-line ${
                        m.role === 'user'
                          ? 'bg-indigo-600 text-white shadow-lg'
                          : m.guardrail_triggered
                          ? 'bg-rose-950/60 border border-rose-500/40 text-rose-200'
                          : 'bg-gray-900/80 border border-white/10 text-gray-200 shadow'
                      }`}
                    >
                      {m.content}

                      {/* Progressive Hints Drawer */}
                      {m.hints && m.hints.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-white/10 space-y-1.5">
                          <span className="text-xs font-bold text-amber-300 uppercase tracking-wider flex items-center gap-1">
                            <span>💡</span> Progressive Hints:
                          </span>
                          {m.hints.map((hint, idx) => (
                            <div
                              key={idx}
                              className="text-xs text-amber-200/90 bg-amber-500/10 p-2 rounded-lg border border-amber-500/20"
                            >
                              {hint}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Follow-up suggestion pills */}
                    {m.role === 'assistant' && m.suggested_followups && m.suggested_followups.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2 max-w-2xl">
                        {m.suggested_followups.map((fu, idx) => (
                          <button
                            key={idx}
                            onClick={() => handleSendMessage(fu)}
                            className="text-xs bg-white/5 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-400/30 rounded-xl px-3 py-1.5 transition text-left"
                          >
                            👉 {fu}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}

                {isSending && (
                  <div className="flex items-center gap-2 text-xs text-indigo-400 italic">
                    <span className="animate-spin text-base">⏳</span> Socratic tutor is formulating pedagogical questions...
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input Row */}
              <div className="p-4 border-t border-white/10 bg-white/5">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSendMessage();
                  }}
                  className="flex gap-3"
                >
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Type your thought, hypothesis, or attempt (or ask for a hint)..."
                    className="flex-1 bg-black/40 border border-gray-700 text-white rounded-xl px-4 py-3 focus:ring-2 focus:ring-indigo-500 focus:outline-none placeholder-gray-500 text-sm"
                  />
                  <button
                    type="submit"
                    disabled={isSending || !inputMessage.trim()}
                    className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold px-6 py-3 rounded-xl transition flex items-center gap-2 shadow"
                  >
                    <span>➤</span> Send
                  </button>
                </form>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-400 space-y-3 p-6 text-center">
              <span className="text-4xl">📚</span>
              <p className="text-lg font-semibold text-white">No Session Selected</p>
              <p className="text-sm max-w-sm">
                Choose an existing tutoring session on the left or click "New Tutoring Session" to begin.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* New Session Modal */}
      {showNewModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-gray-900 border border-white/20 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-xl font-bold text-white">Start Tutoring Session</h3>
            <form onSubmit={handleCreateSession} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Course</label>
                <select
                  value={newSessionData.course_id}
                  onChange={(e) =>
                    setNewSessionData({ ...newSessionData, course_id: Number(e.target.value) })
                  }
                  className="w-full bg-black/40 border border-gray-700 rounded-xl px-4 py-2 text-white"
                >
                  {courses.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.course_code} — {c.title}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Session Title</label>
                <input
                  type="text"
                  required
                  value={newSessionData.title}
                  onChange={(e) => setNewSessionData({ ...newSessionData, title: e.target.value })}
                  placeholder="e.g. Graph Algorithms Deep Dive"
                  className="w-full bg-black/40 border border-gray-700 rounded-xl px-4 py-2 text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Teaching Mode</label>
                <select
                  value={newSessionData.teaching_mode}
                  onChange={(e) =>
                    setNewSessionData({
                      ...newSessionData,
                      teaching_mode: e.target.value as any,
                    })
                  }
                  className="w-full bg-black/40 border border-gray-700 rounded-xl px-4 py-2 text-white"
                >
                  <option value="socratic">Socratic Tutor (Guided Questioning)</option>
                  <option value="explainer">Explainer (Direct Conceptual Clarity)</option>
                  <option value="exam_prep">Exam Prep (Practice & High-Yield Questions)</option>
                  <option value="code_mentor">Code Mentor (Algorithm & Syntax Scaffolding)</option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNewModal(false)}
                  className="px-4 py-2 rounded-xl text-gray-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-5 py-2 rounded-xl"
                >
                  Start Session
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default AITeachingAssistant;
