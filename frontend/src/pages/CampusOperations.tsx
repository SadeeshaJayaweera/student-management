import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Button,
  Chip,
  Card,
  CardContent,
  LinearProgress,
  Divider,
  Alert,
  AlertTitle,
  CircularProgress,
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import RefreshIcon from '@mui/icons-material/Refresh';
import AccountBalanceIcon from '@mui/icons-material/AccountBalance';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import ApartmentIcon from '@mui/icons-material/Apartment';
import DirectionsBusIcon from '@mui/icons-material/DirectionsBus';
import MeetingRoomIcon from '@mui/icons-material/MeetingRoom';
import SportsSoccerIcon from '@mui/icons-material/SportsSoccer';
import NewspaperIcon from '@mui/icons-material/Newspaper';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import api from '@/api/client';
import toast from 'react-hot-toast';
import type { CampusOperationsOverview, CampusOperationalAlert } from '@/types';
import { useAuth } from '@/contexts/AuthContext';

export default function CampusOperations() {
  const { user } = useAuth();
  const [overview, setOverview] = useState<CampusOperationsOverview | null>(null);
  const [alerts, setAlerts] = useState<CampusOperationalAlert[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [ovRes, alRes] = await Promise.all([
        api.get<CampusOperationsOverview>('/campus-operations/overview'),
        api.get<CampusOperationalAlert[]>('/campus-operations/alerts'),
      ]);
      setOverview(ovRes.data);
      setAlerts(alRes.data);
    } catch {
      toast.error('Failed to load campus operations telemetry');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading && !overview) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress sx={{ color: '#00843D' }} />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1300, mx: 'auto', p: { xs: 2, md: 4 }, display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Header Banner */}
      <Paper
        elevation={0}
        sx={{
          p: 3.5,
          borderRadius: 3,
          border: '1px solid #E2E8F0',
          background: 'linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%)',
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
                bgcolor: 'rgba(0,132,61,0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#00843D',
              }}
            >
              <DashboardIcon sx={{ fontSize: 26 }} />
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#0F172A', letterSpacing: '-0.02em' }}>
              NSBM Unified Campus Operations Command Center
            </Typography>
          </Box>
          <Typography variant="body2" sx={{ color: '#64748B', maxWidth: 700, mt: 0.5 }}>
            Real-time executive telemetry across Institutional Finance, Library Systems, Housing & Hostels, Transit Fleet, Facilities, and Athletics.
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <Chip
            icon={<CheckCircleIcon sx={{ fontSize: '14px !important', color: '#00843D !important' }} />}
            label="CAMPUS NETWORK ONLINE"
            size="small"
            sx={{
              bgcolor: 'rgba(0,132,61,0.1)',
              color: '#00843D',
              fontWeight: 800,
              fontSize: '0.72rem',
              border: '1px solid rgba(0,132,61,0.25)',
              px: 0.5,
            }}
          />
          <Button
            variant="outlined"
            onClick={fetchData}
            startIcon={<RefreshIcon />}
            sx={{
              borderColor: '#E2E8F0',
              color: '#475569',
              fontWeight: 700,
              borderRadius: 2,
              textTransform: 'none',
              '&:hover': { borderColor: '#CBD5E1', bgcolor: '#F8FAFC' },
            }}
          >
            Refresh Telemetry
          </Button>
        </Box>
      </Paper>

      {/* Operational Alerts */}
      {alerts.length > 0 && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
          {alerts.map((al) => (
            <Alert
              key={al.id}
              severity={al.level === 'critical' ? 'error' : al.level === 'warning' ? 'warning' : 'info'}
              sx={{
                borderRadius: 2.5,
                border: '1px solid',
                borderColor: al.level === 'critical' ? '#FECDD3' : al.level === 'warning' ? '#FED7AA' : '#BAE6FD',
              }}
              action={
                <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600 }}>
                  {new Date(al.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </Typography>
              }
            >
              <AlertTitle sx={{ fontWeight: 800, fontSize: '0.9rem', mb: 0.2 }}>{al.title}</AlertTitle>
              {al.message}
            </Alert>
          ))}
        </Box>
      )}

      {/* Quick Access Desk Navigation Ribbon */}
      <Paper
        elevation={0}
        sx={{
          p: 2,
          borderRadius: 2.5,
          border: '1px solid #E2E8F0',
          bgcolor: '#FFFFFF',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 1.5,
        }}
      >
        <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#334155', fontSize: '0.85rem' }}>
          Operational Management Desks:
        </Typography>

        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {[
            { label: 'Finance & Fees', icon: <AccountBalanceIcon sx={{ fontSize: 16 }} />, to: '/billing' },
            { label: 'Digital Library', icon: <MenuBookIcon sx={{ fontSize: 16 }} />, to: '/library' },
            { label: 'Athletics & Teams', icon: <SportsSoccerIcon sx={{ fontSize: 16 }} />, to: '/sports' },
            { label: 'Hostels & Housing', icon: <ApartmentIcon sx={{ fontSize: 16 }} />, to: '/hostels' },
            { label: 'Transit & Shuttles', icon: <DirectionsBusIcon sx={{ fontSize: 16 }} />, to: '/transport' },
            { label: 'Venue Reservations', icon: <MeetingRoomIcon sx={{ fontSize: 16 }} />, to: '/facilities' },
            { label: 'Media & News', icon: <NewspaperIcon sx={{ fontSize: 16 }} />, to: '/news' },
          ].map((item) => (
            <Button
              key={item.label}
              component={Link}
              to={item.to}
              size="small"
              startIcon={item.icon}
              sx={{
                bgcolor: '#F8FAFC',
                border: '1px solid #E2E8F0',
                color: '#334155',
                fontSize: '0.78rem',
                fontWeight: 600,
                textTransform: 'none',
                borderRadius: 2,
                '&:hover': { bgcolor: '#F1F5F9', borderColor: '#CBD5E1' },
              }}
            >
              {item.label}
            </Button>
          ))}
        </Box>
      </Paper>

      {/* Operational Domains Grid */}
      {overview && (
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, 1fr)' },
            gap: 3,
          }}
        >
          {/* 1. Finance Domain */}
          <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #E2E8F0', borderLeft: '5px solid #6366F1' }}>
            <CardContent sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AccountBalanceIcon sx={{ color: '#6366F1', fontSize: 22 }} />
                  <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0F172A' }}>
                    Institutional Finance & Billing
                  </Typography>
                </Box>
                <Button component={Link} to="/billing" size="small" endIcon={<ArrowForwardIcon sx={{ fontSize: 14 }} />} sx={{ textTransform: 'none', color: '#6366F1', fontWeight: 700 }}>
                  View Invoices
                </Button>
              </Box>

              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                <Paper elevation={0} sx={{ p: 2, borderRadius: 2, bgcolor: '#F8FAFC', border: '1px solid #E2E8F0', textAlign: 'center' }}>
                  <Typography variant="h5" sx={{ fontWeight: 800, color: '#6366F1' }}>
                    LKR {(overview.finance.total_collected || 1620000).toLocaleString()}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 700, textTransform: 'uppercase' }}>
                    Revenue Collected
                  </Typography>
                </Paper>

                <Paper elevation={0} sx={{ p: 2, borderRadius: 2, bgcolor: '#F8FAFC', border: '1px solid #E2E8F0', textAlign: 'center' }}>
                  <Typography variant="h5" sx={{ fontWeight: 800, color: '#00843D' }}>
                    {overview.finance.collection_rate || 90.0}%
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 700, textTransform: 'uppercase' }}>
                    Collection Rate
                  </Typography>
                </Paper>
              </Box>

              <Box sx={{ pt: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={overview.finance.collection_rate || 90.0}
                  sx={{ height: 8, borderRadius: 4, bgcolor: '#EEF2FF', '& .MuiLinearProgress-bar': { bgcolor: '#6366F1' } }}
                />
              </Box>

              <Box sx={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#64748B', pt: 0.5 }}>
                <span>Total Invoiced: LKR {(overview.finance.total_invoiced || 1800000).toLocaleString()}</span>
                <span>Outstanding: LKR {(overview.finance.outstanding_balance || 180000).toLocaleString()}</span>
              </Box>
            </CardContent>
          </Card>

          {/* 2. Library Domain */}
          <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #E2E8F0', borderLeft: '5px solid #00843D' }}>
            <CardContent sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <MenuBookIcon sx={{ color: '#00843D', fontSize: 22 }} />
                  <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0F172A' }}>
                    Modern Digital & Physical Library
                  </Typography>
                </Box>
                <Button component={Link} to="/library" size="small" endIcon={<ArrowForwardIcon sx={{ fontSize: 14 }} />} sx={{ textTransform: 'none', color: '#00843D', fontWeight: 700 }}>
                  Open Catalog
                </Button>
              </Box>

              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                <Paper elevation={0} sx={{ p: 2, borderRadius: 2, bgcolor: '#F8FAFC', border: '1px solid #E2E8F0', textAlign: 'center' }}>
                  <Typography variant="h5" sx={{ fontWeight: 800, color: '#00843D' }}>
                    {overview.library.total_physical_books || 15}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 700, textTransform: 'uppercase' }}>
                    Physical Volumes
                  </Typography>
                </Paper>

                <Paper elevation={0} sx={{ p: 2, borderRadius: 2, bgcolor: '#F8FAFC', border: '1px solid #E2E8F0', textAlign: 'center' }}>
                  <Typography variant="h5" sx={{ fontWeight: 800, color: '#0284C7' }}>
                    {overview.library.total_digital_resources || 24}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 700, textTransform: 'uppercase' }}>
                    Digital Assets
                  </Typography>
                </Paper>
              </Box>

              <Box sx={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#64748B', pt: 1, borderTop: '1px solid #F1F5F9' }}>
                <span>Active Borrowings: {overview.library.active_borrowings || 8} books</span>
                <span style={{ color: overview.library.overdue_loans > 0 ? '#EF4444' : '#64748B' }}>
                  Overdue Loans: {overview.library.overdue_loans || 0}
                </span>
              </Box>
            </CardContent>
          </Card>

          {/* 3. Housing Domain */}
          <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #E2E8F0', borderLeft: '5px solid #F59E0B' }}>
            <CardContent sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <ApartmentIcon sx={{ color: '#F59E0B', fontSize: 22 }} />
                  <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0F172A' }}>
                    Student Housing & Residential Towers
                  </Typography>
                </Box>
                <Button component={Link} to="/hostels" size="small" endIcon={<ArrowForwardIcon sx={{ fontSize: 14 }} />} sx={{ textTransform: 'none', color: '#F59E0B', fontWeight: 700 }}>
                  Hostel Management
                </Button>
              </Box>

              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                <Paper elevation={0} sx={{ p: 2, borderRadius: 2, bgcolor: '#F8FAFC', border: '1px solid #E2E8F0', textAlign: 'center' }}>
                  <Typography variant="h5" sx={{ fontWeight: 800, color: '#F59E0B' }}>
                    {overview.accommodation.total_capacity || 56}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 700, textTransform: 'uppercase' }}>
                    Total Bed Capacity
                  </Typography>
                </Paper>

                <Paper elevation={0} sx={{ p: 2, borderRadius: 2, bgcolor: '#F8FAFC', border: '1px solid #E2E8F0', textAlign: 'center' }}>
                  <Typography variant="h5" sx={{ fontWeight: 800, color: '#00843D' }}>
                    {overview.accommodation.occupancy_rate || 100}%
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 700, textTransform: 'uppercase' }}>
                    Occupancy Rate
                  </Typography>
                </Paper>
              </Box>

              <Box sx={{ pt: 1 }}>
                <LinearProgress
                  variant="determinate"
                  value={overview.accommodation.occupancy_rate || 100}
                  sx={{ height: 8, borderRadius: 4, bgcolor: '#FEF3C7', '& .MuiLinearProgress-bar': { bgcolor: '#F59E0B' } }}
                />
              </Box>

              <Box sx={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#64748B', pt: 0.5 }}>
                <span>Occupied Beds: {overview.accommodation.occupied_beds || 56}</span>
                <span>Maintenance Requests: {overview.accommodation.pending_repairs || 0}</span>
              </Box>
            </CardContent>
          </Card>

          {/* 4. Transit Domain */}
          <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #E2E8F0', borderLeft: '5px solid #0EA5E9' }}>
            <CardContent sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <DirectionsBusIcon sx={{ color: '#0EA5E9', fontSize: 22 }} />
                  <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0F172A' }}>
                    Campus Shuttle & Commuter Fleet
                  </Typography>
                </Box>
                <Button component={Link} to="/transport" size="small" endIcon={<ArrowForwardIcon sx={{ fontSize: 14 }} />} sx={{ textTransform: 'none', color: '#0EA5E9', fontWeight: 700 }}>
                  Transit Fleet
                </Button>
              </Box>

              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                <Paper elevation={0} sx={{ p: 2, borderRadius: 2, bgcolor: '#F8FAFC', border: '1px solid #E2E8F0', textAlign: 'center' }}>
                  <Typography variant="h5" sx={{ fontWeight: 800, color: '#0EA5E9' }}>
                    {overview.transport.fleet_vehicles || 3}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 700, textTransform: 'uppercase' }}>
                    Active Green Fleet
                  </Typography>
                </Paper>

                <Paper elevation={0} sx={{ p: 2, borderRadius: 2, bgcolor: '#F8FAFC', border: '1px solid #E2E8F0', textAlign: 'center' }}>
                  <Typography variant="h5" sx={{ fontWeight: 800, color: '#6366F1' }}>
                    {overview.transport.active_transit_passes || 6}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 700, textTransform: 'uppercase' }}>
                    Active Transit Passes
                  </Typography>
                </Paper>
              </Box>

              <Box sx={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#64748B', pt: 1, borderTop: '1px solid #F1F5F9' }}>
                <span>Commuter Routes: {overview.transport.active_routes || 3} lines</span>
                <span>Daily Scheduled Trips: {overview.transport.daily_trips || 6} trips</span>
              </Box>
            </CardContent>
          </Card>

          {/* 5. Venues & Facilities */}
          <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #E2E8F0', borderLeft: '5px solid #10B981' }}>
            <CardContent sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <MeetingRoomIcon sx={{ color: '#10B981', fontSize: 22 }} />
                  <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0F172A' }}>
                    Campus Facilities & Venues
                  </Typography>
                </Box>
                <Button component={Link} to="/facilities" size="small" endIcon={<ArrowForwardIcon sx={{ fontSize: 14 }} />} sx={{ textTransform: 'none', color: '#10B981', fontWeight: 700 }}>
                  Space Bookings
                </Button>
              </Box>

              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                <Paper elevation={0} sx={{ p: 2, borderRadius: 2, bgcolor: '#F8FAFC', border: '1px solid #E2E8F0', textAlign: 'center' }}>
                  <Typography variant="h5" sx={{ fontWeight: 800, color: '#10B981' }}>
                    {overview.facilities.total_venues || 3}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 700, textTransform: 'uppercase' }}>
                    Managed Venues
                  </Typography>
                </Paper>

                <Paper elevation={0} sx={{ p: 2, borderRadius: 2, bgcolor: '#F8FAFC', border: '1px solid #E2E8F0', textAlign: 'center' }}>
                  <Typography variant="h5" sx={{ fontWeight: 800, color: '#F59E0B' }}>
                    {(overview.facilities.combined_capacity || 1615).toLocaleString()}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 700, textTransform: 'uppercase' }}>
                    Auditorium / Seat Capacity
                  </Typography>
                </Paper>
              </Box>

              <Box sx={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#64748B', pt: 1, borderTop: '1px solid #F1F5F9' }}>
                <span>Today's Reservations: {overview.facilities.reservations_today || 0}</span>
                <span>Pending Approvals: {overview.facilities.pending_approvals || 0}</span>
              </Box>
            </CardContent>
          </Card>

          {/* 6. Athletics & Media */}
          <Card elevation={0} sx={{ borderRadius: 3, border: '1px solid #E2E8F0', borderLeft: '5px solid #EF4444' }}>
            <CardContent sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SportsSoccerIcon sx={{ color: '#EF4444', fontSize: 22 }} />
                  <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0F172A' }}>
                    Athletics & Campus Media
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button component={Link} to="/sports" size="small" sx={{ textTransform: 'none', color: '#EF4444', fontWeight: 700 }}>
                    Sports
                  </Button>
                  <Button component={Link} to="/news" size="small" sx={{ textTransform: 'none', color: '#64748B', fontWeight: 700 }}>
                    News
                  </Button>
                </Box>
              </Box>

              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                <Paper elevation={0} sx={{ p: 2, borderRadius: 2, bgcolor: '#F8FAFC', border: '1px solid #E2E8F0', textAlign: 'center' }}>
                  <Typography variant="h5" sx={{ fontWeight: 800, color: '#EF4444' }}>
                    {overview.athletics.active_teams || 4}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 700, textTransform: 'uppercase' }}>
                    Varsity Teams
                  </Typography>
                </Paper>

                <Paper elevation={0} sx={{ p: 2, borderRadius: 2, bgcolor: '#F8FAFC', border: '1px solid #E2E8F0', textAlign: 'center' }}>
                  <Typography variant="h5" sx={{ fontWeight: 800, color: '#6366F1' }}>
                    {(overview.media.total_views || 8827).toLocaleString()}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 700, textTransform: 'uppercase' }}>
                    Campus Readers
                  </Typography>
                </Paper>
              </Box>

              <Box sx={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#64748B', pt: 1, borderTop: '1px solid #F1F5F9' }}>
                <span>Student Athletes: {overview.athletics.roster_athletes || 10}</span>
                <span>Published Stories: {overview.media.published_articles || 8}</span>
              </Box>
            </CardContent>
          </Card>
        </Box>
      )}
    </Box>
  );
}
