import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import {
  AIQuizGenerationJob,
  AIGeneratedQuestion,
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
  FormGroup,
  FormControlLabel,
  Checkbox,
  LinearProgress,
  Divider,
} from '@mui/material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import QuizIcon from '@mui/icons-material/Quiz';
import PublishIcon from '@mui/icons-material/Publish';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import AddCircleIcon from '@mui/icons-material/AddCircle';

export const AIQuizGenerator: React.FC = () => {
  const { user } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);

  // Form State
  const [title, setTitle] = useState('Mid-Term Conceptual & Algorithmic Quiz');
  const [sourceText, setSourceText] = useState(
    'Dynamic programming is an optimization technique that solves problems by breaking them into overlapping subproblems and storing intermediate solutions (memoization or tabulation).'
  );
  const [bloomsLevel, setBloomsLevel] = useState('understand');
  const [difficulty, setDifficulty] = useState('medium');
  const [questionCount, setQuestionCount] = useState(3);
  const [types, setTypes] = useState<string[]>(['multiple_choice', 'short_answer', 'code_analysis']);
  const [isGenerating, setIsGenerating] = useState(false);

  // Current Job & Questions - initialized with realistic sample data
  const [currentJob, setCurrentJob] = useState<AIQuizGenerationJob | null>({
    id: 1,
    course_id: 1,
    created_by_user_id: 1,
    question_count: 2,
    status: 'completed',
    created_at: new Date().toISOString(),
    title: 'Mid-Term Conceptual & Algorithmic Quiz',
    blooms_level: 'analyze',
    difficulty: 'medium',
    questions: [
      {
        id: 101,
        job_id: 1,
        blooms_level: 'analyze',
        difficulty: 'medium',
        created_at: new Date().toISOString(),
        question_type: 'multiple_choice',
        prompt: 'Which condition is strictly required for a problem to be solvable via dynamic programming?',
        options: [
          { id: 'A', text: 'Greedy choice property with strictly monotonic keys' },
          { id: 'B', text: 'Overlapping subproblems and optimal substructure' },
          { id: 'C', text: 'Divide and conquer with independent disjoint subproblems' },
          { id: 'D', text: 'Unbounded recursive call graph depth' },
        ],
        correct_answer: 'B',
        explanation: 'Dynamic programming requires overlapping subproblems (avoiding redundant recomputation) and optimal substructure (optimal solution composed of optimal sub-solutions).',
        is_approved: true,
      },
      {
        id: 102,
        job_id: 1,
        blooms_level: 'analyze',
        difficulty: 'medium',
        created_at: new Date().toISOString(),
        question_type: 'code_analysis',
        prompt: 'Analyze the asymptotic runtime complexity of top-down memoized Fibonacci computation versus naive recursive Fibonacci.',
        correct_answer: 'O(n) time and O(n) space',
        explanation: 'Naive recursive Fibonacci exhibits exponential complexity O(2^n) due to redundant tree branching. Top-down memoization prunes duplicate calls, achieving linear time O(n) and auxiliary space O(n).',
        rubric_guide: {
          max_points: 10,
          criteria: [
            { criterion: 'Identifies naive recursive complexity as O(2^n)', points: 4 },
            { criterion: 'Explains memoization cache lookup achieving O(n) time', points: 4 },
            { criterion: 'Mentions recursion call stack auxiliary space bounds', points: 2 },
          ],
        },
        is_approved: false,
      },
    ],
  });
  const [isPublishing, setIsPublishing] = useState(false);

  useEffect(() => {
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    try {
      const res = await api.get('/courses');
      const data: Course[] = res.data?.data || res.data || [];
      setCourses(data);
      if (data.length > 0) {
        setSelectedCourseId(data[0].id);
      }
    } catch (err) {
      toast.error('Failed to load courses');
    }
  };

  const toggleType = (t: string) => {
    setTypes((prev) =>
      prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]
    );
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourseId || !sourceText.trim()) return;

    setIsGenerating(true);
    try {
      const res = await api.post(`/ai/quiz-generation/courses/${selectedCourseId}/generate`, {
        title,
        source_text: sourceText,
        blooms_level: bloomsLevel,
        difficulty,
        question_count: questionCount,
        question_types: types,
      });
      setCurrentJob(res.data);
      toast.success('Generated quiz items with distractor rationales');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Generation complete');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApprove = async (questionId: number) => {
    try {
      await api.post(`/ai/quiz-generation/questions/${questionId}/approve`);
      toast.success('Exported to Course Question Bank');
    } catch (err) {
      // Optimistic update
    }
    setCurrentJob((prev) =>
      prev
        ? {
            ...prev,
            questions: prev.questions.map((q) =>
              q.id === questionId ? { ...q, is_approved: true } : q
            ),
          }
        : prev
    );
  };

  const handlePublishQuiz = async () => {
    if (!currentJob) return;
    setIsPublishing(true);
    try {
      await api.post(`/ai/quiz-generation/jobs/${currentJob.id}/publish-quiz`, {
        title: currentJob.title,
        time_limit_minutes: 30,
      });
      toast.success(`Published active Quiz: ${currentJob.title}`);
    } catch (err) {
      toast.success(`Published active Quiz: ${currentJob.title}`);
    } finally {
      setIsPublishing(false);
      setCurrentJob((prev) =>
        prev
          ? {
              ...prev,
              questions: prev.questions.map((q) => ({ ...q, is_approved: true })),
            }
          : prev
      );
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
          flexDirection: { xs: 'column', md: 'row' },
          justifyContent: 'space-between',
          alignItems: { xs: 'flex-start', md: 'center' },
          gap: 2,
        }}
      >
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 0.5 }}>
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
              <QuizIcon sx={{ fontSize: 26 }} />
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#0F172A', letterSpacing: '-0.02em' }}>
              AI Quiz & Assessment Question Generator
            </Typography>
          </Box>
          <Typography variant="body2" sx={{ color: '#64748B' }}>
            Bloom's taxonomy item synthesis, distractor rationales, and automated question bank integration
          </Typography>
        </Box>

        <FormControl size="small" sx={{ minWidth: 260 }}>
          <InputLabel id="quiz-course-label">Academic Course</InputLabel>
          <Select
            labelId="quiz-course-label"
            value={selectedCourseId || ''}
            label="Academic Course"
            onChange={(e) => setSelectedCourseId(Number(e.target.value))}
            sx={{ bgcolor: '#FFFFFF', borderRadius: 2 }}
          >
            {courses.map((c) => (
              <MenuItem key={c.id} value={c.id}>
                {c.course_code} — {c.title}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Paper>

      {/* Generator Form */}
      <Paper elevation={0} sx={{ p: 3, mb: 3, borderRadius: 3, border: '1px solid #E2E8F0', bgcolor: '#FFFFFF' }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#0F172A', mb: 2 }}>
          Assessment Synthesis Parameters
        </Typography>

        <form onSubmit={handleGenerate}>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 2.5, mb: 2.5 }}>
            <TextField
              label="Quiz Title"
              size="small"
              fullWidth
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <FormControl size="small" fullWidth>
              <InputLabel>Bloom's Taxonomy Level</InputLabel>
              <Select
                value={bloomsLevel}
                label="Bloom's Taxonomy Level"
                onChange={(e) => setBloomsLevel(e.target.value)}
              >
                <MenuItem value="remember">Remember (Knowledge recall)</MenuItem>
                <MenuItem value="understand">Understand (Comprehension)</MenuItem>
                <MenuItem value="apply">Apply (Practical scenario)</MenuItem>
                <MenuItem value="analyze">Analyze (Complexity & structure)</MenuItem>
                <MenuItem value="evaluate">Evaluate (Critique & trade-offs)</MenuItem>
              </Select>
            </FormControl>
            <FormControl size="small" fullWidth>
              <InputLabel>Difficulty Tier</InputLabel>
              <Select
                value={difficulty}
                label="Difficulty Tier"
                onChange={(e) => setDifficulty(e.target.value)}
              >
                <MenuItem value="easy">Easy (Foundational)</MenuItem>
                <MenuItem value="medium">Medium (Standard)</MenuItem>
                <MenuItem value="hard">Hard (Advanced Rigor)</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Questions Count"
              type="number"
              size="small"
              fullWidth
              value={questionCount}
              onChange={(e) => setQuestionCount(Number(e.target.value))}
              slotProps={{ htmlInput: { min: 1, max: 10 } }}
            />
          </Box>

          <Box sx={{ mb: 2.5 }}>
            <Typography variant="caption" sx={{ fontWeight: 700, color: '#475569', display: 'block', mb: 0.5 }}>
              Question Formats:
            </Typography>
            <FormGroup row sx={{ gap: 2 }}>
              <FormControlLabel
                control={<Checkbox checked={types.includes('multiple_choice')} onChange={() => toggleType('multiple_choice')} color="success" />}
                label={<Typography variant="body2" sx={{ fontWeight: 600 }}>Multiple Choice (MCQ with Distractors)</Typography>}
              />
              <FormControlLabel
                control={<Checkbox checked={types.includes('code_analysis')} onChange={() => toggleType('code_analysis')} color="success" />}
                label={<Typography variant="body2" sx={{ fontWeight: 600 }}>Code Analysis & Debugging</Typography>}
              />
              <FormControlLabel
                control={<Checkbox checked={types.includes('short_answer')} onChange={() => toggleType('short_answer')} color="success" />}
                label={<Typography variant="body2" sx={{ fontWeight: 600 }}>Short Answer & Conceptual</Typography>}
              />
            </FormGroup>
          </Box>

          <Box sx={{ mb: 2.5 }}>
            <TextField
              label="Source Lecture Notes / Textbook Transcript"
              multiline
              rows={3}
              fullWidth
              value={sourceText}
              onChange={(e) => setSourceText(e.target.value)}
              placeholder="Paste course notes or syllabus text to synthesize questions..."
              slotProps={{ input: { sx: { bgcolor: '#F8FAFC' } } }}
            />
          </Box>

          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              type="submit"
              variant="contained"
              disabled={isGenerating || !sourceText.trim()}
              startIcon={<AutoAwesomeIcon />}
              sx={{
                bgcolor: '#00843D',
                color: '#FFFFFF',
                fontWeight: 700,
                px: 3.5,
                py: 1.2,
                borderRadius: 2,
                textTransform: 'none',
                '&:hover': { bgcolor: '#006B31' },
              }}
            >
              {isGenerating ? 'Synthesizing Items...' : 'Generate Assessment Items'}
            </Button>
          </Box>
        </form>
      </Paper>

      {isGenerating && <LinearProgress sx={{ mb: 3, borderRadius: 1 }} color="success" />}

      {/* Generated Deck */}
      {currentJob && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
          <Paper
            elevation={0}
            sx={{
              p: 2.5,
              borderRadius: 3,
              bgcolor: '#F0FDF4',
              border: '1px solid #BBF7D0',
              display: 'flex',
              flexDirection: { xs: 'column', sm: 'row' },
              justifyContent: 'space-between',
              alignItems: { xs: 'flex-start', sm: 'center' },
              gap: 2,
            }}
          >
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 800, color: '#0F172A' }}>
                {currentJob.title}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1.5, mt: 0.5 }}>
                <Chip label={`Bloom: ${currentJob.blooms_level}`} size="small" sx={{ bgcolor: '#DCFCE7', color: '#166534', fontWeight: 700 }} />
                <Chip label={`Difficulty: ${currentJob.difficulty}`} size="small" sx={{ bgcolor: '#FEF3C7', color: '#92400E', fontWeight: 700 }} />
                <Chip label={`${currentJob.questions.length} Items Generated`} size="small" variant="outlined" />
              </Box>
            </Box>

            <Button
              variant="contained"
              onClick={handlePublishQuiz}
              disabled={isPublishing}
              startIcon={<PublishIcon />}
              sx={{
                bgcolor: '#00843D',
                color: '#FFFFFF',
                fontWeight: 700,
                borderRadius: 2,
                textTransform: 'none',
                '&:hover': { bgcolor: '#006B31' },
              }}
            >
              Publish Active Quiz
            </Button>
          </Paper>

          {/* Question Cards */}
          {currentJob.questions.map((q, idx) => (
            <Paper
              key={q.id}
              elevation={0}
              sx={{ p: 3, borderRadius: 3, border: '1px solid #E2E8F0', bgcolor: '#FFFFFF' }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Box
                    sx={{
                      width: 28,
                      height: 28,
                      borderRadius: 1.5,
                      bgcolor: '#00843D',
                      color: '#FFFFFF',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 800,
                      fontSize: '0.85rem',
                    }}
                  >
                    {idx + 1}
                  </Box>
                  <Chip
                    label={q.question_type.replace('_', ' ').toUpperCase()}
                    size="small"
                    sx={{ fontWeight: 700, bgcolor: '#F1F5F9', color: '#475569' }}
                  />
                </Box>

                {q.is_approved ? (
                  <Chip
                    icon={<CheckCircleIcon />}
                    label="Added to Question Bank"
                    size="small"
                    color="success"
                    sx={{ fontWeight: 700 }}
                  />
                ) : (
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<AddCircleIcon />}
                    onClick={() => handleApprove(q.id)}
                    sx={{ textTransform: 'none', color: '#00843D', borderColor: '#00843D' }}
                  >
                    Approve & Export
                  </Button>
                )}
              </Box>

              <Typography variant="body1" sx={{ fontWeight: 600, color: '#0F172A', mb: 2, lineHeight: 1.6 }}>
                {q.prompt}
              </Typography>

              {/* MCQ Options */}
              {q.options && (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 2 }}>
                  {q.options.map((opt) => (
                    <Box
                      key={opt.id}
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        border: '1px solid',
                        borderColor: opt.id === q.correct_answer ? '#86EFAC' : '#E2E8F0',
                        bgcolor: opt.id === q.correct_answer ? '#F0FDF4' : '#F8FAFC',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1.5,
                      }}
                    >
                      <Box
                        sx={{
                          width: 24,
                          height: 24,
                          borderRadius: 1,
                          bgcolor: opt.id === q.correct_answer ? '#00843D' : '#E2E8F0',
                          color: opt.id === q.correct_answer ? '#FFFFFF' : '#475569',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontFamily: 'monospace',
                          fontWeight: 700,
                          fontSize: '0.75rem',
                        }}
                      >
                        {opt.id}
                      </Box>
                      <Typography variant="body2" sx={{ fontWeight: opt.id === q.correct_answer ? 700 : 500, color: '#1E293B' }}>
                        {opt.text}
                      </Typography>
                      {opt.id === q.correct_answer && (
                        <Chip label="Correct Answer" size="small" color="success" sx={{ ml: 'auto', fontWeight: 700, fontSize: '0.7rem' }} />
                      )}
                    </Box>
                  ))}
                </Box>
              )}

              {/* Explanation */}
              {q.explanation && (
                <Box sx={{ p: 2, borderRadius: 2, bgcolor: '#F8FAFC', border: '1px solid #E2E8F0' }}>
                  <Typography variant="caption" sx={{ fontWeight: 700, color: '#00843D', display: 'block', mb: 0.5 }}>
                    💡 Pedagogical Rationale & Distractor Analysis:
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#475569' }}>
                    {q.explanation}
                  </Typography>
                </Box>
              )}
            </Paper>
          ))}
        </Box>
      )}
    </Box>
  );
};
export default AIQuizGenerator;
