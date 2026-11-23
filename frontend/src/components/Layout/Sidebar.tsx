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
import { useAuth } from '@/contexts/AuthContext'

const DRAWER_WIDTH = 260

const initials = (name: string) =>
  name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

interface NavItem {
  to: string
  icon: string
  label: string
  badge?: string
}

function studentNav(): NavItem[] {
  return [
    { to: '/dashboard', icon: '🏠', label: 'Dashboard' },
    { to: '/courses', icon: '📖', label: 'My Courses' },
    { to: '/grades', icon: '📊', label: 'Grades & GPA' },
    { to: '/assignments', icon: '📝', label: 'Assignments' },
    { to: '/attendance', icon: '📅', label: 'Attendance' },
    { to: '/timetable', icon: '⏰', label: 'Timetable' },
    { to: '/evaluations', icon: '⭐', label: 'Course Feedback' },
    { to: '/wellbeing', icon: '💚', label: 'Student Wellbeing' },
    { to: '/billing', icon: '💳', label: 'Fees & Billing' },
    { to: '/calendar', icon: '📆', label: 'Calendar & Tasks' },
    { to: '/collaboration', icon: '👥', label: 'Study Groups' },
    { to: '/messages', icon: '💬', label: 'Messages' },
  ]
}

function lecturerNav(): NavItem[] {
  return [
    { to: '/dashboard', icon: '🏠', label: 'Dashboard' },
    { to: '/courses', icon: '📖', label: 'My Courses' },
    { to: '/ai-quiz-generator', icon: '📝', label: 'Quiz Generator' },
    { to: '/ai-grading', icon: '⚖️', label: 'AI Grading' },
    { to: '/grading', icon: '✅', label: 'Grading' },
    { to: '/analytics', icon: '📈', label: 'Analytics' },
    { to: '/calendar', icon: '📆', label: 'Calendar & Tasks' },
    { to: '/messages', icon: '💬', label: 'Messages' },
  ]
}

function alumniNav(): NavItem[] {
  return [
    { to: '/dashboard', icon: '🏠', label: 'Alumni Hub' },
    { to: '/alumni-network', icon: '🌐', label: 'Network' },
    { to: '/experiences', icon: '💬', label: 'Experiences' },
    { to: '/mentorship', icon: '🤝', label: 'Mentorship' },
  ]
}

function adminNav(): NavItem[] {
  return [
    { to: '/dashboard', icon: '🏠', label: 'Dashboard' },
    { to: '/campus-operations', icon: '🎛️', label: 'Operations Command' },
    { to: '/manage-users', icon: '👥', label: 'Users' },
    { to: '/manage-courses', icon: '📖', label: 'Courses' },
    { to: '/billing', icon: '💳', label: 'Fees & Billing' },
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
    { to: '/library', icon: '📚', label: 'Library' },
    { to: '/sports', icon: '⚽', label: 'Sports & Clubs' },
    { to: '/news', icon: '📰', label: 'News Portal' },
    { to: '/hostels', icon: '🏢', label: 'Hostel & Housing' },
    { to: '/transport', icon: '🚌', label: 'Transport & Shuttles' },
    { to: '/facilities', icon: '🏛️', label: 'Facility Booking' },
    { to: '/alumni-network', icon: '🌐', label: 'Alumni Network' },
  ]

  const account: NavItem[] = [
    { to: '/ai-chat', icon: '🤖', label: 'AI Assistant', badge: 'AI' },
    { to: '/course-rag', icon: '📚', label: 'Course RAG', badge: 'RAG' },
    { to: '/ai-tutor', icon: '🎓', label: 'Socratic Tutor', badge: 'Tutor' },
    { to: '/mcp-console', icon: '⚙️', label: 'MCP Tools', badge: 'MCP' },
    { to: '/ai-quiz-generator', icon: '📝', label: 'AI Quiz Gen', badge: 'Quiz' },
    { to: '/ai-grading', icon: '⚖️', label: 'AI Grading', badge: 'Grade' },
    { to: '/notifications', icon: '🔔', label: 'Notifications' },
    { to: '/profile', icon: '👤', label: 'My Profile' },
  ]

  const roleLabel: Record<string, string> = {
    student: 'Student Portal',
    lecturer: 'Lecturer Portal',
    alumni: 'Alumni Network',
    admin: 'Administrator',
    librarian: 'Librarian',
  }

  const drawerContent = (
    <Box
      sx={{
        width: DRAWER_WIDTH,
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#FFFFFF',
        pt: '70px',
        px: 2,
        pb: 3,
        overflowY: 'auto',
      }}
    >
      {/* Profile Card */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          p: 1.75,
          mt: 1.5,
          mb: 2,
          borderRadius: 3,
          backgroundColor: '#F8FAFC',
          border: '1px solid rgba(0, 0, 0, 0.06)',
        }}
      >
        <Avatar
          sx={{
            width: 44,
            height: 44,
            fontSize: '0.95rem',
            fontWeight: 800,
            bgcolor: 'rgba(0, 132, 61, 0.12)',
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
            sx={{ fontWeight: 700, fontSize: '0.875rem', color: '#1A1A2E' }}
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
              fontSize: '0.65rem',
            }}
          >
            {roleLabel[user.role] || user.role}
          </Typography>
        </Box>
      </Box>

      {/* Portal Navigation */}
      {portalNav[user.role] && (
        <Box sx={{ mb: 2 }}>
          <Typography
            variant="overline"
            sx={{
              px: 1.5,
              fontWeight: 800,
              color: 'text.secondary',
              letterSpacing: '0.08em',
              display: 'block',
              mb: 0.5,
            }}
          >
            Portal
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
                  mb: 0.5,
                  py: 1,
                  px: 1.5,
                  color: '#475569',
                  '&.active': {
                    backgroundColor: 'rgba(0, 132, 61, 0.1)',
                    color: '#00843D',
                    fontWeight: 700,
                    '& .MuiListItemIcon-root': {
                      transform: 'scale(1.1)',
                    },
                  },
                  '&:hover': {
                    backgroundColor: 'rgba(0, 0, 0, 0.04)',
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 32, fontSize: '1.15rem' }}>{item.icon}</ListItemIcon>
                <ListItemText
                  primary={
                    <Typography sx={{ fontSize: '0.875rem', fontWeight: 600 }}>
                      {item.label}
                    </Typography>
                  }
                />
                {item.badge && (
                  <Chip
                    label={item.badge}
                    size="small"
                    sx={{
                      height: 20,
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      bgcolor: '#00843D',
                      color: '#FFFFFF',
                    }}
                  />
                )}
              </ListItemButton>
            ))}
          </List>
        </Box>
      )}

      {/* Campus */}
      <Box sx={{ mb: 2 }}>
        <Typography
          variant="overline"
          sx={{
            px: 1.5,
            fontWeight: 800,
            color: 'text.secondary',
            letterSpacing: '0.08em',
            display: 'block',
            mb: 0.5,
          }}
        >
          Campus
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
                mb: 0.5,
                py: 1,
                px: 1.5,
                color: '#475569',
                '&.active': {
                  backgroundColor: 'rgba(0, 132, 61, 0.1)',
                  color: '#00843D',
                  fontWeight: 700,
                },
                '&:hover': {
                  backgroundColor: 'rgba(0, 0, 0, 0.04)',
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 32, fontSize: '1.15rem' }}>{item.icon}</ListItemIcon>
              <ListItemText
                primary={
                  <Typography sx={{ fontSize: '0.875rem', fontWeight: 600 }}>
                    {item.label}
                  </Typography>
                }
              />
            </ListItemButton>
          ))}
        </List>
      </Box>

      {/* Account & AI */}
      <Box sx={{ mb: 2 }}>
        <Typography
          variant="overline"
          sx={{
            px: 1.5,
            fontWeight: 800,
            color: 'text.secondary',
            letterSpacing: '0.08em',
            display: 'block',
            mb: 0.5,
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
                mb: 0.5,
                py: 1,
                px: 1.5,
                color: '#475569',
                '&.active': {
                  backgroundColor: 'rgba(0, 132, 61, 0.1)',
                  color: '#00843D',
                  fontWeight: 700,
                },
                '&:hover': {
                  backgroundColor: 'rgba(0, 0, 0, 0.04)',
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 32, fontSize: '1.15rem' }}>{item.icon}</ListItemIcon>
              <ListItemText
                primary={
                  <Typography sx={{ fontSize: '0.875rem', fontWeight: 600 }}>
                    {item.label}
                  </Typography>
                }
              />
              {item.badge && (
                <Chip
                  label={item.badge}
                  size="small"
                  sx={{
                    height: 20,
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    bgcolor: 'rgba(21, 101, 192, 0.1)',
                    color: '#1565C0',
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
            backgroundColor: '#E8F5E9',
            border: '1px solid rgba(0, 132, 61, 0.2)',
            borderRadius: 3,
            fontSize: '0.72rem',
            color: 'text.secondary',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.75 }}>
            <Box
              sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                bgcolor: '#00843D',
                animation: 'pulse 2s infinite',
              }}
            />
            <Typography variant="caption" sx={{ color: '#00843D', fontWeight: 700 }}>
              System Online
            </Typography>
          </Box>
          <Typography variant="caption" sx={{ color: '#5A6474', display: 'block' }}>
            EduSphere v1.0 · AI: RAG+MCP
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
              borderRight: '1px solid rgba(0,0,0,0.08)',
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
              borderRight: '1px solid rgba(0,0,0,0.08)',
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
