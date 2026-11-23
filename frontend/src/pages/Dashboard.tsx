import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Chip,
  LinearProgress,
  Avatar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Divider,
} from '@mui/material'
import SchoolOutlinedIcon from '@mui/icons-material/SchoolOutlined'
import AssessmentOutlinedIcon from '@mui/icons-material/AssessmentOutlined'
import AssignmentOutlinedIcon from '@mui/icons-material/AssignmentOutlined'
import HowToRegOutlinedIcon from '@mui/icons-material/HowToRegOutlined'
import LocalLibraryOutlinedIcon from '@mui/icons-material/LocalLibraryOutlined'
import MilitaryTechOutlinedIcon from '@mui/icons-material/MilitaryTechOutlined'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import ArrowForwardIcon from '@mui/icons-material/ArrowForward'
import CalendarMonthOutlinedIcon from '@mui/icons-material/CalendarMonthOutlined'
import VideoCameraFrontOutlinedIcon from '@mui/icons-material/VideoCameraFrontOutlined'
import WarningAmberOutlinedIcon from '@mui/icons-material/WarningAmberOutlined'
import AccessTimeOutlinedIcon from '@mui/icons-material/AccessTimeOutlined'
import LocationOnOutlinedIcon from '@mui/icons-material/LocationOnOutlined'
import SportsSoccerOutlinedIcon from '@mui/icons-material/SportsSoccerOutlined'
import PeopleAltOutlinedIcon from '@mui/icons-material/PeopleAltOutlined'
import HubOutlinedIcon from '@mui/icons-material/HubOutlined'
import MenuBookOutlinedIcon from '@mui/icons-material/MenuBookOutlined'
import FactCheckOutlinedIcon from '@mui/icons-material/FactCheckOutlined'
import RecordVoiceOverOutlinedIcon from '@mui/icons-material/RecordVoiceOverOutlined'
import HandshakeOutlinedIcon from '@mui/icons-material/HandshakeOutlined'
import { useAuth } from '@/contexts/AuthContext'
import api from '@/api/client'
import type { StudentDashboard, LecturerDashboard, AdminDashboard, PersonalizedStudentDashboard } from '@/types'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'

// ── Helpers ────────────────────────────────────────────────────

const letterClass = (l: string | null) =>
  !l ? 'badge-warning' : l.startsWith('A') ? 'badge-success' : l.startsWith('B') ? 'badge-info' : l === 'F' ? 'badge-danger' : 'badge-warning'

// ── Modern KPI Stat Card ───────────────────────────────────────

function KpiCard({
  icon,
  value,
  label,
  color,
  bg,
  sublabel,
}: {
  icon: React.ReactNode
  value: string | number
  label: string
  color: string
  bg: string
  sublabel?: string
}) {
  return (
    <Card
      sx={{
        p: 2.5,
        borderRadius: 3.5,
        border: '1px solid #E2E8F0',
        backgroundColor: '#FFFFFF',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.02)',
        transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        '&:hover': {
          transform: 'translateY(-2px)',
          borderColor: '#CBD5E1',
          boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.06), 0 8px 10px -6px rgba(0, 0, 0, 0.04)',
        },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box
          sx={{
            width: 44,
            height: 44,
            borderRadius: 2.5,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: bg,
            color: color,
          }}
        >
          {icon}
        </Box>
        {sublabel && (
          <Chip
            label={sublabel}
            size="small"
            sx={{
              height: 20,
              fontSize: '0.65rem',
              fontWeight: 700,
              bgcolor: '#F1F5F9',
              color: '#475569',
              borderRadius: 1.5,
            }}
          />
        )}
      </Box>
      <Box>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 800,
            fontSize: '1.75rem',
            fontFamily: "'Outfit', sans-serif",
            color: '#0F172A',
            letterSpacing: '-0.02em',
            lineHeight: 1.15,
          }}
        >
          {value}
        </Typography>
        <Typography variant="body2" sx={{ color: '#64748B', fontWeight: 600, mt: 0.5, fontSize: '0.825rem' }}>
          {label}
        </Typography>
      </Box>
    </Card>
  )
}

// ── Student Dashboard ──────────────────────────────────────────

function StudentDash() {
  const [data, setData] = useState<StudentDashboard | null>(null)
  const [personalized, setPersonalized] = useState<PersonalizedStudentDashboard | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.get<StudentDashboard>('/students/dashboard').then((r) => setData(r.data))
    api
      .get<PersonalizedStudentDashboard>('/students/dashboard/personalized')
      .then((r) => setPersonalized(r.data))
      .catch(() => console.info('Personalized dashboard fallback.'))
  }, [])

  if (!data) return <LoadingSpinner message="Loading your student portal..." />

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good Morning' : hour < 17 ? 'Good Afternoon' : 'Good Evening'
  const attOk = data.attendance_rate >= 80

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3.5 }} className="fade-in">
      {/* Editorial Hero Banner */}
      <Card
        sx={{
          p: { xs: 3, md: 4.5 },
          borderRadius: 4,
          background: 'linear-gradient(135deg, #064E3B 0%, #00843D 60%, #059669 100%)',
          color: '#FFFFFF',
          position: 'relative',
          overflow: 'hidden',
          boxShadow: '0 4px 20px rgba(0, 132, 61, 0.25)',
        }}
      >
        <Box
          sx={{
            position: 'absolute',
            width: 350,
            height: 350,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%)',
            top: -100,
            right: -50,
            pointerEvents: 'none',
          }}
        />

        <Box sx={{ position: 'relative', zIndex: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 1.5 }}>
            <Chip
              label="STUDENT PORTAL"
              size="small"
              sx={{
                bgcolor: 'rgba(255, 255, 255, 0.16)',
                backdropFilter: 'blur(8px)',
                color: '#FFFFFF',
                fontWeight: 800,
                fontSize: '0.68rem',
                letterSpacing: '0.08em',
                borderRadius: 1.5,
              }}
            />
            <Chip
              label={`ID: ${data.student_id}`}
              size="small"
              sx={{
                bgcolor: 'rgba(255, 255, 255, 0.12)',
                color: '#FCD34D',
                fontWeight: 700,
                fontSize: '0.68rem',
                borderRadius: 1.5,
              }}
            />
          </Box>

          <Typography
            variant="h3"
            sx={{
              fontFamily: "'Outfit', sans-serif",
              fontWeight: 800,
              fontSize: { xs: '1.75rem', md: '2.3rem' },
              lineHeight: 1.2,
              mb: 1,
              letterSpacing: '-0.02em',
            }}
          >
            {greeting}, {data.full_name.split(' ')[0]}! 👋
          </Typography>

          <Typography
            variant="body1"
            sx={{
              color: 'rgba(255, 255, 255, 0.88)',
              fontSize: '0.975rem',
              maxWidth: 680,
              lineHeight: 1.6,
              mb: 3,
            }}
          >
            {data.program} • Year {data.year_of_study}, Semester {data.semester} • {data.faculty}
          </Typography>

          <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              size="small"
              onClick={() => navigate('/timetable')}
              sx={{
                bgcolor: '#FFFFFF',
                color: '#064E3B',
                fontWeight: 700,
                borderRadius: 2.5,
                px: 2.2,
                py: 0.9,
                '&:hover': {
                  bgcolor: '#F1F5F9',
                },
              }}
            >
              View Timetable
            </Button>
            <Button
              variant="outlined"
              size="small"
              startIcon={<AutoAwesomeIcon sx={{ color: '#FCD34D' }} />}
              onClick={() => navigate('/ai-tutor')}
              sx={{
                borderColor: 'rgba(255, 255, 255, 0.35)',
                color: '#FFFFFF',
                fontWeight: 700,
                borderRadius: 2.5,
                px: 2.2,
                py: 0.9,
                '&:hover': {
                  borderColor: '#FFFFFF',
                  bgcolor: 'rgba(255, 255, 255, 0.1)',
                },
              }}
            >
              Launch Socratic Tutor
            </Button>
          </Box>
        </Box>
      </Card>

      {/* KPI Stats Grid */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 2 }}>
        <KpiCard
          icon={<SchoolOutlinedIcon fontSize="medium" />}
          value={data.enrolled_courses}
          label="Active Courses"
          color="#00843D"
          bg="rgba(0, 132, 61, 0.08)"
          sublabel="Enrolled"
        />
        <KpiCard
          icon={<AssessmentOutlinedIcon fontSize="medium" />}
          value={data.gpa.toFixed(2)}
          label="Cumulative GPA"
          color="#2563EB"
          bg="rgba(37, 99, 235, 0.08)"
          sublabel="Out of 4.00"
        />
        <KpiCard
          icon={<AssignmentOutlinedIcon fontSize="medium" />}
          value={data.pending_assignments}
          label="Pending Tasks"
          color="#D97706"
          bg="rgba(217, 119, 6, 0.08)"
          sublabel="Action Req."
        />
        <KpiCard
          icon={<HowToRegOutlinedIcon fontSize="medium" />}
          value={`${data.attendance_rate}%`}
          label="Attendance Rate"
          color={attOk ? '#059669' : '#DC2626'}
          bg={attOk ? 'rgba(5, 150, 105, 0.08)' : 'rgba(220, 38, 38, 0.08)'}
          sublabel={attOk ? 'Good Standing' : 'Below 80%'}
        />
        <KpiCard
          icon={<LocalLibraryOutlinedIcon fontSize="medium" />}
          value={data.borrowed_books}
          label="Library Loans"
          color="#7C3AED"
          bg="rgba(124, 58, 237, 0.08)"
          sublabel="Active"
        />
        <KpiCard
          icon={<MilitaryTechOutlinedIcon fontSize="medium" />}
          value={data.credits_earned}
          label="Credits Earned"
          color="#0F172A"
          bg="rgba(15, 23, 42, 0.06)"
          sublabel="Accumulated"
        />
      </Box>

      {/* Personalized AI Recommendations */}
      {personalized?.recommendations && personalized.recommendations.length > 0 && (
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1.75 }}>
            <AutoAwesomeIcon sx={{ color: '#00843D', fontSize: '1.25rem' }} />
            <Typography variant="h6" sx={{ fontWeight: 800, fontFamily: "'Outfit', sans-serif" }}>
              AI Personalized Academic Advising
            </Typography>
          </Box>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
            {personalized.recommendations.map((rec) => (
              <Card
                key={rec.id}
                sx={{
                  p: 2.5,
                  borderRadius: 3,
                  borderLeft:
                    rec.priority === 'high'
                      ? '4px solid #DC2626'
                      : rec.priority === 'medium'
                      ? '4px solid #D97706'
                      : '4px solid #059669',
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, fontSize: '0.925rem', color: '#0F172A' }}>
                    {rec.title}
                  </Typography>
                  <Chip
                    label={rec.priority.toUpperCase()}
                    size="small"
                    sx={{
                      height: 20,
                      fontSize: '0.65rem',
                      fontWeight: 800,
                      bgcolor:
                        rec.priority === 'high'
                          ? 'rgba(220, 38, 38, 0.1)'
                          : rec.priority === 'medium'
                          ? 'rgba(217, 119, 6, 0.1)'
                          : 'rgba(5, 150, 105, 0.1)',
                      color:
                        rec.priority === 'high'
                          ? '#DC2626'
                          : rec.priority === 'medium'
                          ? '#D97706'
                          : '#059669',
                      borderRadius: 1,
                    }}
                  />
                </Box>
                <Typography variant="body2" sx={{ color: '#64748B', fontSize: '0.825rem', mb: 2, lineHeight: 1.5 }}>
                  {rec.description}
                </Typography>
                <Button
                  size="small"
                  variant="outlined"
                  color="primary"
                  onClick={() => navigate(rec.action_link)}
                  endIcon={<ArrowForwardIcon fontSize="small" />}
                  sx={{ borderRadius: 2, py: 0.5, px: 1.5, fontSize: '0.78rem' }}
                >
                  {rec.action_label}
                </Button>
              </Card>
            ))}
          </Box>
        </Box>
      )}

      {/* Course Progress Breakdown */}
      {personalized?.courses_progress && personalized.courses_progress.length > 0 && (
        <Card sx={{ p: 3, borderRadius: 3.5 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2.5 }}>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 800, fontFamily: "'Outfit', sans-serif" }}>
                Active Course Progress
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748B' }}>
                Lesson completions and standing for the active term
              </Typography>
            </Box>
            <Button size="small" onClick={() => navigate('/courses')} endIcon={<ArrowForwardIcon />}>
              All Courses
            </Button>
          </Box>

          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
            {personalized.courses_progress.map((cp) => (
              <Box
                key={cp.course_id}
                sx={{
                  p: 2,
                  borderRadius: 2.5,
                  backgroundColor: '#F8FAFC',
                  border: '1px solid #E2E8F0',
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.75 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, fontSize: '0.88rem' }}>
                    {cp.course_code}: {cp.course_title}
                  </Typography>
                  {cp.letter_grade && (
                    <Chip
                      label={cp.letter_grade}
                      size="small"
                      sx={{
                        height: 20,
                        fontSize: '0.7rem',
                        fontWeight: 800,
                        bgcolor: 'rgba(0, 132, 61, 0.1)',
                        color: '#00843D',
                        borderRadius: 1,
                      }}
                    />
                  )}
                </Box>
                <Typography variant="caption" sx={{ color: '#64748B', display: 'block', mb: 1.25 }}>
                  Lecturer: {cp.lecturer_name} • Attendance: {cp.attendance_rate}%
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#64748B', mb: 0.5 }}>
                  <span>Lesson Completion</span>
                  <span>{cp.completed_lessons} / {cp.total_lessons} ({cp.progress_percentage}%)</span>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={cp.progress_percentage}
                  sx={{
                    height: 6,
                    borderRadius: 3,
                    bgcolor: '#E2E8F0',
                    '& .MuiLinearProgress-bar': { bgcolor: '#00843D', borderRadius: 3 },
                  }}
                />
              </Box>
            ))}
          </Box>
        </Card>
      )}

      {/* Two Column Grid: Deadlines & Virtual Classes */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, gap: 3 }}>
        {/* Deadlines Card */}
        <Card sx={{ p: 3, borderRadius: 3.5 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 800, fontFamily: "'Outfit', sans-serif" }}>
                Upcoming Deadlines
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748B' }}>
                Assignments and timed academic quizzes
              </Typography>
            </Box>
            <Button size="small" onClick={() => navigate('/assignments')}>
              View All
            </Button>
          </Box>

          {personalized?.upcoming_deadlines && personalized.upcoming_deadlines.length > 0 ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              {personalized.upcoming_deadlines.slice(0, 4).map((d) => (
                <Box
                  key={`${d.item_type}-${d.id}`}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    p: 1.5,
                    borderRadius: 2,
                    backgroundColor: '#F8FAFC',
                    border: '1px solid #E2E8F0',
                  }}
                >
                  <Box>
                    <Typography variant="subtitle2" sx={{ fontWeight: 700, fontSize: '0.85rem' }}>
                      {d.title}
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.25 }}>
                      <AccessTimeOutlinedIcon sx={{ fontSize: '0.85rem', color: '#94A3B8' }} />
                      <Typography variant="caption" sx={{ color: '#64748B' }}>
                        {d.course_code} • Due {new Date(d.due_date).toLocaleDateString()}
                      </Typography>
                    </Box>
                  </Box>
                  <Chip
                    label={d.submission_status.toUpperCase()}
                    size="small"
                    sx={{
                      height: 20,
                      fontSize: '0.65rem',
                      fontWeight: 800,
                      bgcolor:
                        d.submission_status === 'submitted' || d.submission_status === 'graded'
                          ? 'rgba(5, 150, 105, 0.1)'
                          : d.is_overdue
                          ? 'rgba(220, 38, 38, 0.1)'
                          : 'rgba(217, 119, 6, 0.1)',
                      color:
                        d.submission_status === 'submitted' || d.submission_status === 'graded'
                          ? '#059669'
                          : d.is_overdue
                          ? '#DC2626'
                          : '#D97706',
                      borderRadius: 1,
                    }}
                  />
                </Box>
              ))}
            </Box>
          ) : (
            <Typography variant="body2" sx={{ color: '#94A3B8', textAlign: 'center', py: 3 }}>
              No impending deadlines for this period.
            </Typography>
          )}
        </Card>

        {/* Virtual Classrooms */}
        <Card sx={{ p: 3, borderRadius: 3.5 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 800, fontFamily: "'Outfit', sans-serif" }}>
                Virtual Classrooms
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748B' }}>
                Live video lectures & scheduled sessions
              </Typography>
            </Box>
          </Box>

          {personalized?.upcoming_classes && personalized.upcoming_classes.length > 0 ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              {personalized.upcoming_classes.slice(0, 4).map((s) => (
                <Box
                  key={s.session_id}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    p: 1.5,
                    borderRadius: 2,
                    backgroundColor: '#F8FAFC',
                    border: '1px solid #E2E8F0',
                  }}
                >
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {s.is_live && (
                        <Chip
                          label="LIVE"
                          size="small"
                          sx={{
                            height: 18,
                            fontSize: '0.6rem',
                            fontWeight: 800,
                            bgcolor: '#DC2626',
                            color: '#FFFFFF',
                            borderRadius: 1,
                          }}
                        />
                      )}
                      <Typography variant="subtitle2" sx={{ fontWeight: 700, fontSize: '0.85rem' }}>
                        {s.title}
                      </Typography>
                    </Box>
                    <Typography variant="caption" sx={{ color: '#64748B', display: 'block', mt: 0.25 }}>
                      {s.course_code} • {new Date(s.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ({s.duration_minutes}m)
                    </Typography>
                  </Box>
                  {s.join_url ? (
                    <Button
                      size="small"
                      variant="contained"
                      color="primary"
                      href={s.join_url}
                      target="_blank"
                      startIcon={<VideoCameraFrontOutlinedIcon fontSize="small" />}
                      sx={{ borderRadius: 2, py: 0.5, px: 1.5, fontSize: '0.78rem' }}
                    >
                      Join
                    </Button>
                  ) : (
                    <Chip label={s.session_type} size="small" sx={{ borderRadius: 1.5 }} />
                  )}
                </Box>
              ))}
            </Box>
          ) : (
            <Typography variant="body2" sx={{ color: '#94A3B8', textAlign: 'center', py: 3 }}>
              No virtual classroom sessions today.
            </Typography>
          )}
        </Card>
      </Box>

      {/* Recent Grades & Upcoming Campus Events */}
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', lg: '1fr 1fr' }, gap: 3 }}>
        {/* Recent Grades */}
        <Card sx={{ p: 3, borderRadius: 3.5 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 800, fontFamily: "'Outfit', sans-serif" }}>
                Recent Examination Results
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748B' }}>
                Verified modular assessments and grades
              </Typography>
            </Box>
            <Button size="small" onClick={() => navigate('/grades')}>
              Full Transcript
            </Button>
          </Box>

          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Course</TableCell>
                  <TableCell align="center">Score</TableCell>
                  <TableCell align="right">Grade</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.recent_grades.map((g, i) => (
                  <TableRow key={i} hover>
                    <TableCell>
                      <Typography variant="subtitle2" sx={{ fontWeight: 700, fontSize: '0.85rem' }}>
                        {g.course}
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#64748B' }}>
                        {g.course_code}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {g.total ? `${g.total.toFixed(1)}%` : '—'}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Chip
                        label={g.letter || '—'}
                        size="small"
                        sx={{
                          height: 22,
                          fontWeight: 800,
                          fontSize: '0.72rem',
                          borderRadius: 1.5,
                          bgcolor: g.letter?.startsWith('A')
                            ? 'rgba(0, 132, 61, 0.1)'
                            : g.letter?.startsWith('B')
                            ? 'rgba(37, 99, 235, 0.1)'
                            : 'rgba(217, 119, 6, 0.1)',
                          color: g.letter?.startsWith('A')
                            ? '#00843D'
                            : g.letter?.startsWith('B')
                            ? '#2563EB'
                            : '#D97706',
                        }}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Card>

        {/* Campus Events */}
        <Card sx={{ p: 3, borderRadius: 3.5 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 800, fontFamily: "'Outfit', sans-serif" }}>
                Campus Calendar & Events
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748B' }}>
                Sports, clubs, and university milestones
              </Typography>
            </Box>
            <Button size="small" onClick={() => navigate('/sports')}>
              View All
            </Button>
          </Box>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
            {data.upcoming_events.length ? (
              data.upcoming_events.map((e, i) => {
                const d = new Date(e.date)
                return (
                  <Box
                    key={i}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 2,
                      p: 1.5,
                      borderRadius: 2.5,
                      backgroundColor: '#F8FAFC',
                      border: '1px solid #E2E8F0',
                    }}
                  >
                    <Box
                      sx={{
                        width: 48,
                        height: 48,
                        borderRadius: 2,
                        background: 'linear-gradient(135deg, #00843D 0%, #059669 100%)',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#FFFFFF',
                        flexShrink: 0,
                      }}
                    >
                      <Typography sx={{ fontSize: '1.1rem', fontWeight: 800, lineHeight: 1 }}>
                        {d.getDate()}
                      </Typography>
                      <Typography sx={{ fontSize: '0.6rem', fontWeight: 700, textTransform: 'uppercase', opacity: 0.9 }}>
                        {d.toLocaleString('default', { month: 'short' })}
                      </Typography>
                    </Box>
                    <Box sx={{ minWidth: 0, flex: 1 }}>
                      <Typography variant="subtitle2" sx={{ fontWeight: 700, fontSize: '0.85rem' }}>
                        {e.title}
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.25 }}>
                        <LocationOnOutlinedIcon sx={{ fontSize: '0.85rem', color: '#94A3B8' }} />
                        <Typography variant="caption" sx={{ color: '#64748B' }}>
                          {e.location || 'NSBM Green Campus'}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                )
              })
            ) : (
              <Typography variant="body2" sx={{ color: '#94A3B8', textAlign: 'center', py: 3 }}>
                No upcoming events recorded.
              </Typography>
            )}
          </Box>
        </Card>
      </Box>
    </Box>
  )
}

// ── Lecturer Dashboard ─────────────────────────────────────────

function LecturerDash() {
  const [data, setData] = useState<LecturerDashboard | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.get<LecturerDashboard>('/lecturers/dashboard').then((r) => setData(r.data))
  }, [])

  if (!data) return <LoadingSpinner message="Loading lecturer command hub..." />

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3.5 }} className="fade-in">
      <Card
        sx={{
          p: { xs: 3, md: 4 },
          borderRadius: 4,
          background: 'linear-gradient(135deg, #064E3B 0%, #00843D 100%)',
          color: '#FFFFFF',
        }}
      >
        <Chip
          label="FACULTY PORTAL"
          size="small"
          sx={{
            bgcolor: 'rgba(255, 255, 255, 0.2)',
            color: '#FFFFFF',
            fontWeight: 800,
            fontSize: '0.68rem',
            mb: 1.5,
          }}
        />
        <Typography variant="h4" sx={{ fontFamily: "'Outfit', sans-serif", fontWeight: 800, mb: 1 }}>
          Welcome back, {data.full_name.split(' ')[0]}! 👨‍🏫
        </Typography>
        <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.85)' }}>
          {data.department} • {data.faculty} {data.office_location ? `• Office: ${data.office_location}` : ''}
        </Typography>
      </Card>

      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 2 }}>
        <KpiCard
          icon={<MenuBookOutlinedIcon fontSize="medium" />}
          value={data.total_courses}
          label="Allocated Courses"
          color="#00843D"
          bg="rgba(0, 132, 61, 0.08)"
          sublabel="Active"
        />
        <KpiCard
          icon={<PeopleAltOutlinedIcon fontSize="medium" />}
          value={data.total_students}
          label="Total Students"
          color="#2563EB"
          bg="rgba(37, 99, 235, 0.08)"
          sublabel="Enrolled"
        />
        <KpiCard
          icon={<FactCheckOutlinedIcon fontSize="medium" />}
          value={data.pending_submissions}
          label="Submissions to Grade"
          color="#D97706"
          bg="rgba(217, 119, 6, 0.08)"
          sublabel="Review Needed"
        />
      </Box>

      <Card sx={{ p: 3, borderRadius: 3.5 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 800, fontFamily: "'Outfit', sans-serif" }}>
              Recent Student Submissions
            </Typography>
            <Typography variant="caption" sx={{ color: '#64748B' }}>
              Pending and recently reviewed assignment submissions
            </Typography>
          </Box>
          <Button variant="contained" size="small" onClick={() => navigate('/grading')}>
            Open Grading Suite
          </Button>
        </Box>

        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Student</TableCell>
                <TableCell>Assignment</TableCell>
                <TableCell>Course</TableCell>
                <TableCell>Submitted At</TableCell>
                <TableCell align="right">Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.recent_submissions.map((s, i) => (
                <TableRow key={i} hover>
                  <TableCell sx={{ fontWeight: 700 }}>{s.student}</TableCell>
                  <TableCell>{s.assignment}</TableCell>
                  <TableCell>
                    <Chip label={s.course} size="small" sx={{ borderRadius: 1 }} />
                  </TableCell>
                  <TableCell sx={{ color: '#64748B' }}>
                    {new Date(s.submitted_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell align="right">
                    <Chip
                      label={s.graded ? 'GRADED' : 'PENDING'}
                      size="small"
                      sx={{
                        fontWeight: 800,
                        fontSize: '0.65rem',
                        borderRadius: 1,
                        bgcolor: s.graded ? 'rgba(5, 150, 105, 0.1)' : 'rgba(217, 119, 6, 0.1)',
                        color: s.graded ? '#059669' : '#D97706',
                      }}
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>
    </Box>
  )
}

// ── Admin Dashboard ────────────────────────────────────────────

function AdminDash() {
  const [data, setData] = useState<AdminDashboard | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.get<AdminDashboard>('/admin/dashboard').then((r) => setData(r.data))
  }, [])

  if (!data) return <LoadingSpinner message="Loading university system analytics..." />

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3.5 }} className="fade-in">
      <Card
        sx={{
          p: { xs: 3, md: 4 },
          borderRadius: 4,
          background: 'linear-gradient(135deg, #0F172A 0%, #1E293B 100%)',
          color: '#FFFFFF',
        }}
      >
        <Chip
          label="ADMIN COMMAND CONSOLE"
          size="small"
          sx={{
            bgcolor: 'rgba(255, 255, 255, 0.15)',
            color: '#FFFFFF',
            fontWeight: 800,
            fontSize: '0.68rem',
            mb: 1.5,
          }}
        />
        <Typography variant="h4" sx={{ fontFamily: "'Outfit', sans-serif", fontWeight: 800, mb: 1 }}>
          System Overview & Operations Command
        </Typography>
        <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.75)' }}>
          NSBM EduSphere University Infrastructure & Governance
        </Typography>
      </Card>

      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 2 }}>
        <KpiCard
          icon={<SchoolOutlinedIcon fontSize="medium" />}
          value={data.total_students}
          label="Enrolled Scholars"
          color="#00843D"
          bg="rgba(0, 132, 61, 0.08)"
          sublabel="Students"
        />
        <KpiCard
          icon={<PeopleAltOutlinedIcon fontSize="medium" />}
          value={data.total_lecturers}
          label="Academic Staff"
          color="#2563EB"
          bg="rgba(37, 99, 235, 0.08)"
          sublabel="Faculty"
        />
        <KpiCard
          icon={<HubOutlinedIcon fontSize="medium" />}
          value={data.total_alumni}
          label="Alumni Members"
          color="#7C3AED"
          bg="rgba(124, 58, 237, 0.08)"
          sublabel="Network"
        />
        <KpiCard
          icon={<MenuBookOutlinedIcon fontSize="medium" />}
          value={data.total_courses}
          label="Curriculum Courses"
          color="#D97706"
          bg="rgba(217, 119, 6, 0.08)"
          sublabel="Active"
        />
        <KpiCard
          icon={<LocalLibraryOutlinedIcon fontSize="medium" />}
          value={data.total_books}
          label="Library Volumes"
          color="#059669"
          bg="rgba(5, 150, 105, 0.08)"
          sublabel="Catalog"
        />
        <KpiCard
          icon={<SportsSoccerOutlinedIcon fontSize="medium" />}
          value={data.total_clubs}
          label="Campus Clubs"
          color="#DC2626"
          bg="rgba(220, 38, 38, 0.08)"
          sublabel="Student Life"
        />
      </Box>

      <Card sx={{ p: 3, borderRadius: 3.5 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 800, fontFamily: "'Outfit', sans-serif" }}>
              Recent University Registrations
            </Typography>
            <Typography variant="caption" sx={{ color: '#64748B' }}>
              Newly provisioned identity records across all faculties
            </Typography>
          </Box>
          <Button size="small" variant="outlined" onClick={() => navigate('/manage-users')}>
            Manage All Users
          </Button>
        </Box>

        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Record ID</TableCell>
                <TableCell>Full Name</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Role</TableCell>
                <TableCell align="right">Joined Date</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data.recent_registrations.map((u) => (
                <TableRow key={u.id} hover>
                  <TableCell sx={{ color: '#64748B' }}>#{u.id}</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>{u.full_name}</TableCell>
                  <TableCell sx={{ color: '#64748B' }}>{u.email}</TableCell>
                  <TableCell>
                    <Chip
                      label={u.role.toUpperCase()}
                      size="small"
                      sx={{
                        fontWeight: 800,
                        fontSize: '0.65rem',
                        borderRadius: 1,
                        bgcolor:
                          u.role === 'admin'
                            ? 'rgba(220, 38, 38, 0.1)'
                            : u.role === 'lecturer'
                            ? 'rgba(37, 99, 235, 0.1)'
                            : 'rgba(0, 132, 61, 0.1)',
                        color:
                          u.role === 'admin'
                            ? '#DC2626'
                            : u.role === 'lecturer'
                            ? '#2563EB'
                            : '#00843D',
                      }}
                    />
                  </TableCell>
                  <TableCell align="right" sx={{ color: '#64748B' }}>
                    {new Date(u.created_at).toLocaleDateString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>
    </Box>
  )
}

// ── Alumni Dashboard ───────────────────────────────────────────

function AlumniDash() {
  const [data, setData] = useState<any>(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/alumni/dashboard').then((r) => setData(r.data))
  }, [])

  if (!data) return <LoadingSpinner message="Loading alumni network..." />

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3.5 }} className="fade-in">
      <Card
        sx={{
          p: { xs: 3, md: 4 },
          borderRadius: 4,
          background: 'linear-gradient(135deg, #064E3B 0%, #00843D 100%)',
          color: '#FFFFFF',
        }}
      >
        <Chip
          label="ALUMNI HUB"
          size="small"
          sx={{
            bgcolor: 'rgba(255, 255, 255, 0.2)',
            color: '#FFFFFF',
            fontWeight: 800,
            fontSize: '0.68rem',
            mb: 1.5,
          }}
        />
        <Typography variant="h4" sx={{ fontFamily: "'Outfit', sans-serif", fontWeight: 800, mb: 1 }}>
          Welcome back, {data.full_name.split(' ')[0]}! 🌟
        </Typography>
        <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.85)' }}>
          {data.degree} • Class of {data.graduation_year}
        </Typography>
      </Card>

      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 2 }}>
        <KpiCard
          icon={<HubOutlinedIcon fontSize="medium" />}
          value={data.total_alumni_network}
          label="Alumni Members"
          color="#00843D"
          bg="rgba(0, 132, 61, 0.08)"
          sublabel="Global"
        />
        <KpiCard
          icon={<RecordVoiceOverOutlinedIcon fontSize="medium" />}
          value={data.my_experiences}
          label="Shared Stories"
          color="#2563EB"
          bg="rgba(37, 99, 235, 0.08)"
          sublabel="Published"
        />
        <KpiCard
          icon={<HandshakeOutlinedIcon fontSize="medium" />}
          value={data.active_mentorships}
          label="Active Mentorships"
          color="#D97706"
          bg="rgba(217, 119, 6, 0.08)"
          sublabel="Mentoring"
        />
      </Box>

      <Card sx={{ p: 3, borderRadius: 3.5 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 800, fontFamily: "'Outfit', sans-serif" }}>
              Featured Alumni Spotlights
            </Typography>
            <Typography variant="caption" sx={{ color: '#64748B' }}>
              Inspiring career journeys and mentorship insights
            </Typography>
          </Box>
          <Button size="small" onClick={() => navigate('/experiences')}>
            View All Stories
          </Button>
        </Box>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
          {data.featured_stories.map((e: any) => (
            <Box
              key={e.id}
              sx={{
                p: 2,
                borderRadius: 2.5,
                backgroundColor: '#F8FAFC',
                border: '1px solid #E2E8F0',
              }}
            >
              <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 0.5 }}>
                {e.title}
              </Typography>
              <Typography variant="caption" sx={{ color: '#64748B' }}>
                ✍️ {e.author} • {e.category} • ❤️ {e.likes} likes
              </Typography>
            </Box>
          ))}
        </Box>
      </Card>
    </Box>
  )
}

// ── Main Export ────────────────────────────────────────────────

export default function Dashboard() {
  const { user } = useAuth()
  if (!user) return null
  if (user.role === 'student') return <StudentDash />
  if (user.role === 'lecturer') return <LecturerDash />
  if (user.role === 'admin') return <AdminDash />
  if (user.role === 'alumni') return <AlumniDash />
  return <StudentDash />
}
