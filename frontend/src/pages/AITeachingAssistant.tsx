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
import {
  Box,
  Typography,
  Paper,
  Button,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Chip,
  Avatar,
  Divider,
  LinearProgress,
} from '@mui/material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import PsychologyIcon from '@mui/icons-material/Psychology';
import SendIcon from '@mui/icons-material/Send';
import AddIcon from '@mui/icons-material/Add';
import SchoolIcon from '@mui/icons-material/School';
import LightbulbOutlinedIcon from '@mui/icons-material/LightbulbOutlined';

export const AITeachingAssistant: React.FC = () => {
  const { user } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]);
  const [sessions, setSessions] = useState<AITeachingSession[]>([
    {
      id: 1,
      course_id: 1,
      title: 'Algorithmic Invariants & Recursion',
      teaching_mode: 'socratic',
      student_id: 1,
      is_active: true,
      turn_count: 3,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: 2,
      course_id: 2,
      title: 'Dynamic Programming Subproblems',
      teaching_mode: 'socratic',
      student_id: 1,
      is_active: false,
      turn_count: 5,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ]);
  const [currentSession, setCurrentSession] = useState<AITeachingSessionDetail | null>({
    id: 1,
    course_id: 1,
    title: 'Algorithmic Invariants & Recursion',
    teaching_mode: 'socratic',
    student_id: 1,
    is_active: true,
    turn_count: 3,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    messages: [
      {
        id: 1,
        session_id: 1,
        role: 'assistant',
        content: "Welcome Chamara! Today we're exploring recursion. When designing a recursive algorithm to compute the nth Fibonacci number, what is the first condition you must define before making recursive calls?",
        socratic_phase: 'inquiry',
        tokens_used: 38,
        guardrail_triggered: false,
        created_at: new Date().toISOString(),
      },
      {
        id: 2,
        session_id: 1,
        role: 'user',
        content: "We need base cases, like if n is 0 or 1, we return immediately.",
        socratic_phase: 'response',
        tokens_used: 18,
        guardrail_triggered: false,
        created_at: new Date().toISOString(),
      },
      {
        id: 3,
        session_id: 1,
        role: 'assistant',
        content: "Spot on! Base cases halt the recursive descent. Now, what happens to the call stack if n = 50 and we don't store previous results? What computational pattern do you observe?",
        socratic_phase: 'guiding_hint',
        tokens_used: 42,
        guardrail_triggered: false,
        created_at: new Date().toISOString(),
      },
    ],
  });
  const [inputMessage, setInputMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchCoursesAndSessions();
  }, []);

  const fetchCoursesAndSessions = async () => {
    try {
      const [coursesRes, sessionsRes] = await Promise.all([
        api.get('/courses'),
        api.get('/ai/teaching/sessions'),
      ]);
      const coursesData = coursesRes.data?.data || coursesRes.data || [];
      setCourses(coursesData);

      const sessionsData = sessionsRes.data || [];
      if (sessionsData.length > 0) {
        setSessions(sessionsData);
        selectSession(sessionsData[0].id);
      }
    } catch (err) {
      // Keep demo session
    }
  };

  const selectSession = async (sessionId: number) => {
    try {
      const res = await api.get(`/ai/teaching/sessions/${sessionId}`);
      if (res.data) setCurrentSession(res.data);
    } catch (err) {
      // Keep existing session
    }
  };

  const handleSendMessage = async () => {
    const text = inputMessage.trim();
    if (!text || !currentSession || isSending) return;

    setIsSending(true);
    setInputMessage('');

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
      const res = await api.post(`/ai/teaching/sessions/${currentSession.id}/messages`, {
        content: text,
      });
      setCurrentSession((prev) =>
        prev ? { ...prev, messages: [...prev.messages, res.data] } : prev
      );
    } catch (err) {
      // Mock follow-up response if offline
      setTimeout(() => {
        const mockBotMsg: AITeachingMessage = {
          id: Date.now() + 1,
          session_id: currentSession.id,
          role: 'assistant',
          content: "Excellent insight! Without memoization, redundant tree branches explode exponentially to O(2^n). How would storing solved sub-problems in a hash map change the time complexity?",
          socratic_phase: 'scaffolding',
          tokens_used: 35,
          guardrail_triggered: false,
          created_at: new Date().toISOString(),
        };
        setCurrentSession((prev) =>
          prev ? { ...prev, messages: [...prev.messages, mockBotMsg] } : prev
        );
      }, 700);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 1400, mx: 'auto', p: { xs: 2, md: 4 } }}>
      {/* Header Banner */}
      <Paper
        elevation={0}
        sx={{
          p: 3,
          mb: 3,
          borderRadius: 3,
          border: '1px solid #E2E8F0',
          background: 'linear-gradient(135deg, #FFFFFF 0%, #F0FDF4 100%)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Box
            sx={{
              width: 44,
              height: 44,
              borderRadius: 2.5,
              bgcolor: 'rgba(0, 132, 61, 0.1)',
              color: '#00843D',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <PsychologyIcon sx={{ fontSize: 26 }} />
          </Box>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#0F172A', letterSpacing: '-0.02em' }}>
              Socratic AI Teaching Assistant
            </Typography>
            <Typography variant="body2" sx={{ color: '#64748B' }}>
              Reflective pedagogy, course boundary guardrails & adaptive hint scaffolding
            </Typography>
          </Box>
        </Box>

        <Chip
          icon={<AutoAwesomeIcon />}
          label="Socratic Mode Active"
          sx={{ bgcolor: '#DCFCE7', color: '#166534', fontWeight: 700 }}
        />
      </Paper>

      {/* Main Grid */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '340px 1fr' }, gap: 3 }}>
        {/* Left: Sessions List */}
        <Paper elevation={0} sx={{ p: 2.5, borderRadius: 3, border: '1px solid #E2E8F0', bgcolor: '#FFFFFF', height: '100%' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#0F172A' }}>
                Tutoring Sessions
              </Typography>
              <Button size="small" startIcon={<AddIcon />} sx={{ color: '#00843D', textTransform: 'none', fontWeight: 700 }}>
                New Session
              </Button>
            </Box>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {sessions.map((s) => (
                <Box
                  key={s.id}
                  onClick={() => selectSession(s.id)}
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    border: '1px solid',
                    borderColor: currentSession?.id === s.id ? '#00843D' : '#E2E8F0',
                    bgcolor: currentSession?.id === s.id ? '#F0FDF4' : '#F8FAFC',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    '&:hover': { borderColor: '#00843D' },
                  }}
                >
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#0F172A' }}>
                    {s.title}
                  </Typography>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                    <Chip label={s.teaching_mode} size="small" sx={{ fontSize: '0.7rem', height: 20 }} />
                    <Typography variant="caption" sx={{ color: '#64748B' }}>
                      {s.turn_count} interactions
                    </Typography>
                  </Box>
                </Box>
              ))}
            </Box>
          </Paper>

        {/* Right: Active Chat Window */}
        <Paper
          elevation={0}
          sx={{
            p: 3,
            borderRadius: 3,
            border: '1px solid #E2E8F0',
            bgcolor: '#FFFFFF',
            display: 'flex',
            flexDirection: 'column',
            height: 560,
          }}
        >
            {/* Session Header */}
            <Box sx={{ pb: 2, mb: 2, borderBottom: '1px solid #F1F5F9', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#0F172A' }}>
                {currentSession?.title}
              </Typography>
              <Chip
                label="Pedagogical Guardrails: ON"
                size="small"
                sx={{ bgcolor: '#F0FDF4', color: '#166534', border: '1px solid #BBF7D0', fontWeight: 600 }}
              />
            </Box>

            {/* Messages Thread */}
            <Box sx={{ flex: 1, overflowY: 'auto', pr: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
              {currentSession?.messages.map((m) => (
                <Box
                  key={m.id}
                  sx={{
                    display: 'flex',
                    flexDirection: m.role === 'user' ? 'row-reverse' : 'row',
                    gap: 1.5,
                    alignItems: 'flex-start',
                  }}
                >
                  <Avatar
                    sx={{
                      width: 34,
                      height: 34,
                      bgcolor: m.role === 'user' ? '#00843D' : '#0F172A',
                      fontSize: '0.8rem',
                      fontWeight: 700,
                    }}
                  >
                    {m.role === 'user' ? 'CB' : 'AI'}
                  </Avatar>
                  <Paper
                    elevation={0}
                    sx={{
                      p: 2,
                      maxWidth: '75%',
                      borderRadius: 2.5,
                      bgcolor: m.role === 'user' ? '#F0FDF4' : '#F8FAFC',
                      border: '1px solid',
                      borderColor: m.role === 'user' ? '#BBF7D0' : '#E2E8F0',
                    }}
                  >
                    <Typography variant="body2" sx={{ color: '#1E293B', lineHeight: 1.6 }}>
                      {m.content}
                    </Typography>
                    {m.socratic_phase && m.role === 'assistant' && (
                      <Chip
                        icon={<LightbulbOutlinedIcon sx={{ fontSize: 14 }} />}
                        label={`Phase: ${m.socratic_phase}`}
                        size="small"
                        sx={{ mt: 1, height: 20, fontSize: '0.68rem', bgcolor: '#FFFFFF', border: '1px solid #E2E8F0' }}
                      />
                    )}
                  </Paper>
                </Box>
              ))}
              <div ref={messagesEndRef} />
            </Box>

            {/* Input Bar */}
            <Box sx={{ pt: 2, mt: 'auto', borderTop: '1px solid #F1F5F9', display: 'flex', gap: 1.5 }}>
              <TextField
                fullWidth
                size="small"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder="Reply with your reasoning..."
                sx={{ bgcolor: '#F8FAFC', borderRadius: 2 }}
              />
              <Button
                variant="contained"
                onClick={handleSendMessage}
                disabled={isSending || !inputMessage.trim()}
                sx={{
                  bgcolor: '#00843D',
                  color: '#FFFFFF',
                  px: 3,
                  borderRadius: 2,
                  textTransform: 'none',
                  fontWeight: 700,
                  '&:hover': { bgcolor: '#006B31' },
                }}
              >
                Send
              </Button>
            </Box>
          </Paper>
      </Box>
    </Box>
  );
};
export default AITeachingAssistant;
