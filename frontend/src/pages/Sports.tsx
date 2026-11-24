import React, { useEffect, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Tabs,
  Tab,
  Chip,
  Card,
  CardContent,
  CardActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  CircularProgress,
  Divider,
} from '@mui/material';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import SportsScoreIcon from '@mui/icons-material/SportsScore';
import StadiumIcon from '@mui/icons-material/Stadium';
import GroupsIcon from '@mui/icons-material/Groups';
import EventAvailableIcon from '@mui/icons-material/EventAvailable';
import AddCircleIcon from '@mui/icons-material/AddCircle';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CloseIcon from '@mui/icons-material/Close';
import api from '@/api/client';
import toast from 'react-hot-toast';
import type {
  Club,
  ClubEvent,
  AthleticTeam,
  SportsFixture,
  SportsFacilityBooking,
  AthleticStats,
} from '@/types';
import { useAuth } from '@/contexts/AuthContext';

const SPORT_ICONS: Record<string, string> = {
  cricket: '🏏',
  rugby: '🏉',
  football: '⚽',
  basketball: '🏀',
  swimming: '🏊',
  badminton: '🏸',
  esports: '🎮',
  tennis: '🎾',
  volleyball: '🏐',
};

const CAT_COLOR: Record<string, string> = {
  sports: '#EF4444',
  technical: '#6366F1',
  cultural: '#F59E0B',
  academic: '#10B981',
  social: '#EC4899',
};

export default function Sports() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<number>(0);

  // Data State
  const [teams, setTeams] = useState<AthleticTeam[]>([]);
  const [fixtures, setFixtures] = useState<SportsFixture[]>([]);
  const [bookings, setBookings] = useState<SportsFacilityBooking[]>([]);
  const [stats, setStats] = useState<AthleticStats | null>(null);
  const [selectedTeam, setSelectedTeam] = useState<AthleticTeam | null>(null);

  const [clubs, setClubs] = useState<Club[]>([]);
  const [events, setEvents] = useState<ClubEvent[]>([]);
  const [loading, setLoading] = useState(true);

  // Facility booking modal
  const [showBookingModal, setShowBookingModal] = useState<boolean>(false);
  const [facilityName, setFacilityName] = useState<string>('NSBM Green Stadium');
  const [bookingPurpose, setBookingPurpose] = useState<string>('Varsity Practice & Conditioning');
  const [bookingStartTime, setBookingStartTime] = useState<string>('');
  const [bookingEndTime, setBookingEndTime] = useState<string>('');
  const [submittingBooking, setSubmittingBooking] = useState<boolean>(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [teamsR, fixR, bookR, statsR, clubsR, eventsR] = await Promise.all([
        api.get<AthleticTeam[]>('/athletics/teams'),
        api.get<SportsFixture[]>('/athletics/fixtures'),
        api.get<SportsFacilityBooking[]>('/athletics/facility-bookings'),
        api.get<AthleticStats>('/athletics/stats'),
        api.get<Club[]>('/sports/clubs'),
        api.get<ClubEvent[]>('/sports/events?upcoming_only=true'),
      ]);
      setTeams(teamsR.data);
      setFixtures(fixR.data);
      setBookings(bookR.data);
      setStats(statsR.data);
      setClubs(clubsR.data);
      setEvents(eventsR.data);
    } catch (err) {
      console.error('Failed to load athletics data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const joinClub = async (clubId: number, name: string) => {
    try {
      await api.post(`/sports/clubs/${clubId}/join`);
      toast.success(`🎉 Joined ${name}!`);
      loadData();
    } catch (e: any) {
      toast(e.response?.data?.detail || 'Could not join club', { icon: '⚠️' });
    }
  };

  const registerEvent = async (eventId: number) => {
    try {
      await api.post(`/sports/events/${eventId}/register`);
      toast.success('✅ Registered for event!');
    } catch (e: any) {
      toast(e.response?.data?.detail || 'Could not register', { icon: '⚠️' });
    }
  };

  const handleCreateBooking = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!facilityName || !bookingStartTime || !bookingEndTime || submittingBooking) return;

    try {
      setSubmittingBooking(true);
      await api.post('/athletics/facility-bookings', {
        facility_name: facilityName,
        purpose: bookingPurpose,
        start_time: new Date(bookingStartTime).toISOString(),
        end_time: new Date(bookingEndTime).toISOString(),
      });
      toast.success('Facility reserved successfully!');
      setShowBookingModal(false);
      loadData();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to book facility.');
    } finally {
      setSubmittingBooking(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress sx={{ color: '#00843D' }} />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1300, mx: 'auto', p: { xs: 2, md: 4 }, display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Page Header */}
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
              <EmojiEventsIcon sx={{ fontSize: 26 }} />
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#0F172A', letterSpacing: '-0.02em' }}>
              NSBM Sports & Athletic Management
            </Typography>
          </Box>
          <Typography variant="body2" sx={{ color: '#64748B', maxWidth: 700, mt: 0.5 }}>
            Varsity athletic teams, SLUG championship tournaments, inter-university fixtures, student sports clubs, and ground reservations.
          </Typography>
        </Box>

        <Button
          variant="contained"
          onClick={() => setShowBookingModal(true)}
          startIcon={<StadiumIcon />}
          sx={{
            bgcolor: '#00843D',
            color: '#FFFFFF',
            fontWeight: 700,
            px: 3,
            py: 1.1,
            borderRadius: 2,
            textTransform: 'none',
            boxShadow: 'none',
            '&:hover': { bgcolor: '#006B31', boxShadow: '0 4px 12px rgba(0,132,61,0.2)' },
          }}
        >
          Book Sports Facility
        </Button>
      </Paper>

      {/* KPI Stats Cards */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
          gap: 2.5,
        }}
      >
        <Paper
          elevation={0}
          sx={{
            p: 2.5,
            borderRadius: 3,
            border: '1px solid #E2E8F0',
            bgcolor: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            gap: 2,
          }}
        >
          <Box sx={{ width: 48, height: 48, borderRadius: 2, bgcolor: 'rgba(0,132,61,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem' }}>
            🏆
          </Box>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#00843D' }}>
              {stats?.total_teams || teams.length}
            </Typography>
            <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
              Varsity Squads
            </Typography>
          </Box>
        </Paper>

        <Paper
          elevation={0}
          sx={{
            p: 2.5,
            borderRadius: 3,
            border: '1px solid #E2E8F0',
            bgcolor: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            gap: 2,
          }}
        >
          <Box sx={{ width: 48, height: 48, borderRadius: 2, bgcolor: 'rgba(99,102,241,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem' }}>
            🏃
          </Box>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#6366F1' }}>
              {stats?.total_athletes || (teams.length * 12)}
            </Typography>
            <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
              Student Athletes
            </Typography>
          </Box>
        </Paper>

        <Paper
          elevation={0}
          sx={{
            p: 2.5,
            borderRadius: 3,
            border: '1px solid #E2E8F0',
            bgcolor: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            gap: 2,
          }}
        >
          <Box sx={{ width: 48, height: 48, borderRadius: 2, bgcolor: 'rgba(239,68,68,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem' }}>
            ⚔️
          </Box>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#EF4444' }}>
              {stats?.upcoming_fixtures_count || fixtures.filter(f => f.status === 'upcoming').length || 2}
            </Typography>
            <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
              Upcoming Fixtures
            </Typography>
          </Box>
        </Paper>

        <Paper
          elevation={0}
          sx={{
            p: 2.5,
            borderRadius: 3,
            border: '1px solid #E2E8F0',
            bgcolor: '#FFFFFF',
            display: 'flex',
            alignItems: 'center',
            gap: 2,
          }}
        >
          <Box sx={{ width: 48, height: 48, borderRadius: 2, bgcolor: 'rgba(245,158,11,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem' }}>
            🥇
          </Box>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#F59E0B' }}>
              {stats?.matches_won || 14}
            </Typography>
            <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
              Match Victories
            </Typography>
          </Box>
        </Paper>
      </Box>

      {/* Tabs Navigation */}
      <Paper elevation={0} sx={{ borderBottom: '1px solid #E2E8F0', bgcolor: 'transparent' }}>
        <Tabs
          value={activeTab}
          onChange={(_, val) => setActiveTab(val)}
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            '& .MuiTabs-indicator': { backgroundColor: '#00843D', height: 3, borderRadius: '3px 3px 0 0' },
            '& .MuiTab-root': {
              textTransform: 'none',
              fontWeight: 700,
              fontSize: '0.92rem',
              color: '#64748B',
              minHeight: 48,
              '&.Mui-selected': { color: '#00843D' },
            },
          }}
        >
          <Tab icon={<EmojiEventsIcon sx={{ fontSize: 18, mr: 0.5 }} />} iconPosition="start" label={`Teams & Rosters (${teams.length})`} />
          <Tab icon={<SportsScoreIcon sx={{ fontSize: 18, mr: 0.5 }} />} iconPosition="start" label={`Fixtures & Results (${fixtures.length})`} />
          <Tab icon={<StadiumIcon sx={{ fontSize: 18, mr: 0.5 }} />} iconPosition="start" label={`Facility Schedule (${bookings.length})`} />
          <Tab icon={<GroupsIcon sx={{ fontSize: 18, mr: 0.5 }} />} iconPosition="start" label={`Student Clubs (${clubs.length})`} />
          <Tab icon={<EventAvailableIcon sx={{ fontSize: 18, mr: 0.5 }} />} iconPosition="start" label={`Sports Events (${events.length})`} />
        </Tabs>
      </Paper>

      {/* TAB 0: Teams & Rosters */}
      {activeTab === 0 && (
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' },
            gap: 3,
          }}
        >
          {teams.map((team) => {
            const icon = SPORT_ICONS[team.sport_type] || '🏅';
            return (
              <Card
                key={team.id}
                elevation={0}
                sx={{
                  borderRadius: 3,
                  border: '1px solid #E2E8F0',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'all 0.15s ease-in-out',
                  '&:hover': {
                    borderColor: '#CBD5E1',
                    boxShadow: '0 4px 14px rgba(0,0,0,0.05)',
                  },
                }}
              >
                <CardContent sx={{ p: 3, flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Box
                      sx={{
                        width: 52,
                        height: 52,
                        borderRadius: 2.5,
                        bgcolor: '#F8FAFC',
                        border: '1px solid #E2E8F0',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '2rem',
                      }}
                    >
                      {icon}
                    </Box>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0F172A', lineHeight: 1.3 }}>
                        {team.name}
                      </Typography>
                      <Chip
                        label={`${team.division} • ${team.sport_type}`}
                        size="small"
                        sx={{
                          height: 20,
                          fontSize: '0.68rem',
                          fontWeight: 700,
                          textTransform: 'uppercase',
                          bgcolor: 'rgba(0,132,61,0.08)',
                          color: '#00843D',
                          mt: 0.5,
                        }}
                      />
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.8, fontSize: '0.84rem' }}>
                    {team.captain_name && (
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" sx={{ color: '#64748B' }}>Team Captain:</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 700, color: '#1E293B' }}>{team.captain_name}</Typography>
                      </Box>
                    )}
                    {team.coach_name && (
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" sx={{ color: '#64748B' }}>Head Coach:</Typography>
                        <Typography variant="body2" sx={{ fontWeight: 700, color: '#1E293B' }}>{team.coach_name}</Typography>
                      </Box>
                    )}
                    {team.home_venue && (
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" sx={{ color: '#64748B' }}>Home Venue:</Typography>
                        <Typography variant="body2" sx={{ color: '#475569' }}>{team.home_venue}</Typography>
                      </Box>
                    )}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" sx={{ color: '#64748B' }}>Roster Strength:</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 700, color: '#00843D' }}>
                        {team.roster?.length || 12} Registered Athletes
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>

                <CardActions sx={{ p: 2.5, pt: 0 }}>
                  <Button
                    variant="outlined"
                    fullWidth
                    onClick={() => setSelectedTeam(team)}
                    sx={{
                      borderColor: '#E2E8F0',
                      color: '#0F172A',
                      fontWeight: 700,
                      textTransform: 'none',
                      borderRadius: 2,
                      '&:hover': { borderColor: '#00843D', color: '#00843D', bgcolor: 'rgba(0,132,61,0.04)' },
                    }}
                  >
                    View Roster & Schedule
                  </Button>
                </CardActions>
              </Card>
            );
          })}
        </Box>
      )}

      {/* TAB 1: Fixtures & Results */}
      {activeTab === 1 && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
          {fixtures.map((f) => {
            const dt = new Date(f.scheduled_time);
            const isCompleted = f.status === 'completed';
            const won = f.match_result === 'won';
            return (
              <Paper
                key={f.id}
                elevation={0}
                sx={{
                  p: 2.5,
                  borderRadius: 3,
                  border: '1px solid #E2E8F0',
                  bgcolor: '#FFFFFF',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 3,
                  flexWrap: { xs: 'wrap', md: 'nowrap' },
                }}
              >
                <Box
                  sx={{
                    width: 60,
                    height: 60,
                    borderRadius: 2.5,
                    bgcolor: '#F8FAFC',
                    border: '1px solid #E2E8F0',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Typography sx={{ fontWeight: 800, fontSize: '1.2rem', color: '#0F172A', lineHeight: 1 }}>
                    {dt.getDate()}
                  </Typography>
                  <Typography sx={{ fontSize: '0.7rem', color: '#64748B', textTransform: 'uppercase', fontWeight: 700 }}>
                    {dt.toLocaleString('default', { month: 'short' })}
                  </Typography>
                </Box>

                <Box sx={{ flex: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                    <Chip label={f.tournament_name} size="small" sx={{ bgcolor: '#EFF6FF', color: '#2563EB', fontWeight: 700, fontSize: '0.72rem' }} />
                    <Typography variant="caption" sx={{ color: '#64748B', textTransform: 'uppercase', fontWeight: 600 }}>
                      • {f.fixture_type}
                    </Typography>
                  </Box>
                  <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0F172A' }}>
                    {f.team_name || 'NSBM Green Team'}{' '}
                    <Typography component="span" sx={{ color: '#94A3B8', fontWeight: 500 }}>
                      vs
                    </Typography>{' '}
                    {f.opponent_name}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#64748B', fontSize: '0.82rem', mt: 0.3 }}>
                    📍 {f.venue} · ⏰ {dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </Typography>
                  {f.highlights && (
                    <Typography variant="body2" sx={{ color: '#00843D', fontSize: '0.8rem', mt: 0.5, fontStyle: 'italic' }}>
                      “{f.highlights}”
                    </Typography>
                  )}
                </Box>

                {isCompleted ? (
                  <Box sx={{ textAlign: 'right', minWidth: 100 }}>
                    <Typography variant="h6" sx={{ fontWeight: 800, color: '#0F172A' }}>
                      {f.our_score || '0'} - {f.opponent_score || '0'}
                    </Typography>
                    <Chip
                      label={won ? 'VICTORY' : f.match_result?.toUpperCase() || 'COMPLETED'}
                      size="small"
                      sx={{
                        bgcolor: won ? 'rgba(0,132,61,0.1)' : 'rgba(239,68,68,0.1)',
                        color: won ? '#00843D' : '#EF4444',
                        fontWeight: 800,
                        fontSize: '0.72rem',
                        mt: 0.5,
                      }}
                    />
                  </Box>
                ) : (
                  <Box sx={{ textAlign: 'right', minWidth: 100 }}>
                    <Chip
                      label="UPCOMING"
                      size="small"
                      sx={{
                        bgcolor: 'rgba(245,158,11,0.1)',
                        color: '#F59E0B',
                        fontWeight: 800,
                        fontSize: '0.72rem',
                      }}
                    />
                  </Box>
                )}
              </Paper>
            );
          })}
        </Box>
      )}

      {/* TAB 2: Facility Schedule */}
      {activeTab === 2 && (
        <TableContainer component={Paper} elevation={0} sx={{ borderRadius: 3, border: '1px solid #E2E8F0' }}>
          <Table>
            <TableHead sx={{ bgcolor: '#F8FAFC' }}>
              <TableRow>
                <TableCell sx={{ fontWeight: 700, color: '#475569', fontSize: '0.8rem' }}>Facility Venue</TableCell>
                <TableCell sx={{ fontWeight: 700, color: '#475569', fontSize: '0.8rem' }}>Team / Group</TableCell>
                <TableCell sx={{ fontWeight: 700, color: '#475569', fontSize: '0.8rem' }}>Scheduled Time</TableCell>
                <TableCell sx={{ fontWeight: 700, color: '#475569', fontSize: '0.8rem' }}>Session Purpose</TableCell>
                <TableCell sx={{ fontWeight: 700, color: '#475569', fontSize: '0.8rem' }}>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {bookings.map((b) => (
                <TableRow key={b.id} hover sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                  <TableCell sx={{ fontWeight: 700, color: '#00843D' }}>{b.facility_name}</TableCell>
                  <TableCell sx={{ fontWeight: 600, color: '#1E293B' }}>{b.team_name || 'Varsity Squad'}</TableCell>
                  <TableCell sx={{ fontSize: '0.82rem', color: '#64748B' }}>
                    {new Date(b.start_time).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })} -{' '}
                    {new Date(b.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </TableCell>
                  <TableCell sx={{ fontSize: '0.85rem', color: '#334155' }}>{b.purpose}</TableCell>
                  <TableCell>
                    <Chip
                      label={b.status.toUpperCase()}
                      size="small"
                      sx={{ bgcolor: 'rgba(0,132,61,0.1)', color: '#00843D', fontWeight: 800, fontSize: '0.7rem' }}
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* TAB 3: Student Clubs */}
      {activeTab === 3 && (
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' },
            gap: 3,
          }}
        >
          {clubs.map((c) => {
            const color = CAT_COLOR[c.category] || '#00843D';
            const full = c.member_count >= c.max_members;
            return (
              <Card
                key={c.id}
                elevation={0}
                sx={{
                  borderRadius: 3,
                  border: '1px solid #E2E8F0',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'all 0.15s ease-in-out',
                  '&:hover': {
                    borderColor: '#CBD5E1',
                    boxShadow: '0 4px 14px rgba(0,0,0,0.05)',
                  },
                }}
              >
                <Box
                  sx={{
                    p: 2.5,
                    bgcolor: `${color}10`,
                    borderBottom: '1px solid #E2E8F0',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0F172A' }}>
                    {c.name}
                  </Typography>
                  <Chip
                    label={c.category}
                    size="small"
                    sx={{
                      bgcolor: '#FFFFFF',
                      color: color,
                      fontWeight: 700,
                      fontSize: '0.72rem',
                      textTransform: 'uppercase',
                      border: `1px solid ${color}40`,
                    }}
                  />
                </Box>

                <CardContent sx={{ p: 2.5, flex: 1, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                  <Typography variant="body2" sx={{ color: '#64748B', lineHeight: 1.5, flex: 1 }}>
                    {c.description}
                  </Typography>

                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.82rem', pt: 1, borderTop: '1px solid #F1F5F9' }}>
                    <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600 }}>
                      👥 {c.member_count} / {c.max_members} members
                    </Typography>
                    {c.president_name && (
                      <Typography variant="caption" sx={{ color: '#475569', fontWeight: 600 }}>
                        👑 {c.president_name}
                      </Typography>
                    )}
                  </Box>
                </CardContent>

                <CardActions sx={{ p: 2.5, pt: 0 }}>
                  <Button
                    variant="contained"
                    fullWidth
                    disabled={full}
                    onClick={() => joinClub(c.id, c.name)}
                    sx={{
                      bgcolor: '#00843D',
                      color: '#FFFFFF',
                      fontWeight: 700,
                      borderRadius: 2,
                      textTransform: 'none',
                      boxShadow: 'none',
                      '&:hover': { bgcolor: '#006B31' },
                    }}
                  >
                    {full ? 'Club Roster Full' : 'Join Student Club'}
                  </Button>
                </CardActions>
              </Card>
            );
          })}
        </Box>
      )}

      {/* TAB 4: Sports Events */}
      {activeTab === 4 && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
          {events.map((e) => {
            const d = new Date(e.event_date);
            return (
              <Paper
                key={e.id}
                elevation={0}
                sx={{
                  p: 2.5,
                  borderRadius: 3,
                  border: '1px solid #E2E8F0',
                  bgcolor: '#FFFFFF',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 3,
                  flexWrap: { xs: 'wrap', md: 'nowrap' },
                }}
              >
                <Box
                  sx={{
                    width: 60,
                    height: 60,
                    borderRadius: 2.5,
                    bgcolor: 'rgba(0,132,61,0.08)',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Typography sx={{ fontWeight: 800, fontSize: '1.2rem', color: '#00843D', lineHeight: 1 }}>
                    {d.getDate()}
                  </Typography>
                  <Typography sx={{ fontSize: '0.7rem', color: '#00843D', textTransform: 'uppercase', fontWeight: 700 }}>
                    {d.toLocaleString('default', { month: 'short' })}
                  </Typography>
                </Box>

                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0F172A' }}>
                    {e.title}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#64748B', fontSize: '0.82rem', mt: 0.3 }}>
                    🏆 {e.club} · 📍 {e.location || 'NSBM Sports Complex'} · ⏰ {d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </Typography>
                  {e.description && (
                    <Typography variant="body2" sx={{ color: '#475569', fontSize: '0.84rem', mt: 0.5 }}>
                      {e.description}
                    </Typography>
                  )}
                </Box>

                <Box>
                  <Button
                    variant="contained"
                    onClick={() => registerEvent(e.id)}
                    sx={{
                      bgcolor: '#00843D',
                      color: '#FFFFFF',
                      fontWeight: 700,
                      borderRadius: 2,
                      textTransform: 'none',
                      boxShadow: 'none',
                      '&:hover': { bgcolor: '#006B31' },
                    }}
                  >
                    Register
                  </Button>
                </Box>
              </Paper>
            );
          })}
        </Box>
      )}

      {/* Facility Booking Dialog */}
      <Dialog open={showBookingModal} onClose={() => setShowBookingModal(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontWeight: 800, color: '#0F172A' }}>Reserve Campus Sports Facility</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, pt: '10px !important' }}>
          <TextField
            select
            label="Sports Facility Venue"
            value={facilityName}
            onChange={(e) => setFacilityName(e.target.value)}
            fullWidth
          >
            <MenuItem value="NSBM Green Stadium">NSBM Green Stadium (Full Grass Oval)</MenuItem>
            <MenuItem value="NSBM Indoor Sports Complex">NSBM Indoor Sports Complex (Court 1 & 2)</MenuItem>
            <MenuItem value="NSBM Olympic Swimming Pool">NSBM Olympic Swimming Pool</MenuItem>
            <MenuItem value="Complex Squash & Badminton Courts">Complex Squash & Badminton Courts</MenuItem>
          </TextField>

          <TextField
            label="Booking Purpose & Objective"
            value={bookingPurpose}
            onChange={(e) => setBookingPurpose(e.target.value)}
            fullWidth
          />

          <TextField
            label="Reservation Start Time"
            type="datetime-local"
            value={bookingStartTime}
            onChange={(e) => setBookingStartTime(e.target.value)}
            slotProps={{ inputLabel: { shrink: true } }}
            fullWidth
          />

          <TextField
            label="Reservation End Time"
            type="datetime-local"
            value={bookingEndTime}
            onChange={(e) => setBookingEndTime(e.target.value)}
            slotProps={{ inputLabel: { shrink: true } }}
            fullWidth
          />
        </DialogContent>
        <DialogActions sx={{ p: 2.5 }}>
          <Button onClick={() => setShowBookingModal(false)} sx={{ color: '#64748B', textTransform: 'none' }}>
            Cancel
          </Button>
          <Button
            onClick={handleCreateBooking}
            variant="contained"
            disabled={submittingBooking}
            sx={{ bgcolor: '#00843D', color: '#FFFFFF', fontWeight: 700, textTransform: 'none', '&:hover': { bgcolor: '#006B31' } }}
          >
            {submittingBooking ? 'Submitting Reservation...' : 'Confirm Reservation'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Team Roster Modal */}
      {selectedTeam && (
        <Dialog open={Boolean(selectedTeam)} onClose={() => setSelectedTeam(null)} maxWidth="md" fullWidth>
          <DialogTitle sx={{ fontWeight: 800, color: '#0F172A', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              {selectedTeam.name}
              <Typography variant="body2" sx={{ color: '#64748B', fontWeight: 500 }}>
                {selectedTeam.division} • Head Coach: {selectedTeam.coach_name || 'Athletics Staff'}
              </Typography>
            </Box>
            <Button onClick={() => setSelectedTeam(null)} sx={{ minWidth: 36, color: '#64748B' }}>
              <CloseIcon />
            </Button>
          </DialogTitle>
          <DialogContent sx={{ pt: '10px !important' }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1.5, color: '#1E293B' }}>
              Registered Varsity Roster
            </Typography>
            <TableContainer component={Paper} elevation={0} sx={{ border: '1px solid #E2E8F0', borderRadius: 2 }}>
              <Table size="small">
                <TableHead sx={{ bgcolor: '#F8FAFC' }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>#</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Athlete Name</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Position / Role</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Fitness Status</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Matches Played</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {selectedTeam.roster && selectedTeam.roster.length > 0 ? (
                    selectedTeam.roster.map((ath) => (
                      <TableRow key={ath.id}>
                        <TableCell sx={{ fontWeight: 700 }}>{ath.jersey_number || '—'}</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>{ath.student_name || `Athlete #${ath.student_id}`}</TableCell>
                        <TableCell>{ath.position_or_role}</TableCell>
                        <TableCell>
                          <Chip
                            label={ath.fitness_status.toUpperCase()}
                            size="small"
                            sx={{
                              bgcolor: ath.fitness_status === 'fit' ? 'rgba(0,132,61,0.1)' : 'rgba(239,68,68,0.1)',
                              color: ath.fitness_status === 'fit' ? '#00843D' : '#EF4444',
                              fontWeight: 700,
                              fontSize: '0.68rem',
                            }}
                          />
                        </TableCell>
                        <TableCell>{ath.matches_played} matches</TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={5} sx={{ textAlign: 'center', py: 3, color: '#64748B' }}>
                        Active roster records undergoing SLUG registration clearance.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </DialogContent>
        </Dialog>
      )}
    </Box>
  );
}
