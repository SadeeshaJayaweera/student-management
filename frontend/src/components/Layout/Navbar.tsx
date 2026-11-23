import React from 'react'
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
} from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import SmartToyIcon from '@mui/icons-material/SmartToy'
import LogoutIcon from '@mui/icons-material/Logout'
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

  return (
    <AppBar
      position="fixed"
      sx={{
        zIndex: (theme) => theme.zIndex.drawer + 1,
        backgroundColor: '#FFFFFF',
        color: '#1A1A2E',
        borderBottom: '1px solid rgba(0, 0, 0, 0.08)',
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.04)',
        height: 70,
        justifyContent: 'center',
      }}
    >
      <Toolbar sx={{ px: { xs: 2, sm: 3 } }}>
        <IconButton
          color="inherit"
          aria-label="open drawer"
          edge="start"
          onClick={onMenuClick}
          sx={{ mr: 2, display: { md: 'none' } }}
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
          }}
        >
          <Box
            component="img"
            src="/nsbm-logo.svg"
            alt="NSBM Logo"
            sx={{
              width: 42,
              height: 42,
              objectFit: 'contain',
              transition: 'transform 0.2s ease',
              '&:hover': {
                transform: 'scale(1.05)',
              },
            }}
          />
          <Box sx={{ display: 'flex', flexDirection: 'column' }}>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 800,
                fontFamily: "'Outfit', sans-serif",
                lineHeight: 1.1,
                fontSize: { xs: '1.05rem', sm: '1.2rem' },
                background: 'linear-gradient(135deg, #00843D 0%, #1565C0 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              EduSphere
            </Typography>
            <Typography
              variant="caption"
              sx={{
                fontSize: '0.68rem',
                color: 'text.secondary',
                fontWeight: 600,
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}
            >
              NSBM Green University
            </Typography>
          </Box>
        </Box>

        <Box sx={{ flexGrow: 1 }} />

        {/* AI Quick Access Button */}
        <Button
          variant="outlined"
          color="primary"
          size="small"
          startIcon={<SmartToyIcon />}
          onClick={() => navigate('/ai-chat')}
          sx={{
            mr: { xs: 1, sm: 2 },
            display: { xs: 'none', sm: 'inline-flex' },
            borderRadius: 2.5,
            px: 2,
            py: 0.75,
            fontWeight: 600,
            borderColor: 'rgba(0, 132, 61, 0.3)',
            backgroundColor: 'rgba(0, 132, 61, 0.04)',
            '&:hover': {
              backgroundColor: 'rgba(0, 132, 61, 0.1)',
              borderColor: '#00843D',
            },
          }}
        >
          AI Assistant
        </Button>

        {/* User Info */}
        {user && (
          <Box
            onClick={() => navigate('/profile')}
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1.25,
              cursor: 'pointer',
              p: 0.75,
              px: 1.5,
              borderRadius: 2.5,
              transition: 'background 0.2s ease',
              '&:hover': {
                backgroundColor: 'rgba(0, 132, 61, 0.06)',
              },
            }}
          >
            <Avatar
              sx={{
                width: 36,
                height: 36,
                fontSize: '0.85rem',
                fontWeight: 700,
                bgcolor: 'rgba(0, 132, 61, 0.12)',
                color: '#00843D',
                border: '1.5px solid rgba(0, 132, 61, 0.25)',
              }}
            >
              {initials(user.full_name)}
            </Avatar>
            <Box sx={{ display: { xs: 'none', sm: 'flex' }, flexDirection: 'column' }}>
              <Typography variant="body2" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
                {user.full_name.split(' ')[0]}
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  color: 'text.secondary',
                  textTransform: 'capitalize',
                  fontWeight: 500,
                  fontSize: '0.7rem',
                }}
              >
                {user.role}
              </Typography>
            </Box>
          </Box>
        )}

        {/* Logout */}
        <Tooltip title="Sign Out">
          <IconButton
            onClick={logout}
            color="error"
            size="small"
            sx={{
              ml: 1,
              p: 1,
              borderRadius: 2,
              border: '1px solid rgba(229, 57, 53, 0.2)',
              backgroundColor: 'rgba(229, 57, 53, 0.04)',
              '&:hover': {
                backgroundColor: 'rgba(229, 57, 53, 0.12)',
              },
            }}
          >
            <LogoutIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Toolbar>
    </AppBar>
  )
}
