import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AppBar,
  Toolbar,
  Box,
  Typography,
  IconButton,
  Button,
  Avatar,
  Tooltip,
  Badge,
  InputBase,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Chip,
} from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import SearchIcon from '@mui/icons-material/Search'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import NotificationsNoneIcon from '@mui/icons-material/NotificationsNone'
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown'
import AccountCircleOutlinedIcon from '@mui/icons-material/AccountCircleOutlined'
import LogoutIcon from '@mui/icons-material/Logout'
import SchoolIcon from '@mui/icons-material/School'
import { useAuth } from '@/contexts/AuthContext'

const initials = (name: string) =>
  name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

interface NavbarProps {
  onMenuClick: () => void
}

export default function Navbar({ onMenuClick }: NavbarProps) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const openMenu = Boolean(anchorEl)

  const handleProfileClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleCloseMenu = () => {
    setAnchorEl(null)
  }

  const handleLogout = () => {
    handleCloseMenu()
    logout()
  }

  return (
    <AppBar
      position="fixed"
      sx={{
        zIndex: (theme) => theme.zIndex.drawer + 1,
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(16px)',
        color: '#0F172A',
        borderBottom: '1px solid #E2E8F0',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.03)',
        height: 64,
        justifyContent: 'center',
      }}
    >
      <Toolbar sx={{ px: { xs: 2, sm: 3 }, gap: { xs: 1, md: 2 } }}>
        {/* Mobile menu trigger */}
        <IconButton
          color="inherit"
          aria-label="open drawer"
          edge="start"
          onClick={onMenuClick}
          sx={{ display: { md: 'none' }, mr: 1 }}
        >
          <MenuIcon />
        </IconButton>

        {/* NSBM Brand Logo & Title */}
        <Box
          onClick={() => navigate('/dashboard')}
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
            cursor: 'pointer',
            userSelect: 'none',
            minWidth: 220,
          }}
        >
          <Box
            component="img"
            src="/nsbm-logo.svg"
            alt="NSBM Logo"
            sx={{
              width: 38,
              height: 38,
              objectFit: 'contain',
              filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.06))',
              transition: 'transform 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
              '&:hover': {
                transform: 'scale(1.06)',
              },
            }}
          />
          <Box sx={{ display: 'flex', flexDirection: 'column' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 800,
                  fontFamily: "'Outfit', sans-serif",
                  lineHeight: 1.1,
                  fontSize: '1.2rem',
                  color: '#0F172A',
                  letterSpacing: '-0.02em',
                }}
              >
                EduSphere
              </Typography>
              <Chip
                label="NSBM"
                size="small"
                sx={{
                  height: 18,
                  fontSize: '0.62rem',
                  fontWeight: 800,
                  bgcolor: '#00843D',
                  color: '#FFFFFF',
                  borderRadius: 1,
                  letterSpacing: '0.05em',
                  px: 0.2,
                }}
              />
            </Box>
            <Typography
              variant="caption"
              sx={{
                fontSize: '0.68rem',
                color: '#64748B',
                fontWeight: 600,
                letterSpacing: '0.03em',
              }}
            >
              Green University Portal
            </Typography>
          </Box>
        </Box>

        {/* Center Global Search Bar */}
        <Box
          sx={{
            display: { xs: 'none', lg: 'flex' },
            alignItems: 'center',
            backgroundColor: '#F1F5F9',
            border: '1px solid #E2E8F0',
            borderRadius: 2.5,
            px: 1.75,
            py: 0.6,
            width: 360,
            transition: 'all 0.2s ease',
            '&:hover, &:focus-within': {
              backgroundColor: '#FFFFFF',
              borderColor: '#00843D',
              boxShadow: '0 0 0 3px rgba(0, 132, 61, 0.1)',
            },
          }}
        >
          <SearchIcon sx={{ color: '#94A3B8', fontSize: '1.2rem', mr: 1 }} />
          <InputBase
            placeholder="Search courses, library, exams... (⌘K)"
            sx={{
              fontSize: '0.85rem',
              color: '#0F172A',
              width: '100%',
              '& input::placeholder': { color: '#94A3B8', opacity: 1 },
            }}
          />
        </Box>

        <Box sx={{ flexGrow: 1 }} />

        {/* AI Quick Assistant Pill */}
        <Button
          variant="outlined"
          color="primary"
          size="small"
          startIcon={<AutoAwesomeIcon sx={{ color: '#00843D' }} />}
          onClick={() => navigate('/ai-chat')}
          sx={{
            display: { xs: 'none', sm: 'inline-flex' },
            borderRadius: 3,
            px: 2,
            py: 0.7,
            fontWeight: 700,
            fontSize: '0.825rem',
            borderColor: 'rgba(0, 132, 61, 0.3)',
            backgroundColor: 'rgba(0, 132, 61, 0.04)',
            color: '#00843D',
            '&:hover': {
              backgroundColor: 'rgba(0, 132, 61, 0.08)',
              borderColor: '#00843D',
              transform: 'translateY(-1px)',
            },
          }}
        >
          AI Assistant
        </Button>

        {/* Academic Term Chip */}
        <Chip
          label="2026/27 • Sem 2"
          size="small"
          sx={{
            display: { xs: 'none', md: 'inline-flex' },
            bgcolor: '#F1F5F9',
            color: '#475569',
            border: '1px solid #E2E8F0',
            fontWeight: 600,
            fontSize: '0.75rem',
            height: 28,
          }}
        />

        {/* Notifications Icon Button */}
        <Tooltip title="Notifications">
          <IconButton
            size="small"
            onClick={() => navigate('/notifications')}
            sx={{
              p: 1,
              borderRadius: 2.5,
              border: '1px solid #E2E8F0',
              backgroundColor: '#FFFFFF',
              color: '#475569',
              '&:hover': {
                backgroundColor: '#F8FAFC',
                borderColor: '#CBD5E1',
              },
            }}
          >
            <Badge badgeContent={3} color="primary" sx={{ '& .MuiBadge-badge': { fontSize: '0.65rem', height: 16, minWidth: 16 } }}>
              <NotificationsNoneIcon fontSize="small" />
            </Badge>
          </IconButton>
        </Tooltip>

        <Divider orientation="vertical" flexItem sx={{ mx: 0.5, height: 28, alignSelf: 'center' }} />

        {/* User Profile Pill & Dropdown */}
        {user && (
          <>
            <Box
              onClick={handleProfileClick}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1.25,
                cursor: 'pointer',
                p: 0.5,
                pr: 1,
                borderRadius: 3,
                border: '1px solid #E2E8F0',
                backgroundColor: '#FFFFFF',
                transition: 'all 0.2s ease',
                '&:hover': {
                  borderColor: '#CBD5E1',
                  backgroundColor: '#F8FAFC',
                },
              }}
            >
              <Badge
                overlap="circular"
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                variant="dot"
                sx={{
                  '& .MuiBadge-badge': {
                    backgroundColor: '#10B981',
                    color: '#10B981',
                    boxShadow: '0 0 0 2px #FFFFFF',
                  },
                }}
              >
                <Avatar
                  sx={{
                    width: 32,
                    height: 32,
                    fontSize: '0.8rem',
                    fontWeight: 700,
                    bgcolor: 'rgba(0, 132, 61, 0.1)',
                    color: '#00843D',
                    border: '1px solid rgba(0, 132, 61, 0.2)',
                  }}
                >
                  {initials(user.full_name)}
                </Avatar>
              </Badge>
              <Box sx={{ display: { xs: 'none', md: 'flex' }, flexDirection: 'column', alignItems: 'flex-start' }}>
                <Typography variant="body2" sx={{ fontWeight: 700, fontSize: '0.825rem', lineHeight: 1.2, color: '#0F172A' }}>
                  {user.full_name.split(' ')[0]}
                </Typography>
                <Typography variant="caption" sx={{ color: '#64748B', textTransform: 'capitalize', fontSize: '0.68rem', fontWeight: 600 }}>
                  {user.role}
                </Typography>
              </Box>
              <KeyboardArrowDownIcon sx={{ fontSize: '1.1rem', color: '#94A3B8' }} />
            </Box>

            {/* Profile Dropdown Menu */}
            <Menu
              anchorEl={anchorEl}
              open={openMenu}
              onClose={handleCloseMenu}
              onClick={handleCloseMenu}
              transformOrigin={{ horizontal: 'right', vertical: 'top' }}
              anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
              slotProps={{
                paper: {
                  elevation: 0,
                  sx: {
                    overflow: 'visible',
                    filter: 'drop-shadow(0 10px 25px rgba(0,0,0,0.08))',
                    mt: 1.2,
                    minWidth: 210,
                    borderRadius: 3,
                    border: '1px solid #E2E8F0',
                    p: 0.5,
                  },
                },
              }}
            >
              <Box sx={{ px: 2, py: 1.5 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#0F172A' }}>
                  {user.full_name}
                </Typography>
                <Typography variant="caption" sx={{ color: '#64748B', display: 'block' }}>
                  {user.email || `${user.username}@nsbm.ac.lk`}
                </Typography>
                <Chip
                  label={user.role.toUpperCase()}
                  size="small"
                  sx={{ mt: 0.75, height: 20, fontSize: '0.65rem', fontWeight: 700, bgcolor: 'rgba(0,132,61,0.1)', color: '#00843D' }}
                />
              </Box>
              <Divider sx={{ my: 0.5 }} />
              <MenuItem onClick={() => navigate('/profile')}>
                <ListItemIcon>
                  <AccountCircleOutlinedIcon fontSize="small" sx={{ color: '#475569' }} />
                </ListItemIcon>
                <ListItemText primary={<Typography sx={{ fontSize: '0.85rem', fontWeight: 500 }}>My Profile & Settings</Typography>} />
              </MenuItem>
              <MenuItem onClick={() => navigate('/courses')}>
                <ListItemIcon>
                  <SchoolIcon fontSize="small" sx={{ color: '#475569' }} />
                </ListItemIcon>
                <ListItemText primary={<Typography sx={{ fontSize: '0.85rem', fontWeight: 500 }}>Enrolled Courses</Typography>} />
              </MenuItem>
              <Divider sx={{ my: 0.5 }} />
              <MenuItem onClick={handleLogout} sx={{ color: '#DC2626' }}>
                <ListItemIcon>
                  <LogoutIcon fontSize="small" sx={{ color: '#DC2626' }} />
                </ListItemIcon>
                <ListItemText primary={<Typography sx={{ fontSize: '0.85rem', fontWeight: 600 }}>Sign Out</Typography>} />
              </MenuItem>
            </Menu>
          </>
        )}
      </Toolbar>
    </AppBar>
  )
}
