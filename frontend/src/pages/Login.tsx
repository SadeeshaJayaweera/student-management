import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material'
import SchoolIcon from '@mui/icons-material/School'
import SmartToyIcon from '@mui/icons-material/SmartToy'
import MenuBookIcon from '@mui/icons-material/MenuBook'
import AnalyticsIcon from '@mui/icons-material/Analytics'
import SportsSoccerIcon from '@mui/icons-material/SportsSoccer'
import ArrowForwardIcon from '@mui/icons-material/ArrowForward'
import toast from 'react-hot-toast'
import { useAuth } from '@/contexts/AuthContext'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!username || !password) {
      toast.error('Please enter both username and password')
      return
    }
    setError(null)
    setLoading(true)
    try {
      await login(username, password)
      toast.success('Welcome back to NSBM EduSphere!')
      navigate('/dashboard')
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Invalid credentials'
      setError(msg)
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  const fillDemo = (role: string) => {
    const accounts: Record<string, [string, string]> = {
      student: ['student01', 'Student@123'],
      lecturer: ['kperera', 'Lecturer@123'],
      admin: ['admin', 'Admin@123'],
      alumni: ['alumni01', 'Alumni@123'],
    }
    const [u, p] = accounts[role]
    setUsername(u)
    setPassword(p)
    setError(null)
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        backgroundColor: '#F5F7FA',
      }}
    >
      <Grid container sx={{ minHeight: '100vh' }}>
        {/* Left Side: NSBM Green University Showcase */}
        <Grid
          size={{ xs: 0, md: 6, lg: 7 }}
          sx={{
            display: { xs: 'none', md: 'flex' },
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            p: 6,
            background: 'linear-gradient(135deg, #00843D 0%, #005020 100%)',
            color: '#FFFFFF',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Subtle background circles */}
          <Box
            sx={{
              position: 'absolute',
              width: 500,
              height: 500,
              borderRadius: '50%',
              background: 'radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%)',
              top: -100,
              right: -100,
            }}
          />
          <Box
            sx={{
              position: 'absolute',
              width: 400,
              height: 400,
              borderRadius: '50%',
              background: 'radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 70%)',
              bottom: -50,
              left: -50,
            }}
          />

          <Box sx={{ position: 'relative', zIndex: 1, maxWidth: 560, textAlign: 'center' }}>
            {/* NSBM Crest */}
            <Box
              component="img"
              src="/nsbm-logo.svg"
              alt="NSBM Logo"
              sx={{
                width: 100,
                height: 100,
                mx: 'auto',
                mb: 3,
                filter: 'drop-shadow(0 10px 20px rgba(0,0,0,0.25))',
              }}
            />

            <Typography
              variant="h2"
              sx={{
                fontFamily: "'Outfit', sans-serif",
                fontWeight: 900,
                fontSize: { md: '2.5rem', lg: '3.2rem' },
                lineHeight: 1.15,
                mb: 2,
                color: '#FFFFFF',
              }}
            >
              NSBM EduSphere
            </Typography>

            <Typography
              variant="subtitle1"
              sx={{
                color: 'rgba(255, 255, 255, 0.88)',
                fontSize: '1.1rem',
                lineHeight: 1.6,
                mb: 5,
                fontWeight: 400,
              }}
            >
              The intelligent digital campus for NSBM Green University. Seamless academic
              management, AI-driven learning, and connected campus life.
            </Typography>

            {/* Feature Badges */}
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                gap: 2,
                flexWrap: 'wrap',
              }}
            >
              {[
                { icon: <SmartToyIcon fontSize="small" />, label: 'AI RAG & Tutor' },
                { icon: <MenuBookIcon fontSize="small" />, label: 'Digital Library' },
                { icon: <AnalyticsIcon fontSize="small" />, label: 'Live Analytics' },
                { icon: <SportsSoccerIcon fontSize="small" />, label: 'Campus Life' },
              ].map((f) => (
                <Paper
                  key={f.label}
                  elevation={0}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1.25,
                    px: 2.5,
                    py: 1.5,
                    borderRadius: 3,
                    backgroundColor: 'rgba(255, 255, 255, 0.12)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    color: '#FFFFFF',
                  }}
                >
                  {f.icon}
                  <Typography variant="body2" sx={{ fontWeight: 600, fontSize: '0.85rem' }}>
                    {f.label}
                  </Typography>
                </Paper>
              ))}
            </Box>
          </Box>
        </Grid>

        {/* Right Side: Clean White Login Card */}
        <Grid
          size={{ xs: 12, md: 6, lg: 5 }}
          sx={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            p: { xs: 3, sm: 6 },
            backgroundColor: '#FFFFFF',
          }}
        >
          <Box sx={{ width: '100%', maxWidth: 420 }}>
            {/* Header */}
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <Box
                component="img"
                src="/nsbm-logo.svg"
                alt="NSBM Logo"
                sx={{
                  width: 56,
                  height: 56,
                  mb: 2,
                  display: { xs: 'inline-block', md: 'none' },
                }}
              />
              <Typography
                variant="h4"
                sx={{
                  fontFamily: "'Outfit', sans-serif",
                  fontWeight: 800,
                  color: '#1A1A2E',
                  mb: 1,
                }}
              >
                Welcome Back
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Sign in to your EduSphere account
              </Typography>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mb: 3, borderRadius: 2.5 }}>
                {error}
              </Alert>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit}>
              <Box sx={{ mb: 2.5 }}>
                <Typography variant="caption" sx={{ fontWeight: 700, color: '#1A1A2E', mb: 0.75, display: 'block' }}>
                  Username
                </Typography>
                <TextField
                  fullWidth
                  placeholder="Enter your username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoFocus
                  variant="outlined"
                  size="medium"
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2.5,
                      backgroundColor: '#F8FAFC',
                    },
                  }}
                />
              </Box>

              <Box sx={{ mb: 3 }}>
                <Typography variant="caption" sx={{ fontWeight: 700, color: '#1A1A2E', mb: 0.75, display: 'block' }}>
                  Password
                </Typography>
                <TextField
                  fullWidth
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  variant="outlined"
                  size="medium"
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2.5,
                      backgroundColor: '#F8FAFC',
                    },
                  }}
                />
              </Box>

              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                disabled={loading}
                endIcon={!loading && <ArrowForwardIcon />}
                sx={{
                  py: 1.5,
                  borderRadius: 2.5,
                  fontWeight: 700,
                  fontSize: '0.95rem',
                  backgroundColor: '#00843D',
                  '&:hover': {
                    backgroundColor: '#006B30',
                  },
                }}
              >
                {loading ? <CircularProgress size={24} color="inherit" /> : 'Sign In'}
              </Button>
            </form>

            {/* Quick Demo Logins */}
            <Box
              sx={{
                mt: 4,
                pt: 3,
                borderTop: '1px solid rgba(0, 0, 0, 0.08)',
              }}
            >
              <Typography
                variant="overline"
                sx={{
                  display: 'block',
                  textAlign: 'center',
                  fontWeight: 800,
                  color: 'text.secondary',
                  letterSpacing: '0.08em',
                  mb: 1.5,
                }}
              >
                Quick Demo Accounts
              </Typography>

              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
                {[
                  { role: 'student', label: '🎓 Student', color: '#00843D' },
                  { role: 'lecturer', label: '👨‍🏫 Lecturer', color: '#1565C0' },
                  { role: 'admin', label: '⚙️ Admin', color: '#C62828' },
                  { role: 'alumni', label: '🌐 Alumni', color: '#E65100' },
                ].map((demo) => (
                  <Button
                    key={demo.role}
                    variant="outlined"
                    size="small"
                    onClick={() => fillDemo(demo.role)}
                    sx={{
                      borderRadius: 2,
                      py: 0.85,
                      fontWeight: 600,
                      borderColor: 'rgba(0, 0, 0, 0.12)',
                      color: '#1A1A2E',
                      backgroundColor: '#F8FAFC',
                      '&:hover': {
                        borderColor: demo.color,
                        backgroundColor: 'rgba(0, 0, 0, 0.04)',
                        color: demo.color,
                      },
                    }}
                  >
                    {demo.label}
                  </Button>
                ))}
              </Box>

              <Typography
                variant="caption"
                sx={{
                  display: 'block',
                  textAlign: 'center',
                  color: 'text.secondary',
                  mt: 1.5,
                  fontSize: '0.75rem',
                }}
              >
                Click any role to autofill demo credentials
              </Typography>
            </Box>
          </Box>
        </Grid>
      </Grid>
    </Box>
  )
}
