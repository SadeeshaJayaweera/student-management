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
  IconButton,
  InputAdornment,
  FormControlLabel,
  Checkbox,
  Link,
} from '@mui/material'
import AccountCircleOutlinedIcon from '@mui/icons-material/AccountCircleOutlined'
import LockOutlinedIcon from '@mui/icons-material/LockOutlined'
import VisibilityOutlinedIcon from '@mui/icons-material/VisibilityOutlined'
import VisibilityOffOutlinedIcon from '@mui/icons-material/VisibilityOffOutlined'
import ArrowForwardIcon from '@mui/icons-material/ArrowForward'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import LocalLibraryOutlinedIcon from '@mui/icons-material/LocalLibraryOutlined'
import InsightsOutlinedIcon from '@mui/icons-material/InsightsOutlined'
import VerifiedUserOutlinedIcon from '@mui/icons-material/VerifiedUserOutlined'
import SchoolIcon from '@mui/icons-material/School'
import CastForEducationIcon from '@mui/icons-material/CastForEducation'
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings'
import HubIcon from '@mui/icons-material/Hub'
import toast from 'react-hot-toast'
import { useAuth } from '@/contexts/AuthContext'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(true)
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
      const msg = err.response?.data?.detail || 'Invalid username or password'
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
    toast.success(`Loaded demo credentials for ${role.toUpperCase()}`, { duration: 1800 })
  }

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', backgroundColor: '#F8FAFC' }}>
      <Grid container sx={{ minHeight: '100vh' }}>
        {/* Left Side: Editorial Academic Showcase */}
        <Grid
          size={{ xs: 0, md: 6, lg: 7 }}
          sx={{
            display: { xs: 'none', md: 'flex' },
            flexDirection: 'column',
            justifyContent: 'space-between',
            p: { md: 6, lg: 8 },
            background: 'linear-gradient(145deg, #064E3B 0%, #022C22 100%)',
            color: '#FFFFFF',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Ambient Lighting Gradients */}
          <Box
            sx={{
              position: 'absolute',
              width: 600,
              height: 600,
              borderRadius: '50%',
              background: 'radial-gradient(circle, rgba(16, 185, 129, 0.15) 0%, transparent 70%)',
              top: -150,
              left: -150,
              pointerEvents: 'none',
            }}
          />
          <Box
            sx={{
              position: 'absolute',
              width: 500,
              height: 500,
              borderRadius: '50%',
              background: 'radial-gradient(circle, rgba(245, 158, 11, 0.12) 0%, transparent 70%)',
              bottom: -100,
              right: -100,
              pointerEvents: 'none',
            }}
          />

          {/* Top Brand Bar */}
          <Box sx={{ position: 'relative', zIndex: 1, display: 'flex', alignItems: 'center', gap: 2 }}>
            <Box
              sx={{
                display: 'inline-flex',
                alignItems: 'center',
                bgcolor: '#FFFFFF',
                borderRadius: 3,
                px: 2.2,
                py: 1,
                boxShadow: '0 8px 24px rgba(0,0,0,0.22)',
              }}
            >
              <Box
                component="img"
                src="/nsbm-logo.png"
                alt="NSBM Green University Town"
                sx={{
                  height: 44,
                  maxWidth: 220,
                  objectFit: 'contain',
                }}
              />
            </Box>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 800, fontFamily: "'Outfit', sans-serif", letterSpacing: '-0.01em', lineHeight: 1.1 }}>
                EDUSPHERE PORTAL
              </Typography>
              <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.75)', letterSpacing: '0.08em', fontWeight: 600 }}>
                MINISTRY OF EDUCATION • SRI LANKA
              </Typography>
            </Box>
          </Box>

          {/* Middle Value Proposition */}
          <Box sx={{ position: 'relative', zIndex: 1, maxWidth: 620, my: 4 }}>
            <Chip
              icon={<VerifiedUserOutlinedIcon sx={{ color: '#FCD34D !important', fontSize: '0.9rem' }} />}
              label="Accredited Academic Management Ecosystem"
              size="small"
              sx={{
                mb: 3,
                bgcolor: 'rgba(255, 255, 255, 0.1)',
                backdropFilter: 'blur(10px)',
                color: '#FCD34D',
                border: '1px solid rgba(252, 211, 77, 0.3)',
                fontWeight: 700,
                fontSize: '0.75rem',
              }}
            />

            <Typography
              variant="h2"
              sx={{
                fontFamily: "'Outfit', sans-serif",
                fontWeight: 900,
                fontSize: { md: '2.5rem', lg: '3.4rem' },
                lineHeight: 1.12,
                letterSpacing: '-0.03em',
                mb: 2.5,
              }}
            >
              The Next Generation of Academic Excellence.
            </Typography>

            <Typography
              variant="body1"
              sx={{
                color: 'rgba(255, 255, 255, 0.85)',
                fontSize: '1.05rem',
                lineHeight: 1.7,
                mb: 4.5,
                fontWeight: 400,
              }}
            >
              EduSphere integrates university lifecycle management with grounded AI Socratic tutoring,
              automated essay & code grading, smart library circulation, and real-time operations command.
            </Typography>

            {/* Feature Cards Grid */}
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 2 }}>
              {[
                { icon: <AutoAwesomeIcon sx={{ color: '#34D399' }} />, title: 'AI Socratic Suite', desc: 'RAG & automated grading' },
                { icon: <LocalLibraryOutlinedIcon sx={{ color: '#60A5FA' }} />, title: 'Smart Campus', desc: 'Library, transit & booking' },
                { icon: <InsightsOutlinedIcon sx={{ color: '#FCD34D' }} />, title: 'Audit Analytics', desc: 'Live GPA & rubric tracking' },
              ].map((f) => (
                <Paper
                  key={f.title}
                  elevation={0}
                  sx={{
                    p: 2.2,
                    borderRadius: 3,
                    backgroundColor: 'rgba(255, 255, 255, 0.08)',
                    backdropFilter: 'blur(12px)',
                    border: '1px solid rgba(255, 255, 255, 0.12)',
                    color: '#FFFFFF',
                  }}
                >
                  <Box sx={{ mb: 1 }}>{f.icon}</Box>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, fontSize: '0.875rem' }}>
                    {f.title}
                  </Typography>
                  <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: '0.72rem', display: 'block' }}>
                    {f.desc}
                  </Typography>
                </Paper>
              ))}
            </Box>
          </Box>

          {/* Bottom Trust Indicators */}
          <Box sx={{ position: 'relative', zIndex: 1, display: 'flex', gap: 5, pt: 3, borderTop: '1px solid rgba(255, 255, 255, 0.15)' }}>
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 800, fontFamily: "'Outfit', sans-serif", color: '#34D399' }}>
                99.8%
              </Typography>
              <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: '0.72rem' }}>
                System Reliability
              </Typography>
            </Box>
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 800, fontFamily: "'Outfit', sans-serif", color: '#FCD34D' }}>
                40+
              </Typography>
              <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: '0.72rem' }}>
                Degree Programs
              </Typography>
            </Box>
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 800, fontFamily: "'Outfit', sans-serif", color: '#60A5FA' }}>
                15,000+
              </Typography>
              <Typography variant="caption" sx={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: '0.72rem' }}>
                Enrolled Scholars
              </Typography>
            </Box>
          </Box>
        </Grid>

        {/* Right Side: High-End Authentication Card */}
        <Grid
          size={{ xs: 12, md: 6, lg: 5 }}
          sx={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            p: { xs: 3, sm: 6, lg: 8 },
            backgroundColor: '#FFFFFF',
          }}
        >
          <Box sx={{ width: '100%', maxWidth: 430 }}>
            {/* Header */}
            <Box sx={{ textAlign: 'center', mb: 3.5 }}>
              <Box
                component="img"
                src="/nsbm-logo.png"
                alt="NSBM Green University Town"
                sx={{
                  height: 62,
                  maxWidth: 240,
                  objectFit: 'contain',
                  mb: 2,
                }}
              />
              <Typography
                variant="h4"
                sx={{
                  fontFamily: "'Outfit', sans-serif",
                  fontWeight: 800,
                  color: '#0F172A',
                  letterSpacing: '-0.02em',
                  mb: 0.75,
                }}
              >
                Sign in to EduSphere
              </Typography>
              <Typography variant="body2" sx={{ color: '#64748B', fontSize: '0.9rem' }}>
                Official NSBM Green University Authentication Portal
              </Typography>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mb: 3, borderRadius: 2.5, fontSize: '0.85rem' }}>
                {error}
              </Alert>
            )}

            {/* Login Form */}
            <form onSubmit={handleSubmit}>
              <Box sx={{ mb: 2.5 }}>
                <Typography variant="caption" sx={{ fontWeight: 700, color: '#334155', mb: 0.75, display: 'block', fontSize: '0.78rem' }}>
                  Student / Staff ID or Username
                </Typography>
                <TextField
                  fullWidth
                  placeholder="e.g. student01 or kperera"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoFocus
                  slotProps={{
                    input: {
                      startAdornment: (
                        <InputAdornment position="start">
                          <AccountCircleOutlinedIcon sx={{ color: '#94A3B8', fontSize: '1.2rem' }} />
                        </InputAdornment>
                      ),
                    },
                  }}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2.5,
                      backgroundColor: '#F8FAFC',
                    },
                  }}
                />
              </Box>

              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.75 }}>
                  <Typography variant="caption" sx={{ fontWeight: 700, color: '#334155', fontSize: '0.78rem' }}>
                    Password
                  </Typography>
                  <Link href="#" underline="hover" sx={{ fontSize: '0.75rem', fontWeight: 600, color: '#00843D' }}>
                    Forgot password?
                  </Link>
                </Box>
                <TextField
                  fullWidth
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  slotProps={{
                    input: {
                      startAdornment: (
                        <InputAdornment position="start">
                          <LockOutlinedIcon sx={{ color: '#94A3B8', fontSize: '1.2rem' }} />
                        </InputAdornment>
                      ),
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            size="small"
                            onClick={() => setShowPassword(!showPassword)}
                            edge="end"
                            sx={{ color: '#94A3B8' }}
                          >
                            {showPassword ? <VisibilityOffOutlinedIcon fontSize="small" /> : <VisibilityOutlinedIcon fontSize="small" />}
                          </IconButton>
                        </InputAdornment>
                      ),
                    },
                  }}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2.5,
                      backgroundColor: '#F8FAFC',
                    },
                  }}
                />
              </Box>

              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      size="small"
                      sx={{ color: '#CBD5E1', '&.Mui-checked': { color: '#00843D' } }}
                    />
                  }
                  label={<Typography sx={{ fontSize: '0.8rem', color: '#475569', fontWeight: 500 }}>Remember this device</Typography>}
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
                  py: 1.4,
                  borderRadius: 2.5,
                  fontWeight: 700,
                  fontSize: '0.95rem',
                  background: 'linear-gradient(135deg, #00843D 0%, #059669 100%)',
                  boxShadow: '0 4px 14px rgba(0, 132, 61, 0.3)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #006B30 0%, #00843D 100%)',
                    boxShadow: '0 6px 20px rgba(0, 132, 61, 0.4)',
                  },
                }}
              >
                {loading ? <CircularProgress size={24} color="inherit" /> : 'Sign In to Portal'}
              </Button>
            </form>

            {/* Quick Demo Access Bar */}
            <Box sx={{ mt: 4, pt: 3, borderTop: '1px solid #E2E8F0' }}>
              <Typography
                variant="overline"
                sx={{
                  display: 'block',
                  textAlign: 'center',
                  fontWeight: 800,
                  color: '#94A3B8',
                  letterSpacing: '0.08em',
                  fontSize: '0.68rem',
                  mb: 1.5,
                }}
              >
                Quick Demo Access (1-Click Fill)
              </Typography>

              <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 1.25 }}>
                {[
                  { role: 'student', label: 'Student', icon: <SchoolIcon fontSize="small" sx={{ color: '#00843D' }} />, desc: 'Sadeesha Perera' },
                  { role: 'lecturer', label: 'Faculty', icon: <CastForEducationIcon fontSize="small" sx={{ color: '#2563EB' }} />, desc: 'Dr. Kasun Perera' },
                  { role: 'admin', label: 'Admin', icon: <AdminPanelSettingsIcon fontSize="small" sx={{ color: '#DC2626' }} />, desc: 'System Administrator' },
                  { role: 'alumni', label: 'Alumni', icon: <HubIcon fontSize="small" sx={{ color: '#D97706' }} />, desc: 'Ruwan Jayasinghe' },
                ].map((demo) => (
                  <Paper
                    key={demo.role}
                    elevation={0}
                    onClick={() => fillDemo(demo.role)}
                    sx={{
                      p: 1.25,
                      borderRadius: 2,
                      border: '1.5px solid #E2E8F0',
                      backgroundColor: '#F8FAFC',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1.2,
                      '&:hover': {
                        borderColor: '#00843D',
                        backgroundColor: '#FFFFFF',
                        boxShadow: '0 4px 12px rgba(0, 132, 61, 0.08)',
                        transform: 'translateY(-1px)',
                      },
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      {demo.icon}
                    </Box>
                    <Box sx={{ minWidth: 0 }}>
                      <Typography variant="body2" sx={{ fontWeight: 700, fontSize: '0.8rem', color: '#0F172A', lineHeight: 1.1 }}>
                        {demo.label}
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#64748B', fontSize: '0.68rem', display: 'block' }}>
                        {demo.desc}
                      </Typography>
                    </Box>
                  </Paper>
                ))}
              </Box>

              <Typography variant="caption" sx={{ display: 'block', textAlign: 'center', color: '#94A3B8', mt: 2, fontSize: '0.72rem' }}>
                Protected by Enterprise Multi-Tenant Security Controls
              </Typography>
            </Box>
          </Box>
        </Grid>
      </Grid>
    </Box>
  )
}
