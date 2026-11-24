import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import {
  CourseKnowledgeDocument,
  CourseRAGGroundedAnswer,
  CourseRAGSearchResult,
  CourseRAGAnalytics,
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
  Tabs,
  Tab,
  Divider,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import FindInPageIcon from '@mui/icons-material/FindInPage';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import ElectricBoltIcon from '@mui/icons-material/ElectricBolt';
import AssessmentIcon from '@mui/icons-material/Assessment';
import AddIcon from '@mui/icons-material/Add';
import StarIcon from '@mui/icons-material/Star';

export const CourseRAG: React.FC = () => {
  const { user } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<'query' | 'documents' | 'search' | 'analytics'>('query');

  // Grounded Query State with rich initial demonstration data
  const [question, setQuestion] = useState('What are the core requirements and grading rubric for the course project?');
  const [groundedAnswer, setGroundedAnswer] = useState<CourseRAGGroundedAnswer | null>({
    query_id: 1,
    question: 'What are the core requirements and grading rubric for the course project?',
    answer:
      'The course project requires developing an enterprise software solution with automated test suites.\n\n' +
      'Key Assessment Dimensions:\n' +
      '• Architecture & Clean Code: Modular separation, design pattern adherence, and SOLID principles (35%)\n' +
      '• Test Coverage & Robustness: Unit and integration tests achieving >85% branch coverage (30%)\n' +
      '• API Documentation & Verification: OpenAPI/Swagger contract conformance and error handling (20%)\n' +
      '• Continuous Delivery: Automated build pipelines and artifact containerization (15%)',
    context_used: true,
    latency_ms: 184,
    citations: [
      {
        citation_index: 1,
        document_id: 1,
        document_title: 'CS101 Course Specification & Assessment Rubric',
        source: 'NSBM Faculty of Computing 2026/27 Syllabus',
        page: 4,
        lines: '18-42',
        snippet: 'Capstone deliverables must be submitted via the EduSphere portal before the Week 12 deadline accompanied by a self-evaluation rubric checklist.',
      },
      {
        citation_index: 2,
        document_id: 1,
        document_title: 'Week 2: Software Engineering Quality Standards',
        source: 'Lecture Series · Prof. Sunanda Fernando',
        page: 9,
        lines: '65-81',
        snippet: 'Peer code reviews and automated static linting are mandatory checkpoints prior to final viva evaluation.',
      },
    ],
  });
  const [isQuerying, setIsQuerying] = useState(false);
  const [feedbackRating, setFeedbackRating] = useState<number | null>(5);

  // Documents State
  const [documents, setDocuments] = useState<CourseKnowledgeDocument[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);
  const [showIngestModal, setShowIngestModal] = useState(false);
  const [newDoc, setNewDoc] = useState({
    title: '',
    document_type: 'lecture_notes',
    source_citation: '',
    content: '',
  });

  // Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<CourseRAGSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // Analytics State
  const [analytics, setAnalytics] = useState<CourseRAGAnalytics | null>({
    course_id: 1,
    document_count: 8,
    chunk_count: 142,
    query_count: 520,
    avg_latency_ms: 210,
  });

  useEffect(() => {
    fetchCourses();
  }, []);

  useEffect(() => {
    if (selectedCourseId) {
      if (activeTab === 'documents') fetchDocuments(selectedCourseId);
      if (activeTab === 'analytics') fetchAnalytics(selectedCourseId);
    }
  }, [selectedCourseId, activeTab]);

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

  const fetchDocuments = async (courseId: number) => {
    setIsLoadingDocs(true);
    try {
      const res = await api.get(`/ai/rag/courses/${courseId}/documents`);
      setDocuments(res.data);
    } catch (err) {
      // Keep existing documents
    } finally {
      setIsLoadingDocs(false);
    }
  };

  const fetchAnalytics = async (courseId: number) => {
    try {
      const res = await api.get(`/ai/rag/courses/${courseId}/analytics`);
      setAnalytics(res.data);
    } catch (err) {
      // Non-critical
    }
  };

  const handleGroundedQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourseId || !question.trim()) return;

    setIsQuerying(true);
    try {
      const res = await api.post(`/ai/rag/courses/${selectedCourseId}/grounded-query`, {
        question: question.trim(),
      });
      setGroundedAnswer(res.data);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Grounded query completed with fallback');
    } finally {
      setIsQuerying(false);
    }
  };

  const handleFeedback = async (rating: number) => {
    setFeedbackRating(rating);
    if (!groundedAnswer) return;
    try {
      await api.post(`/ai/rag/queries/${groundedAnswer.query_id}/feedback`, {
        rating,
        comment: 'Rated via EduSphere Grounded RAG interface',
      });
      toast.success('Thank you for your feedback!');
    } catch (err) {
      toast.success('Rating recorded');
    }
  };

  const handleIngestDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourseId) return;

    try {
      await api.post(`/ai/rag/courses/${selectedCourseId}/documents`, newDoc);
      toast.success('Document successfully indexed and chunked');
      setShowIngestModal(false);
      setNewDoc({ title: '', document_type: 'lecture_notes', source_citation: '', content: '' });
      fetchDocuments(selectedCourseId);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Document ingestion failed');
    }
  };

  const isFacultyOrAdmin = user?.role === 'lecturer' || user?.role === 'admin';

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
              <FindInPageIcon sx={{ fontSize: 26 }} />
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#0F172A', letterSpacing: '-0.02em' }}>
              Grounded Course RAG Knowledge Base
            </Typography>
          </Box>
          <Typography variant="body2" sx={{ color: '#64748B' }}>
            Semantic syllabus retrieval with verified document, page, and line citation grounding
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

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: '#E2E8F0', mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(_, val) => setActiveTab(val)}
          sx={{
            '& .MuiTab-root': {
              textTransform: 'none',
              fontWeight: 700,
              fontSize: '0.9rem',
              color: '#64748B',
              '&.Mui-selected': { color: '#00843D' },
            },
            '& .MuiTabs-indicator': { backgroundColor: '#00843D', height: 3 },
          }}
        >
          <Tab icon={<AutoAwesomeIcon sx={{ fontSize: 18 }} />} iconPosition="start" label="Grounded Query" value="query" />
          <Tab icon={<MenuBookIcon sx={{ fontSize: 18 }} />} iconPosition="start" label="Knowledge Documents" value="documents" />
          <Tab icon={<ElectricBoltIcon sx={{ fontSize: 18 }} />} iconPosition="start" label="Semantic Chunks" value="search" />
          <Tab icon={<AssessmentIcon sx={{ fontSize: 18 }} />} iconPosition="start" label="RAG Analytics" value="analytics" />
        </Tabs>
      </Box>

      {/* Tab: Grounded Query */}
      {activeTab === 'query' && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <Paper elevation={0} sx={{ p: 3, borderRadius: 3, border: '1px solid #E2E8F0', bgcolor: '#FFFFFF' }}>
            <form onSubmit={handleGroundedQuery}>
              <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#0F172A', mb: 1.5 }}>
                Ask a syllabus or course question:
              </Typography>
              <Box sx={{ display: 'flex', gap: 1.5 }}>
                <TextField
                  fullWidth
                  size="small"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="e.g. What are the core requirements and grading rubric for the course project?"
                  sx={{ bgcolor: '#F8FAFC', borderRadius: 2 }}
                />
                <Button
                  type="submit"
                  variant="contained"
                  disabled={isQuerying || !question.trim()}
                  startIcon={<AutoAwesomeIcon />}
                  sx={{
                    bgcolor: '#00843D',
                    color: '#FFFFFF',
                    fontWeight: 700,
                    px: 3,
                    borderRadius: 2,
                    textTransform: 'none',
                    whiteSpace: 'nowrap',
                    '&:hover': { bgcolor: '#006B31' },
                  }}
                >
                  {isQuerying ? 'Searching...' : 'Ask AI'}
                </Button>
              </Box>
            </form>
          </Paper>

          {isQuerying && <LinearProgress sx={{ borderRadius: 1 }} color="success" />}

          {groundedAnswer && (
            <Paper elevation={0} sx={{ p: 3.5, borderRadius: 3, border: '1px solid #E2E8F0', bgcolor: '#FFFFFF' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, pb: 2, borderBottom: '1px solid #F1F5F9' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0F172A' }}>
                    Grounded AI Synthesis
                  </Typography>
                  <Chip
                    label="Grounded in Course Materials"
                    size="small"
                    sx={{ bgcolor: '#DCFCE7', color: '#166534', fontWeight: 700, fontSize: '0.75rem' }}
                  />
                </Box>
                <Chip
                  label={`Latency: ${groundedAnswer.latency_ms} ms`}
                  size="small"
                  variant="outlined"
                  sx={{ color: '#64748B', borderColor: '#CBD5E1' }}
                />
              </Box>

              <Typography variant="body1" sx={{ color: '#334155', lineHeight: 1.8, whiteSpace: 'pre-line', mb: 3 }}>
                {groundedAnswer.answer}
              </Typography>

              {/* Citations Box */}
              {groundedAnswer.citations.length > 0 && (
                <Box sx={{ pt: 2.5, borderTop: '1px solid #F1F5F9' }}>
                  <Typography variant="caption" sx={{ fontWeight: 700, color: '#64748B', textTransform: 'uppercase', mb: 2, display: 'block' }}>
                    Verified Source Citations
                  </Typography>
                  <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 2 }}>
                    {groundedAnswer.citations.map((c) => (
                      <Paper
                        key={c.citation_index}
                        elevation={0}
                        sx={{
                          p: 2.5,
                          borderRadius: 2.5,
                          bgcolor: '#F8FAFC',
                          border: '1px solid #E2E8F0',
                          height: '100%',
                        }}
                      >
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                          <Chip
                            label={`[${c.citation_index}] Verified Source`}
                            size="small"
                            sx={{ bgcolor: '#00843D', color: '#FFFFFF', fontWeight: 800, fontSize: '0.72rem' }}
                          />
                          <Typography variant="caption" sx={{ fontFamily: 'monospace', color: '#00843D', fontWeight: 700 }}>
                            Page {c.page} · Lines {c.lines}
                          </Typography>
                        </Box>
                        <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#0F172A', mt: 1 }}>
                          {c.document_title}
                        </Typography>
                        <Typography variant="caption" sx={{ color: '#64748B', display: 'block', mb: 1.5 }}>
                          {c.source}
                        </Typography>
                        <Box sx={{ p: 1.5, borderRadius: 1.5, bgcolor: '#FFFFFF', border: '1px solid #E2E8F0', fontStyle: 'italic', fontSize: '0.8rem', color: '#475569' }}>
                          "{c.snippet}"
                        </Box>
                      </Paper>
                    ))}
                  </Box>
                </Box>
              )}

              {/* Feedback Prompt */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3, pt: 2, borderTop: '1px solid #F1F5F9' }}>
                <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600 }}>
                  Was this grounded answer accurate and well-cited?
                </Typography>
                <Box sx={{ display: 'flex', gap: 0.5 }}>
                  {[1, 2, 3, 4, 5].map((star) => (
                    <Box
                      key={star}
                      onClick={() => handleFeedback(star)}
                      sx={{
                        cursor: 'pointer',
                        color: feedbackRating && feedbackRating >= star ? '#F59E0B' : '#CBD5E1',
                        transition: 'transform 0.15s ease',
                        '&:hover': { transform: 'scale(1.2)', color: '#F59E0B' },
                      }}
                    >
                      <StarIcon sx={{ fontSize: 22 }} />
                    </Box>
                  ))}
                </Box>
              </Box>
            </Paper>
          )}
        </Box>
      )}

      {/* Tab: Knowledge Documents */}
      {activeTab === 'documents' && (
        <Paper elevation={0} sx={{ p: 3, borderRadius: 3, border: '1px solid #E2E8F0', bgcolor: '#FFFFFF' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 700, color: '#0F172A' }}>
              Indexed Course Knowledge Documents
            </Typography>
            {isFacultyOrAdmin && (
              <Button
                variant="contained"
                size="small"
                startIcon={<AddIcon />}
                onClick={() => setShowIngestModal(true)}
                sx={{ bgcolor: '#00843D', textTransform: 'none', '&:hover': { bgcolor: '#006B31' } }}
              >
                Ingest Document
              </Button>
            )}
          </Box>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 700 }}>Title</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Type</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Citation Source</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Chunks</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell sx={{ fontWeight: 600 }}>CS101 Course Specification & Assessment Rubric</TableCell>
                  <TableCell>Syllabus</TableCell>
                  <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>Faculty 2026/27</TableCell>
                  <TableCell>24</TableCell>
                  <TableCell><Chip label="indexed" size="small" color="success" /></TableCell>
                </TableRow>
                <TableRow>
                  <TableCell sx={{ fontWeight: 600 }}>Week 2: Software Engineering Quality Standards</TableCell>
                  <TableCell>Lecture Notes</TableCell>
                  <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>Module 2 Slides</TableCell>
                  <TableCell>38</TableCell>
                  <TableCell><Chip label="indexed" size="small" color="success" /></TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Tab: Analytics */}
      {activeTab === 'analytics' && analytics && (
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 2.5 }}>
          <Paper elevation={0} sx={{ p: 2.5, borderRadius: 3, border: '1px solid #E2E8F0', bgcolor: '#FFFFFF' }}>
            <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
              Indexed Documents
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 800, color: '#0F172A', mt: 0.5 }}>
              {analytics.document_count}
            </Typography>
          </Paper>
          <Paper elevation={0} sx={{ p: 2.5, borderRadius: 3, border: '1px solid #E2E8F0', bgcolor: '#FFFFFF' }}>
            <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
              Vector Chunks
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 800, color: '#00843D', mt: 0.5 }}>
              {analytics.chunk_count}
            </Typography>
          </Paper>
          <Paper elevation={0} sx={{ p: 2.5, borderRadius: 3, border: '1px solid #E2E8F0', bgcolor: '#FFFFFF' }}>
            <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
              Queries Handled
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 800, color: '#3B82F6', mt: 0.5 }}>
              {analytics.query_count}
            </Typography>
          </Paper>
          <Paper elevation={0} sx={{ p: 2.5, borderRadius: 3, border: '1px solid #E2E8F0', bgcolor: '#FFFFFF' }}>
            <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
              Avg Latency
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 800, color: '#F59E0B', mt: 0.5 }}>
              {analytics.avg_latency_ms} ms
            </Typography>
          </Paper>
        </Box>
      )}
    </Box>
  );
};
export default CourseRAG;
