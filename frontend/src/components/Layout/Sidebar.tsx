import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  Drawer,
  Box,
  Typography,
  Avatar,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Chip,
  Divider,
} from '@mui/material'
import DashboardOutlinedIcon from '@mui/icons-material/DashboardOutlined'
import SchoolOutlinedIcon from '@mui/icons-material/SchoolOutlined'
import AssessmentOutlinedIcon from '@mui/icons-material/AssessmentOutlined'
import AssignmentOutlinedIcon from '@mui/icons-material/AssignmentOutlined'
import HowToRegOutlinedIcon from '@mui/icons-material/HowToRegOutlined'
import CalendarMonthOutlinedIcon from '@mui/icons-material/CalendarMonthOutlined'
import RateReviewOutlinedIcon from '@mui/icons-material/RateReviewOutlined'
import VolunteerActivismOutlinedIcon from '@mui/icons-material/VolunteerActivismOutlined'
import AccountBalanceWalletOutlinedIcon from '@mui/icons-material/AccountBalanceWalletOutlined'
import EventNoteOutlinedIcon from '@mui/icons-material/EventNoteOutlined'
import Diversity3OutlinedIcon from '@mui/icons-material/Diversity3Outlined'
import ForumOutlinedIcon from '@mui/icons-material/ForumOutlined'
import AutoAwesomeOutlinedIcon from '@mui/icons-material/AutoAwesomeOutlined'
import FactCheckOutlinedIcon from '@mui/icons-material/FactCheckOutlined'
import TaskAltOutlinedIcon from '@mui/icons-material/TaskAltOutlined'
import InsightsOutlinedIcon from '@mui/icons-material/InsightsOutlined'
import HubOutlinedIcon from '@mui/icons-material/HubOutlined'
import RecordVoiceOverOutlinedIcon from '@mui/icons-material/RecordVoiceOverOutlined'
import HandshakeOutlinedIcon from '@mui/icons-material/HandshakeOutlined'
import TuneOutlinedIcon from '@mui/icons-material/TuneOutlined'
import PeopleAltOutlinedIcon from '@mui/icons-material/PeopleAltOutlined'
import LocalLibraryOutlinedIcon from '@mui/icons-material/LocalLibraryOutlined'
import SportsSoccerOutlinedIcon from '@mui/icons-material/SportsSoccerOutlined'
import NewspaperOutlinedIcon from '@mui/icons-material/NewspaperOutlined'
import ApartmentOutlinedIcon from '@mui/icons-material/ApartmentOutlined'
import DirectionsBusOutlinedIcon from '@mui/icons-material/DirectionsBusOutlined'
import MeetingRoomOutlinedIcon from '@mui/icons-material/MeetingRoomOutlined'
import SmartToyOutlinedIcon from '@mui/icons-material/SmartToyOutlined'
import FindInPageOutlinedIcon from '@mui/icons-material/FindInPageOutlined'
import PsychologyOutlinedIcon from '@mui/icons-material/PsychologyOutlined'
import TerminalOutlinedIcon from '@mui/icons-material/TerminalOutlined'
import NotificationsNoneOutlinedIcon from '@mui/icons-material/NotificationsNoneOutlined'
import PersonOutlineOutlinedIcon from '@mui/icons-material/PersonOutlineOutlined'
import { useAuth } from '@/contexts/AuthContext'

const DRAWER_WIDTH = 270

const initials = (name: string) =>
  name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

interface NavItem {
  to: string
  icon: React.ReactNode
  label: string
  badge?: string
}

function studentNav(): NavItem[] {
  return [
    { to: '/dashboard', icon: <DashboardOutlinedIcon fontSize="small" />, label: 'Dashboard' },
    { to: '/courses', icon: <SchoolOutlinedIcon fontSize="small" />, label: 'My Courses' },
    { to: '/grades', icon: <AssessmentOutlinedIcon fontSize="small" />, label: 'Grades & GPA' },
    { to: '/assignments', icon: <AssignmentOutlinedIcon fontSize="small" />, label: 'Assignments' },
    { to: '/attendance', icon: <HowToRegOutlinedIcon fontSize="small" />, label: 'Attendance' },
    { to: '/timetable', icon: <CalendarMonthOutlinedIcon fontSize="small" />, label: 'Timetable' },
    { to: '/evaluations', icon: <RateReviewOutlinedIcon fontSize="small" />, label: 'Course Feedback' },
    { to: '/wellbeing', icon: <VolunteerActivismOutlinedIcon fontSize="small" />, label: 'Student Wellbeing' },
    { to: '/billing', icon: <AccountBalanceWalletOutlinedIcon fontSize="small" />, label: 'Fees & Billing' },
    { to: '/calendar', icon: <EventNoteOutlinedIcon fontSize="small" />, label: 'Calendar & Tasks' },
    { to: '/collaboration', icon: <Diversity3OutlinedIcon fontSize="small" />, label: 'Study Groups' },
    { to: '/messages', icon: <ForumOutlinedIcon fontSize="small" />, label: 'Messages' },
  ]
}

function lecturerNav(): NavItem[] {
  return [
    { to: '/dashboard', icon: <DashboardOutlinedIcon fontSize="small" />, label: 'Dashboard' },
    { to: '/courses', icon: <SchoolOutlinedIcon fontSize="small" />, label: 'My Courses' },
    { to: '/ai-quiz-generator', icon: <AutoAwesomeOutlinedIcon fontSize="small" />, label: 'Quiz Generator' },
    { to: '/ai-grading', icon: <FactCheckOutlinedIcon fontSize="small" />, label: 'AI Grading' },
    { to: '/grading', icon: <TaskAltOutlinedIcon fontSize="small" />, label: 'Submissions' },
    { to: '/analytics', icon: <InsightsOutlinedIcon fontSize="small" />, label: 'Analytics' },
    { to: '/calendar', icon: <EventNoteOutlinedIcon fontSize="small" />, label: 'Calendar & Tasks' },
    { to: '/messages', icon: <ForumOutlinedIcon fontSize="small" />, label: 'Messages' },
  ]
}

function alumniNav(): NavItem[] {
  return [
    { to: '/dashboard', icon: <DashboardOutlinedIcon fontSize="small" />, label: 'Alumni Hub' },
    { to: '/alumni-network', icon: <HubOutlinedIcon fontSize="small" />, label: 'Network' },
    { to: '/experiences', icon: <RecordVoiceOverOutlinedIcon fontSize="small" />, label: 'Experiences' },
    { to: '/mentorship', icon: <HandshakeOutlinedIcon fontSize="small" />, label: 'Mentorship' },
  ]
}

function adminNav(): NavItem[] {
  return [
    { to: '/dashboard', icon: <DashboardOutlinedIcon fontSize="small" />, label: 'Dashboard' },
    { to: '/campus-operations', icon: <TuneOutlinedIcon fontSize="small" />, label: 'Operations Command' },
    { to: '/manage-users', icon: <PeopleAltOutlinedIcon fontSize="small" />, label: 'Users & Roles' },
    { to: '/manage-courses', icon: <SchoolOutlinedIcon fontSize="small" />, label: 'Course Catalog' },
    { to: '/billing', icon: <AccountBalanceWalletOutlinedIcon fontSize="small" />, label: 'Fees & Billing' },
  ]
}

interface SidebarProps {
  isOpen: boolean
  onClose?: () => void
  variant?: 'permanent' | 'temporary'
}

export default function Sidebar({ isOpen, onClose, variant = 'permanent' }: SidebarProps) {
  const { user } = useAuth()
  if (!user) return null

  const portalNav: Record<string, NavItem[]> = {
    student: studentNav(),
    lecturer: lecturerNav(),
    alumni: alumniNav(),
    admin: adminNav(),
  }

  const campus: NavItem[] = [
    { to: '/library', icon: <LocalLibraryOutlinedIcon fontSize="small" />, label: 'Library & E-Resources' },
    { to: '/sports', icon: <SportsSoccerOutlinedIcon fontSize="small" />, label: 'Sports & Clubs' },
    { to: '/news', icon: <NewspaperOutlinedIcon fontSize="small" />, label: 'Campus News' },
    { to: '/hostels', icon: <ApartmentOutlinedIcon fontSize="small" />, label: 'Hostel & Housing' },
    { to: '/transport', icon: <DirectionsBusOutlinedIcon fontSize="small" />, label: 'Transport & Shuttles' },
    { to: '/facilities', icon: <MeetingRoomOutlinedIcon fontSize="small" />, label: 'Facility Booking' },
    { to: '/alumni-network', icon: <HubOutlinedIcon fontSize="small" />, label: 'Alumni Network' },
  ]

  const account: NavItem[] = [
    { to: '/ai-chat', icon: <SmartToyOutlinedIcon fontSize="small" />, label: 'AI Assistant', badge: 'PRO' },
    { to: '/course-rag', icon: <FindInPageOutlinedIcon fontSize="small" />, label: 'Course RAG', badge: 'RAG' },
    { to: '/ai-tutor', icon: <PsychologyOutlinedIcon fontSize="small" />, label: 'Socratic Tutor', badge: 'Tutor' },
    { to: '/mcp-console', icon: <TerminalOutlinedIcon fontSize="small" />, label: 'MCP Dev Console', badge: 'MCP' },
    { to: '/notifications', icon: <NotificationsNoneOutlinedIcon fontSize="small" />, label: 'Notifications' },
    { to: '/profile', icon: <PersonOutlineOutlinedIcon fontSize="small" />, label: 'My Profile' },
  ]

  const roleLabel: Record<string, string> = {
    student: 'Student Portal',
    lecturer: 'Faculty Portal',
    alumni: 'Alumni Portal',
    admin: 'Command Admin',
    librarian: 'Library Staff',
  }

  const drawerContent = (
    <Box
      sx={{
        width: DRAWER_WIDTH,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#FFFFFF',
        pt: '64px',
        px: 2,
        pb: 3,
        overflowY: 'auto',
      }}
    >
      {/* User Information Card */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          p: 1.75,
          mt: 2,
          mb: 2.5,
          borderRadius: 3,
          backgroundColor: '#F8FAFC',
          border: '1px solid #E2E8F0',
          boxShadow: '0 1px 2px rgba(0,0,0,0.02)',
        }}
      >
        <Avatar
          sx={{
            width: 42,
            height: 42,
            fontSize: '0.9rem',
            fontWeight: 800,
            bgcolor: 'rgba(0, 132, 61, 0.1)',
            color: '#00843D',
            border: '1.5px solid rgba(0, 132, 61, 0.25)',
          }}
        >
          {initials(user.full_name)}
        </Avatar>
        <Box sx={{ minWidth: 0, flex: 1 }}>
          <Typography
            variant="subtitle2"
            noWrap
            sx={{ fontWeight: 700, fontSize: '0.875rem', color: '#0F172A', lineHeight: 1.25 }}
          >
            {user.full_name}
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color: '#00843D',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              fontSize: '0.66rem',
              display: 'block',
              mt: 0.25,
            }}
          >
            {roleLabel[user.role] || user.role}
          </Typography>
        </Box>
      </Box>

      {/* Main Portal Section */}
      {portalNav[user.role] && (
        <Box sx={{ mb: 2.5 }}>
          <Typography
            variant="overline"
            sx={{
              px: 1.5,
              fontWeight: 800,
              color: '#94A3B8',
              letterSpacing: '0.08em',
              fontSize: '0.68rem',
              display: 'block',
              mb: 0.75,
            }}
          >
            Academic Portal
          </Typography>
          <List disablePadding>
            {portalNav[user.role].map((item) => (
              <ListItemButton
                key={item.to}
                component={NavLink}
                to={item.to}
                end={item.to === '/dashboard'}
                onClick={onClose}
                sx={{
                  borderRadius: 2.5,
                  mb: 0.4,
                  py: 0.85,
                  px: 1.5,
                  color: '#475569',
                  transition: 'all 0.18s ease',
                  '&.active': {
                    backgroundColor: 'rgba(0, 132, 61, 0.08)',
                    color: '#00843D',
                    fontWeight: 700,
                    borderLeft: '3px solid #00843D',
                    '& .MuiListItemIcon-root': {
                      color: '#00843D',
                    },
                  },
                  '&:hover': {
                    backgroundColor: '#F1F5F9',
                    color: '#0F172A',
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 32, color: '#64748B' }}>{item.icon}</ListItemIcon>
                <ListItemText
                  primary={
                    <Typography sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
                      {item.label}
                    </Typography>
                  }
                />
                {item.badge && (
                  <Chip
                    label={item.badge}
                    size="small"
                    sx={{
                      height: 18,
                      fontSize: '0.65rem',
                      fontWeight: 700,
                      bgcolor: '#00843D',
                      color: '#FFFFFF',
                      borderRadius: 1,
                    }}
                  />
                )}
              </ListItemButton>
            ))}
          </List>
        </Box>
      )}

      {/* Campus Life Section */}
      <Box sx={{ mb: 2.5 }}>
        <Typography
          variant="overline"
          sx={{
            px: 1.5,
            fontWeight: 800,
            color: '#94A3B8',
            letterSpacing: '0.08em',
            fontSize: '0.68rem',
            display: 'block',
            mb: 0.75,
          }}
        >
          Campus Ecosystem
        </Typography>
        <List disablePadding>
          {campus.map((item) => (
            <ListItemButton
              key={item.to}
              component={NavLink}
              to={item.to}
              onClick={onClose}
              sx={{
                borderRadius: 2.5,
                mb: 0.4,
                py: 0.85,
                px: 1.5,
                color: '#475569',
                transition: 'all 0.18s ease',
                '&.active': {
                  backgroundColor: 'rgba(0, 132, 61, 0.08)',
                  color: '#00843D',
                  fontWeight: 700,
                  borderLeft: '3px solid #00843D',
                  '& .MuiListItemIcon-root': {
                    color: '#00843D',
                  },
                },
                '&:hover': {
                  backgroundColor: '#F1F5F9',
                  color: '#0F172A',
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 32, color: '#64748B' }}>{item.icon}</ListItemIcon>
              <ListItemText
                primary={
                  <Typography sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
                    {item.label}
                  </Typography>
                }
              />
            </ListItemButton>
          ))}
        </List>
      </Box>

      {/* AI Services Section */}
      <Box sx={{ mb: 2 }}>
        <Typography
          variant="overline"
          sx={{
            px: 1.5,
            fontWeight: 800,
            color: '#94A3B8',
            letterSpacing: '0.08em',
            fontSize: '0.68rem',
            display: 'block',
            mb: 0.75,
          }}
        >
          AI & Services
        </Typography>
        <List disablePadding>
          {account.map((item) => (
            <ListItemButton
              key={item.to}
              component={NavLink}
              to={item.to}
              onClick={onClose}
              sx={{
                borderRadius: 2.5,
                mb: 0.4,
                py: 0.85,
                px: 1.5,
                color: '#475569',
                transition: 'all 0.18s ease',
                '&.active': {
                  backgroundColor: 'rgba(0, 132, 61, 0.08)',
                  color: '#00843D',
                  fontWeight: 700,
                  borderLeft: '3px solid #00843D',
                  '& .MuiListItemIcon-root': {
                    color: '#00843D',
                  },
                },
                '&:hover': {
                  backgroundColor: '#F1F5F9',
                  color: '#0F172A',
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 32, color: '#64748B' }}>{item.icon}</ListItemIcon>
              <ListItemText
                primary={
                  <Typography sx={{ fontSize: '0.85rem', fontWeight: 600 }}>
                    {item.label}
                  </Typography>
                }
              />
              {item.badge && (
                <Chip
                  label={item.badge}
                  size="small"
                  sx={{
                    height: 18,
                    fontSize: '0.65rem',
                    fontWeight: 700,
                    bgcolor: 'rgba(37, 99, 235, 0.1)',
                    color: '#2563EB',
                    borderRadius: 1,
                  }}
                />
              )}
            </ListItemButton>
          ))}
        </List>
      </Box>

      {/* System Status Footer */}
      <Box sx={{ mt: 'auto', pt: 2 }}>
        <Box
          sx={{
            p: 1.75,
            backgroundColor: '#F8FAFC',
            border: '1px solid #E2E8F0',
            borderRadius: 3,
            fontSize: '0.72rem',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.75 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.85 }}>
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  bgcolor: '#10B981',
                  boxShadow: '0 0 0 3px rgba(16, 185, 129, 0.2)',
                  animation: 'pulse 2s infinite',
                }}
              />
              <Typography variant="caption" sx={{ color: '#0F172A', fontWeight: 700, fontSize: '0.72rem' }}>
                EduSphere Cloud
              </Typography>
            </Box>
            <Chip
              label="v1.4"
              size="small"
              sx={{ height: 16, fontSize: '0.62rem', fontWeight: 700, bgcolor: '#E2E8F0', color: '#475569' }}
            />
          </Box>
          <Typography variant="caption" sx={{ color: '#64748B', display: 'block', fontSize: '0.68rem' }}>
            FastAPI + ChromaDB • 99.98% SLA
          </Typography>
        </Box>
      </Box>
    </Box>
  )

  return (
    <Box component="nav" sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}>
      {variant === 'temporary' ? (
        <Drawer
          variant="temporary"
          open={isOpen}
          onClose={onClose}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: DRAWER_WIDTH,
              borderRight: '1px solid #E2E8F0',
            },
          }}
        >
          {drawerContent}
        </Drawer>
      ) : (
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: DRAWER_WIDTH,
              borderRight: '1px solid #E2E8F0',
            },
          }}
          open
        >
          {drawerContent}
        </Drawer>
      )}
    </Box>
  )
}
