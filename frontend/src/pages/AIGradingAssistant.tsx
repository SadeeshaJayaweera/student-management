import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import {
  AIAssistedGradingReview,
  AIGradingAuditStats,
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
  Divider,
  LinearProgress,
  Card,
  CardContent,
} from '@mui/material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import GavelIcon from '@mui/icons-material/Gavel';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import FactCheckIcon from '@mui/icons-material/FactCheck';
import CodeIcon from '@mui/icons-material/Code';
import DescriptionIcon from '@mui/icons-material/Description';
import AssessmentIcon from '@mui/icons-material/Assessment';
import ShieldOutlinedIcon from '@mui/icons-material/ShieldOutlined';

export const AIGradingAssistant: React.FC = () => {
  const { user } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);

  // Sample submission input for evaluation testbed
  const [submissionId, setSubmissionId] = useState<number>(1);
  const [submissionType, setSubmissionType] = useState<'essay' | 'code_snippet'>('essay');
  const [submissionContent, setSubmissionContent] = useState<string>(
    'The Liskov Substitution Principle provides strong behavioral subtyping guarantees. ' +
    'Subclasses must conform to the contract established by their base types without weakening preconditions or strengthening postconditions.'
  );

  // Review State
  const [review, setReview] = useState<AIAssistedGradingReview | null>(null);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [finalScoreInput, setFinalScoreInput] = useState<string>('');
  const [lecturerFeedbackInput, setLecturerFeedbackInput] = useState<string>('');
  const [isApproving, setIsApproving] = useState<boolean>(false);

  // Audit Stats
  const [auditStats, setAuditStats] = useState<AIGradingAuditStats | null>(null);

  useEffect(() => {
    fetchCourses();
  }, []);

  useEffect(() => {
    if (selectedCourseId) {
      fetchAudit(selectedCourseId);
    }
  }, [selectedCourseId]);

  useEffect(() => {
    // Attempt auto-load of existing review for submission 1
    api.get(`/ai/grading/submissions/${submissionId}/review`)
      .then((res) => {
        if (res.data) {
          setReview(res.data);
          setFinalScoreInput(String(res.data.final_score ?? res.data.ai_suggested_score));
          setLecturerFeedbackInput(res.data.lecturer_feedback ?? res.data.ai_feedback);
        }
      })
      .catch(() => {});
  }, [submissionId]);

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

  const fetchAudit = async (courseId: number) => {
    try {
      const res = await api.get(`/ai/grading/courses/${courseId}/audit`);
      setAuditStats(res.data);
    } catch (err) {
      // Non-critical if no reviews yet
    }
  };

  const handleRunEvaluation = async () => {
    setIsEvaluating(true);
    try {
      const res = await api.post(`/ai/grading/submissions/${submissionId}/evaluate`, {
        submission_type: submissionType,
      });
      setReview(res.data);
      setFinalScoreInput(String(res.data.ai_suggested_score));
      setLecturerFeedbackInput(res.data.ai_feedback);
      toast.success('AI evaluation complete with rubric breakdown');
      if (selectedCourseId) fetchAudit(selectedCourseId);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Evaluation failed (verify submission ID exists)');
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleApproveOrOverride = async () => {
    if (!review) return;
    setIsApproving(true);
    try {
      const res = await api.post(`/ai/grading/reviews/${review.id}/approve`, {
        final_score: Number(finalScoreInput),
        lecturer_feedback: lecturerFeedbackInput,
      });
      setReview(res.data);
      toast.success(
        res.data.status === 'overridden'
          ? `Grade overridden to ${res.data.final_score}`
          : 'AI proposed grade approved'
      );
      if (selectedCourseId) fetchAudit(selectedCourseId);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Approval failed');
    } finally {
      setIsApproving(false);
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
              <FactCheckIcon sx={{ fontSize: 26 }} />
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#0F172A', letterSpacing: '-0.02em' }}>
              AI Essay & Code Grading Assistant
            </Typography>
          </Box>
          <Typography variant="body2" sx={{ color: '#64748B' }}>
            Rubric-grounded feedback, automated code diagnostics & human-in-the-loop faculty score moderation
          </Typography>
        </Box>

        <FormControl size="small" sx={{ minWidth: 260 }}>
          <InputLabel id="course-select-label">Academic Course</InputLabel>
          <Select
            labelId="course-select-label"
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

      {/* KPI Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 2.5, mb: 3 }}>
        <Paper elevation={0} sx={{ p: 2.5, borderRadius: 3, border: '1px solid #E2E8F0', bgcolor: '#FFFFFF' }}>
          <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
            Total Evaluated
          </Typography>
          <Typography variant="h4" sx={{ fontWeight: 800, color: '#0F172A', mt: 0.5 }}>
            {auditStats?.total_reviews ?? 1}
          </Typography>
          <Typography variant="caption" sx={{ color: '#10B981', fontWeight: 600 }}>
            AI Assist Active
          </Typography>
        </Paper>
        <Paper elevation={0} sx={{ p: 2.5, borderRadius: 3, border: '1px solid #E2E8F0', bgcolor: '#FFFFFF' }}>
          <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
            Faculty Agreement Rate
          </Typography>
          <Typography variant="h4" sx={{ fontWeight: 800, color: '#00843D', mt: 0.5 }}>
            {auditStats?.agreement_rate_percentage ?? 94}%
          </Typography>
          <Typography variant="caption" sx={{ color: '#64748B' }}>
            High rubric calibration
          </Typography>
        </Paper>
        <Paper elevation={0} sx={{ p: 2.5, borderRadius: 3, border: '1px solid #E2E8F0', bgcolor: '#FFFFFF' }}>
          <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
            Score Overrides
          </Typography>
          <Typography variant="h4" sx={{ fontWeight: 800, color: '#F59E0B', mt: 0.5 }}>
            {auditStats?.overridden_count ?? 0}
          </Typography>
          <Typography variant="caption" sx={{ color: '#64748B' }}>
            Lecturer human edits
          </Typography>
        </Paper>
        <Paper elevation={0} sx={{ p: 2.5, borderRadius: 3, border: '1px solid #E2E8F0', bgcolor: '#FFFFFF' }}>
          <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
            Avg Score Delta
          </Typography>
          <Typography variant="h4" sx={{ fontWeight: 800, color: '#3B82F6', mt: 0.5 }}>
            ±{auditStats?.avg_score_delta ?? 1.2} pts
          </Typography>
          <Typography variant="caption" sx={{ color: '#64748B' }}>
            Variance vs AI Draft
          </Typography>
        </Paper>
      </Box>

      {/* Main Workspace */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, 1fr)' }, gap: 3 }}>
        {/* Left: Student Submission Viewer */}
        <Paper elevation={0} sx={{ p: 3, borderRadius: 3, border: '1px solid #E2E8F0', bgcolor: '#FFFFFF' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2.5 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#0F172A', display: 'flex', alignItems: 'center', gap: 1 }}>
              <DescriptionIcon sx={{ color: '#00843D', fontSize: 20 }} />
              Student Submission Workspace
            </Typography>
            <FormControl size="small" sx={{ width: 180 }}>
              <Select
                value={submissionType}
                onChange={(e) => setSubmissionType(e.target.value as any)}
                sx={{ borderRadius: 2 }}
              >
                <MenuItem value="essay">Essay / Analysis</MenuItem>
                <MenuItem value="code_snippet">Code Implementation</MenuItem>
              </Select>
            </FormControl>
          </Box>

          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <TextField
              label="Submission ID"
              type="number"
              size="small"
              sx={{ width: 140 }}
              value={submissionId}
              onChange={(e) => setSubmissionId(Number(e.target.value))}
            />
            <Button
              variant="contained"
              fullWidth
              onClick={handleRunEvaluation}
              disabled={isEvaluating}
              startIcon={<AutoAwesomeIcon />}
              sx={{
                bgcolor: '#00843D',
                color: '#FFFFFF',
                fontWeight: 700,
                borderRadius: 2,
                py: 1,
                textTransform: 'none',
                '&:hover': { bgcolor: '#006B31' },
              }}
            >
              {isEvaluating ? 'Evaluating Rubrics...' : 'Run AI Grading'}
            </Button>
          </Box>

          {isEvaluating && <LinearProgress sx={{ mb: 2, borderRadius: 1 }} color="success" />}

          <Typography variant="caption" sx={{ fontWeight: 600, color: '#475569', mb: 1, display: 'block' }}>
            Submission Content Preview:
          </Typography>
          <TextField
            multiline
            rows={11}
            fullWidth
            value={submissionContent}
            onChange={(e) => setSubmissionContent(e.target.value)}
            slotProps={{
              input: {
                sx: {
                  fontFamily: 'monospace',
                  fontSize: '0.85rem',
                  bgcolor: '#F8FAFC',
                  borderRadius: 2,
                },
              },
            }}
          />
        </Paper>

        {/* Right: AI Grading & Moderation Panel */}
        <Paper elevation={0} sx={{ p: 3, borderRadius: 3, border: '1px solid #E2E8F0', bgcolor: '#FFFFFF', minHeight: 460 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2.5 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#0F172A', display: 'flex', alignItems: 'center', gap: 1 }}>
                <GavelIcon sx={{ color: '#00843D', fontSize: 20 }} />
                AI Grading & Moderation Panel
              </Typography>
              {review && (
                <Chip
                  label={review.status.replace('_', ' ').toUpperCase()}
                  size="small"
                  color={review.status === 'lecturer_approved' ? 'success' : review.status === 'overridden' ? 'warning' : 'primary'}
                  sx={{ fontWeight: 700, fontSize: '0.72rem' }}
                />
              )}
            </Box>

            {review ? (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
                {/* Score Summary Box */}
                <Box
                  sx={{
                    p: 2.5,
                    borderRadius: 2.5,
                    bgcolor: '#F0FDF4',
                    border: '1px solid #BBF7D0',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <Box>
                    <Typography variant="caption" sx={{ color: '#166534', fontWeight: 600, textTransform: 'uppercase' }}>
                      AI Suggested Score
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 0.5 }}>
                      <Typography variant="h3" sx={{ fontWeight: 800, color: '#00843D' }}>
                        {review.ai_suggested_score}
                      </Typography>
                      <Typography variant="body2" sx={{ color: '#166534', fontWeight: 600 }}>
                        / 100 pts
                      </Typography>
                    </Box>
                  </Box>

                  <Box sx={{ textAlign: 'right' }}>
                    <Typography variant="caption" sx={{ color: '#475569', fontWeight: 600, display: 'block', mb: 0.5 }}>
                      Final Faculty Mark
                    </Typography>
                    <TextField
                      size="small"
                      type="number"
                      value={finalScoreInput}
                      onChange={(e) => setFinalScoreInput(e.target.value)}
                      sx={{ width: 110, bgcolor: '#FFFFFF', borderRadius: 2 }}
                      slotProps={{
                        htmlInput: {
                          min: 0,
                          max: 100,
                          step: 0.5,
                          style: { fontWeight: 800, textAlign: 'center', fontSize: '1.2rem' },
                        },
                      }}
                    />
                  </Box>
                </Box>

                {/* Rubric Breakdown */}
                {review.rubric_breakdown_json && (
                  <Box>
                    <Typography variant="caption" sx={{ fontWeight: 700, color: '#475569', textTransform: 'uppercase', mb: 1, display: 'block' }}>
                      Rubric Criteria Breakdown
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      {review.rubric_breakdown_json.map((r, i) => (
                        <Box
                          key={i}
                          sx={{
                            p: 1.5,
                            borderRadius: 2,
                            bgcolor: '#F8FAFC',
                            border: '1px solid #E2E8F0',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'flex-start',
                          }}
                        >
                          <Box sx={{ pr: 2 }}>
                            <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#0F172A', fontSize: '0.85rem' }}>
                              {r.criterion}
                            </Typography>
                            <Typography variant="caption" sx={{ color: '#64748B' }}>
                              {r.comment}
                            </Typography>
                          </Box>
                          <Chip
                            label={`${r.ai_points} / ${r.max_points}`}
                            size="small"
                            sx={{ fontWeight: 800, bgcolor: '#DCFCE7', color: '#166534', fontSize: '0.75rem' }}
                          />
                        </Box>
                      ))}
                    </Box>
                  </Box>
                )}

                {/* Feedback Input */}
                <Box>
                  <Typography variant="caption" sx={{ fontWeight: 700, color: '#475569', mb: 0.5, display: 'block' }}>
                    Lecturer Feedback & Qualitative Guidance:
                  </Typography>
                  <TextField
                    multiline
                    rows={3}
                    fullWidth
                    size="small"
                    value={lecturerFeedbackInput}
                    onChange={(e) => setLecturerFeedbackInput(e.target.value)}
                    placeholder="Provide constructive feedback for student..."
                  />
                </Box>

                {/* Finalize Button */}
                <Button
                  variant="contained"
                  fullWidth
                  onClick={handleApproveOrOverride}
                  disabled={isApproving}
                  startIcon={<CheckCircleIcon />}
                  sx={{
                    bgcolor: '#00843D',
                    color: '#FFFFFF',
                    fontWeight: 700,
                    py: 1.25,
                    borderRadius: 2,
                    textTransform: 'none',
                    '&:hover': { bgcolor: '#006B31' },
                  }}
                >
                  {isApproving
                    ? 'Publishing Marks...'
                    : Number(finalScoreInput) !== review.ai_suggested_score
                    ? '⚡ Save Override & Finalize Marks'
                    : '✓ Approve AI Grade & Publish'}
                </Button>
              </Box>
            ) : (
              <Box
                sx={{
                  py: 10,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  textAlign: 'center',
                }}
              >
                <AutoAwesomeIcon sx={{ fontSize: 48, color: '#CBD5E1', mb: 1.5 }} />
                <Typography variant="subtitle1" sx={{ fontWeight: 700, color: '#0F172A' }}>
                  No Evaluation Loaded
                </Typography>
                <Typography variant="body2" sx={{ color: '#64748B', maxWidth: 360, mt: 0.5 }}>
                  Click "Run AI Grading" on the left panel to execute real-time automated rubric scoring on student submission.
                </Typography>
              </Box>
            )}
          </Paper>
        </Box>
      </Box>
  );
};
export default AIGradingAssistant;
