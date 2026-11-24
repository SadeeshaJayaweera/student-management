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
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
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
  CircularProgress,
  IconButton,
  Tooltip,
  FormControlLabel,
  Checkbox,
} from '@mui/material';
import AutoStoriesIcon from '@mui/icons-material/AutoStories';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import BookmarkIcon from '@mui/icons-material/Bookmark';
import BookmarkBorderIcon from '@mui/icons-material/BookmarkBorder';
import DownloadIcon from '@mui/icons-material/Download';
import VisibilityIcon from '@mui/icons-material/Visibility';
import AddCircleIcon from '@mui/icons-material/AddCircle';
import SearchIcon from '@mui/icons-material/Search';
import CloseIcon from '@mui/icons-material/Close';
import api from '@/api/client';
import toast from 'react-hot-toast';
import type {
  Book,
  BorrowRecord,
  Paginated,
  DigitalLibraryResource,
  LibrarySubjectCollection,
  LibraryBookmark,
  DigitalLibraryStats,
} from '@/types';
import { useAuth } from '@/contexts/AuthContext';

const BOOK_EMOJI: Record<string, string> = {
  'Computer Science': '💻',
  'AI/ML': '🤖',
  Business: '💼',
  Engineering: '⚙️',
  Databases: '🗄️',
  Networking: '🌐',
  'Data Science': '📊',
  'Software Engineering': '🔧',
  Mathematics: '📐',
  Physics: '⚗️',
};

const RESOURCE_ICONS: Record<string, string> = {
  ebook: '📘',
  research_paper: '📑',
  journal_article: '📄',
  thesis: '🎓',
  video_lecture: '🎥',
  audio_resource: '🎧',
};

export default function Library() {
  const { user } = useAuth();
  const isLibrarianOrAdmin = user?.role === 'librarian' || user?.role === 'admin';

  // Active Tab: 0 = Digital, 1 = Physical Books, 2 = Reading List
  const [activeTab, setActiveTab] = useState<number>(0);

  // Physical Books
  const [books, setBooks] = useState<Book[]>([]);
  const [total, setTotal] = useState(0);
  const [borrows, setBorrows] = useState<BorrowRecord[]>([]);
  const [categories, setCategories] = useState<{ category: string; count: number }[]>([]);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [availableOnly, setAvailableOnly] = useState(false);

  // Digital Repository
  const [digitalResources, setDigitalResources] = useState<DigitalLibraryResource[]>([]);
  const [digitalType, setDigitalType] = useState<string>('all');
  const [digitalFormat, setDigitalFormat] = useState<string>('all');
  const [digitalQuery, setDigitalQuery] = useState<string>('');
  const [collections, setCollections] = useState<LibrarySubjectCollection[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<number | null>(null);
  const [bookmarks, setBookmarks] = useState<LibraryBookmark[]>([]);
  const [stats, setStats] = useState<DigitalLibraryStats | null>(null);

  // Modals & previews
  const [loading, setLoading] = useState(true);
  const [previewResource, setPreviewResource] = useState<DigitalLibraryResource | null>(null);
  const [showAddModal, setShowAddModal] = useState<boolean>(false);

  // New digital resource form
  const [newTitle, setNewTitle] = useState('');
  const [newAuthor, setNewAuthor] = useState('');
  const [newType, setNewType] = useState('ebook');
  const [newCategory, setNewCategory] = useState('Computer Science');
  const [newFormat, setNewFormat] = useState('pdf');
  const [newUrl, setNewUrl] = useState('');
  const [newAbstract, setNewAbstract] = useState('');
  const [newYear, setNewYear] = useState<number>(2026);
  const [savingResource, setSavingResource] = useState(false);

  const fetchBooks = async (s = search, c = category, a = availableOnly) => {
    const params = new URLSearchParams({ page: '1', size: '12' });
    if (s) params.set('search', s);
    if (c) params.set('category', c);
    if (a) params.set('available_only', 'true');
    try {
      const r = await api.get<Paginated<Book>>(`/library/catalog?${params}`);
      setBooks(r.data.items);
      setTotal(r.data.total);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchDigitalResources = async () => {
    try {
      const params = new URLSearchParams({ limit: '30' });
      if (digitalQuery) params.set('query', digitalQuery);
      if (digitalType && digitalType !== 'all') params.set('resource_type', digitalType);
      if (digitalFormat && digitalFormat !== 'all') params.set('file_format', digitalFormat);
      if (selectedCollection) params.set('collection_id', String(selectedCollection));

      const [resR, colR, statsR] = await Promise.all([
        api.get<DigitalLibraryResource[]>(`/digital-library/catalog?${params}`),
        api.get<LibrarySubjectCollection[]>('/digital-library/collections'),
        api.get<DigitalLibraryStats>('/digital-library/stats'),
      ]);
      setDigitalResources(resR.data);
      setCollections(colR.data);
      setStats(statsR.data);
    } catch (e) {
      console.error('Failed to load digital resources', e);
    }
  };

  const fetchBookmarks = async () => {
    try {
      const r = await api.get<LibraryBookmark[]>('/digital-library/my-bookmarks');
      setBookmarks(r.data);
    } catch (e) {
      console.error('Failed to load bookmarks', e);
    }
  };

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchBooks(),
      fetchDigitalResources(),
      fetchBookmarks(),
      api.get<{ category: string; count: number }[]>('/library/categories').then((r) => setCategories(r.data)).catch(() => {}),
      user?.role === 'student'
        ? api.get<BorrowRecord[]>('/library/my-borrows').then((r) => setBorrows(r.data)).catch(() => {})
        : Promise.resolve(),
    ]).finally(() => setLoading(false));
  }, []);

  const handleBorrow = async (bookId: number, title: string) => {
    try {
      const r = await api.post<{ message: string }>(`/library/borrow/${bookId}`);
      toast.success(`📚 ${r.data.message}`);
      fetchBooks();
      api.get<BorrowRecord[]>('/library/my-borrows').then((res) => setBorrows(res.data)).catch(() => {});
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Cannot borrow');
    }
  };

  const handleRenew = async (borrowId: number) => {
    try {
      await api.post(`/circulation/renew/${borrowId}`);
      toast.success('Book loan renewed for an additional 14 days!');
      api.get<BorrowRecord[]>('/library/my-borrows').then((res) => setBorrows(res.data)).catch(() => {});
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Cannot renew loan.');
    }
  };

  const handleReturn = async (borrowId: number) => {
    try {
      await api.post(`/circulation/return/${borrowId}`);
      toast.success('Book returned successfully!');
      fetchBooks();
      api.get<BorrowRecord[]>('/library/my-borrows').then((res) => setBorrows(res.data)).catch(() => {});
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to process return.');
    }
  };

  const handleReserve = async (bookId: number) => {
    try {
      const res = await api.post<{ priority_number: number }>(`/circulation/reserve/${bookId}`);
      toast.success(`Book reserved! You are priority #${res.data.priority_number} in queue.`);
    } catch (e: any) {
      toast.error(e.response?.data?.detail || 'Failed to place reservation.');
    }
  };

  const handleBookmarkToggle = async (resourceId: number) => {
    try {
      const res = await api.post<{ bookmarked: boolean; message: string }>(`/digital-library/catalog/${resourceId}/bookmark`);
      toast.success(res.data.message);
      setDigitalResources((prev) =>
        prev.map((r) => (r.id === resourceId ? { ...r, is_bookmarked: res.data.bookmarked } : r))
      );
      fetchBookmarks();
    } catch {
      toast.error('Failed to update bookmark');
    }
  };

  const handleDownload = async (resourceId: number, url: string, title: string) => {
    try {
      await api.post(`/digital-library/catalog/${resourceId}/download`);
      toast.success(`Downloading ${title}`);
      setDigitalResources((prev) =>
        prev.map((r) => (r.id === resourceId ? { ...r, download_count: r.download_count + 1 } : r))
      );
      window.open(url, '_blank');
    } catch {
      window.open(url, '_blank');
    }
  };

  const handleViewPreview = async (res: DigitalLibraryResource) => {
    try {
      const updated = await api.get<DigitalLibraryResource>(`/digital-library/catalog/${res.id}`);
      setPreviewResource(updated.data);
      setDigitalResources((prev) =>
        prev.map((r) => (r.id === res.id ? { ...r, view_count: updated.data.view_count } : r))
      );
    } catch {
      setPreviewResource(res);
    }
  };

  const handleCreateResource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newAuthor.trim() || !newUrl.trim() || savingResource) return;

    try {
      setSavingResource(true);
      await api.post('/digital-library/catalog', {
        title: newTitle.trim(),
        author: newAuthor.trim(),
        resource_type: newType,
        subject_category: newCategory,
        file_format: newFormat,
        file_url: newUrl.trim(),
        abstract: newAbstract.trim() || undefined,
        published_year: newYear,
        is_open_access: true,
      });
      toast.success('Digital asset published successfully!');
      setShowAddModal(false);
      fetchDigitalResources();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to publish resource.');
    } finally {
      setSavingResource(false);
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
              <AutoStoriesIcon sx={{ fontSize: 26 }} />
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#0F172A', letterSpacing: '-0.02em' }}>
              NSBM Modern Digital Library & Knowledge Repository
            </Typography>
          </Box>
          <Typography variant="body2" sx={{ color: '#64748B', maxWidth: 700, mt: 0.5 }}>
            Academic physical library collection, peer-reviewed research papers, open-access e-books, and digital thesis repository.
          </Typography>
        </Box>

        {isLibrarianOrAdmin && (
          <Button
            variant="contained"
            onClick={() => setShowAddModal(true)}
            startIcon={<AddCircleIcon />}
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
            Publish Digital Asset
          </Button>
        )}
      </Paper>

      {/* KPI Stats */}
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
          <Box sx={{ width: 48, height: 48, borderRadius: 2, bgcolor: 'rgba(99,102,241,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem' }}>
            📚
          </Box>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#6366F1' }}>
              {(stats?.total_resources || 0) + total}
            </Typography>
            <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
              Catalog Holdings
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
          <Box sx={{ width: 48, height: 48, borderRadius: 2, bgcolor: 'rgba(0,132,61,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem' }}>
            👁
          </Box>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#00843D' }}>
              {stats?.total_views || 240}
            </Typography>
            <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
              Repository Views
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
            ⬇
          </Box>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#EF4444' }}>
              {stats?.total_downloads || 86}
            </Typography>
            <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
              Downloads & Reads
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
            🔖
          </Box>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#F59E0B' }}>
              {bookmarks.length}
            </Typography>
            <Typography variant="caption" sx={{ color: '#64748B', fontWeight: 600, textTransform: 'uppercase' }}>
              My Reading List
            </Typography>
          </Box>
        </Paper>
      </Box>

      {/* Tabs */}
      <Paper elevation={0} sx={{ borderBottom: '1px solid #E2E8F0', bgcolor: 'transparent' }}>
        <Tabs
          value={activeTab}
          onChange={(_, val) => setActiveTab(val)}
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
          <Tab icon={<AutoStoriesIcon sx={{ fontSize: 18, mr: 0.5 }} />} iconPosition="start" label={`Digital Repository & E-Books (${digitalResources.length})`} />
          <Tab icon={<MenuBookIcon sx={{ fontSize: 18, mr: 0.5 }} />} iconPosition="start" label={`Physical Library Catalog (${total})`} />
          <Tab icon={<BookmarkIcon sx={{ fontSize: 18, mr: 0.5 }} />} iconPosition="start" label={`Saved Reading List (${bookmarks.length})`} />
        </Tabs>
      </Paper>

      {/* TAB 0: Digital Repository */}
      {activeTab === 0 && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Collections Pill Drawer */}
          {collections.length > 0 && (
            <Box sx={{ display: 'flex', gap: 1, overflowX: 'auto', pb: 0.5 }}>
              <Chip
                label="All Subject Collections"
                clickable
                onClick={() => { setSelectedCollection(null); fetchDigitalResources(); }}
                sx={{
                  fontWeight: 700,
                  fontSize: '0.8rem',
                  bgcolor: selectedCollection === null ? 'rgba(0,132,61,0.1)' : '#FFFFFF',
                  color: selectedCollection === null ? '#00843D' : '#64748B',
                  border: selectedCollection === null ? '1.5px solid #00843D' : '1px solid #E2E8F0',
                }}
              />
              {collections.map((c) => (
                <Chip
                  key={c.id}
                  label={`${c.icon} ${c.title}`}
                  clickable
                  onClick={() => { setSelectedCollection(c.id); fetchDigitalResources(); }}
                  sx={{
                    fontWeight: 700,
                    fontSize: '0.8rem',
                    bgcolor: selectedCollection === c.id ? 'rgba(0,132,61,0.1)' : '#FFFFFF',
                    color: selectedCollection === c.id ? '#00843D' : '#64748B',
                    border: selectedCollection === c.id ? '1.5px solid #00843D' : '1px solid #E2E8F0',
                  }}
                />
              ))}
            </Box>
          )}

          {/* Search and Filters Bar */}
          <Paper
            elevation={0}
            sx={{
              p: 2.5,
              borderRadius: 3,
              border: '1px solid #E2E8F0',
              bgcolor: '#FFFFFF',
              display: 'flex',
              gap: 2,
              flexWrap: 'wrap',
              alignItems: 'center',
            }}
          >
            <TextField
              size="small"
              placeholder="Search papers, e-books, theses, keywords..."
              value={digitalQuery}
              onChange={(e) => setDigitalQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && fetchDigitalResources()}
              sx={{ flex: 1, minWidth: 260 }}
              slotProps={{
                input: {
                  startAdornment: <SearchIcon sx={{ color: '#94A3B8', mr: 1, fontSize: 20 }} />,
                },
              }}
            />

            <FormControl size="small" sx={{ minWidth: 160 }}>
              <InputLabel>Resource Type</InputLabel>
              <Select
                value={digitalType}
                label="Resource Type"
                onChange={(e) => setDigitalType(e.target.value)}
              >
                <MenuItem value="all">All Types</MenuItem>
                <MenuItem value="ebook">E-Books</MenuItem>
                <MenuItem value="research_paper">Research Papers</MenuItem>
                <MenuItem value="journal_article">Journal Articles</MenuItem>
                <MenuItem value="thesis">Theses & Dissertations</MenuItem>
                <MenuItem value="video_lecture">Video Lectures</MenuItem>
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 140 }}>
              <InputLabel>File Format</InputLabel>
              <Select
                value={digitalFormat}
                label="File Format"
                onChange={(e) => setDigitalFormat(e.target.value)}
              >
                <MenuItem value="all">All Formats</MenuItem>
                <MenuItem value="pdf">PDF Document</MenuItem>
                <MenuItem value="epub">ePub Book</MenuItem>
                <MenuItem value="mp4">MP4 Video</MenuItem>
              </Select>
            </FormControl>

            <Button
              variant="contained"
              onClick={fetchDigitalResources}
              sx={{
                bgcolor: '#00843D',
                color: '#FFFFFF',
                fontWeight: 700,
                textTransform: 'none',
                borderRadius: 2,
                px: 3,
                boxShadow: 'none',
                '&:hover': { bgcolor: '#006B31' },
              }}
            >
              Filter Catalog
            </Button>
          </Paper>

          {/* Digital Resources Grid */}
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' },
              gap: 3,
            }}
          >
            {digitalResources.map((res) => {
              const icon = RESOURCE_ICONS[res.resource_type] || '📄';
              return (
                <Card
                  key={res.id}
                  elevation={0}
                  sx={{
                    borderRadius: 3,
                    border: '1px solid #E2E8F0',
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'all 0.15s ease-in-out',
                    '&:hover': { borderColor: '#CBD5E1', boxShadow: '0 4px 14px rgba(0,0,0,0.05)' },
                  }}
                >
                  <Box
                    sx={{
                      height: 120,
                      bgcolor: 'rgba(0,132,61,0.06)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '3rem',
                      position: 'relative',
                    }}
                  >
                    <span>{icon}</span>
                    <IconButton
                      size="small"
                      onClick={() => handleBookmarkToggle(res.id)}
                      sx={{
                        position: 'absolute',
                        top: 8,
                        right: 8,
                        bgcolor: 'rgba(255,255,255,0.85)',
                        '&:hover': { bgcolor: '#FFFFFF' },
                      }}
                    >
                      {res.is_bookmarked ? (
                        <BookmarkIcon sx={{ color: '#F59E0B', fontSize: 18 }} />
                      ) : (
                        <BookmarkBorderIcon sx={{ color: '#64748B', fontSize: 18 }} />
                      )}
                    </IconButton>
                    <Chip
                      label={`${res.file_format?.toUpperCase()} • ${res.resource_type?.replace('_', ' ')}`}
                      size="small"
                      sx={{
                        position: 'absolute',
                        bottom: 8,
                        left: 8,
                        bgcolor: '#FFFFFF',
                        fontWeight: 700,
                        fontSize: '0.68rem',
                        border: '1px solid #E2E8F0',
                        color: '#00843D',
                      }}
                    />
                  </Box>

                  <CardContent sx={{ p: 2.5, flex: 1, display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0F172A', lineHeight: 1.3 }}>
                      {res.title}
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#64748B' }}>
                      by {res.author} {res.published_year ? `(${res.published_year})` : ''}
                    </Typography>
                    {res.abstract && (
                      <Typography
                        variant="body2"
                        sx={{
                          color: '#475569',
                          fontSize: '0.82rem',
                          lineHeight: 1.4,
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                          mt: 0.5,
                        }}
                      >
                        {res.abstract}
                      </Typography>
                    )}

                    <Box sx={{ mt: 'auto', pt: 1.5, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Chip label={res.subject_category} size="small" sx={{ bgcolor: '#F1F5F9', fontSize: '0.7rem', fontWeight: 600 }} />
                      <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                        👁 {res.view_count} · ⬇ {res.download_count}
                      </Typography>
                    </Box>
                  </CardContent>

                  <CardActions sx={{ p: 2.5, pt: 0, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => handleViewPreview(res)}
                      startIcon={<VisibilityIcon sx={{ fontSize: 16 }} />}
                      sx={{
                        borderColor: '#E2E8F0',
                        color: '#0F172A',
                        fontWeight: 700,
                        textTransform: 'none',
                        borderRadius: 2,
                        '&:hover': { borderColor: '#00843D', color: '#00843D' },
                      }}
                    >
                      Preview
                    </Button>
                    <Button
                      variant="contained"
                      size="small"
                      onClick={() => handleDownload(res.id, res.file_url, res.title)}
                      startIcon={<DownloadIcon sx={{ fontSize: 16 }} />}
                      sx={{
                        bgcolor: '#00843D',
                        color: '#FFFFFF',
                        fontWeight: 700,
                        textTransform: 'none',
                        borderRadius: 2,
                        boxShadow: 'none',
                        '&:hover': { bgcolor: '#006B31' },
                      }}
                    >
                      Download
                    </Button>
                  </CardActions>
                </Card>
              );
            })}
          </Box>
        </Box>
      )}

      {/* TAB 1: Physical Library */}
      {activeTab === 1 && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Search bar */}
          <Paper
            elevation={0}
            sx={{
              p: 2.5,
              borderRadius: 3,
              border: '1px solid #E2E8F0',
              bgcolor: '#FFFFFF',
              display: 'flex',
              gap: 2,
              flexWrap: 'wrap',
              alignItems: 'center',
            }}
          >
            <TextField
              size="small"
              placeholder="Search title, author, ISBN..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && fetchBooks(search, category, availableOnly)}
              sx={{ flex: 1, minWidth: 240 }}
            />

            <FormControl size="small" sx={{ minWidth: 180 }}>
              <InputLabel>Category</InputLabel>
              <Select
                value={category}
                label="Category"
                onChange={(e) => {
                  setCategory(e.target.value);
                  fetchBooks(search, e.target.value, availableOnly);
                }}
              >
                <MenuItem value="">All Categories</MenuItem>
                {categories.map((c) => (
                  <MenuItem key={c.category} value={c.category}>
                    {c.category} ({c.count})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControlLabel
              control={
                <Checkbox
                  checked={availableOnly}
                  onChange={(e) => {
                    setAvailableOnly(e.target.checked);
                    fetchBooks(search, category, e.target.checked);
                  }}
                  sx={{ color: '#00843D', '&.Mui-checked': { color: '#00843D' } }}
                />
              }
              label={<Typography variant="body2" sx={{ fontWeight: 600 }}>Available Only</Typography>}
            />

            <Button
              variant="contained"
              onClick={() => fetchBooks(search, category, availableOnly)}
              sx={{
                bgcolor: '#00843D',
                color: '#FFFFFF',
                fontWeight: 700,
                textTransform: 'none',
                borderRadius: 2,
                px: 3,
                boxShadow: 'none',
                '&:hover': { bgcolor: '#006B31' },
              }}
            >
              Search Catalog
            </Button>
          </Paper>

          {/* Book Cards Grid */}
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(4, 1fr)' },
              gap: 3,
            }}
          >
            {books.map((b) => {
              const emoji = BOOK_EMOJI[b.category] || '📖';
              const available = b.available_copies > 0;
              return (
                <Card
                  key={b.id}
                  elevation={0}
                  sx={{
                    borderRadius: 3,
                    border: '1px solid #E2E8F0',
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'all 0.15s ease-in-out',
                    '&:hover': { borderColor: '#CBD5E1', boxShadow: '0 4px 14px rgba(0,0,0,0.05)' },
                  }}
                >
                  <Box
                    sx={{
                      height: 130,
                      bgcolor: 'rgba(0,132,61,0.08)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '3.2rem',
                    }}
                  >
                    {emoji}
                  </Box>

                  <CardContent sx={{ p: 2, flex: 1, display: 'flex', flexDirection: 'column', gap: 0.8 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#0F172A', lineHeight: 1.3 }}>
                      {b.title}
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#64748B' }}>
                      by {b.author}
                    </Typography>
                    {b.year && (
                      <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                        {b.publisher} · {b.year}
                      </Typography>
                    )}

                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 0.5 }}>
                      <Chip
                        label={available ? 'Available' : 'Borrowed'}
                        size="small"
                        sx={{
                          height: 20,
                          fontSize: '0.68rem',
                          fontWeight: 700,
                          bgcolor: available ? 'rgba(0,132,61,0.1)' : 'rgba(239,68,68,0.1)',
                          color: available ? '#00843D' : '#EF4444',
                        }}
                      />
                      <Chip label={b.category} size="small" sx={{ height: 20, fontSize: '0.68rem', bgcolor: '#F1F5F9' }} />
                    </Box>

                    <Typography variant="caption" sx={{ color: '#64748B', mt: 'auto', pt: 0.5 }}>
                      {b.available_copies}/{b.total_copies} copies · {b.location || 'NSBM Main Library'}
                    </Typography>
                  </CardContent>

                  <CardActions sx={{ p: 2, pt: 0 }}>
                    {available ? (
                      <Button
                        variant="contained"
                        fullWidth
                        size="small"
                        onClick={() => handleBorrow(b.id, b.title)}
                        sx={{
                          bgcolor: '#00843D',
                          color: '#FFFFFF',
                          fontWeight: 700,
                          textTransform: 'none',
                          borderRadius: 2,
                          boxShadow: 'none',
                          '&:hover': { bgcolor: '#006B31' },
                        }}
                      >
                        Borrow Book
                      </Button>
                    ) : (
                      <Button
                        variant="outlined"
                        fullWidth
                        size="small"
                        onClick={() => handleReserve(b.id)}
                        sx={{
                          borderColor: '#E2E8F0',
                          color: '#475569',
                          fontWeight: 700,
                          textTransform: 'none',
                          borderRadius: 2,
                          '&:hover': { borderColor: '#CBD5E1' },
                        }}
                      >
                        Reserve in Queue
                      </Button>
                    )}
                  </CardActions>
                </Card>
              );
            })}
          </Box>

          {/* Active Borrows Table */}
          {borrows.length > 0 && (
            <Paper elevation={0} sx={{ p: 3, borderRadius: 3, border: '1px solid #E2E8F0', bgcolor: '#FFFFFF' }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0F172A', mb: 2 }}>
                My Active Borrowings & Loans
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead sx={{ bgcolor: '#F8FAFC' }}>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 700 }}>Book Title</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Author</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Borrowed On</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Due Date</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                      <TableCell sx={{ fontWeight: 700, textAlign: 'right' }}>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {borrows.map((b) => (
                      <TableRow key={b.id}>
                        <TableCell sx={{ fontWeight: 700, color: '#0F172A' }}>{b.book}</TableCell>
                        <TableCell sx={{ color: '#64748B' }}>{b.author}</TableCell>
                        <TableCell>{new Date(b.borrowed_at).toLocaleDateString()}</TableCell>
                        <TableCell>{new Date(b.due_date).toLocaleDateString()}</TableCell>
                        <TableCell>
                          <Chip
                            label={b.status.toUpperCase()}
                            size="small"
                            sx={{
                              bgcolor: b.status === 'active' ? 'rgba(0,132,61,0.1)' : 'rgba(239,68,68,0.1)',
                              color: b.status === 'active' ? '#00843D' : '#EF4444',
                              fontWeight: 700,
                              fontSize: '0.68rem',
                            }}
                          />
                        </TableCell>
                        <TableCell sx={{ textAlign: 'right' }}>
                          <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                            {b.status === 'active' && (
                              <Button
                                size="small"
                                variant="outlined"
                                onClick={() => handleRenew(b.id)}
                                sx={{ textTransform: 'none', fontWeight: 700, borderRadius: 1.5 }}
                              >
                                Renew
                              </Button>
                            )}
                            <Button
                              size="small"
                              variant="contained"
                              onClick={() => handleReturn(b.id)}
                              sx={{
                                bgcolor: '#00843D',
                                color: '#FFFFFF',
                                textTransform: 'none',
                                fontWeight: 700,
                                borderRadius: 1.5,
                                boxShadow: 'none',
                                '&:hover': { bgcolor: '#006B31' },
                              }}
                            >
                              Return
                            </Button>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}
        </Box>
      )}

      {/* TAB 2: Reading List */}
      {activeTab === 2 && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {bookmarks.length === 0 ? (
            <Paper elevation={0} sx={{ p: 6, borderRadius: 3, border: '1px solid #E2E8F0', textAlign: 'center' }}>
              <Typography sx={{ fontSize: '3rem', mb: 1 }}>🔖</Typography>
              <Typography variant="h6" sx={{ fontWeight: 800, color: '#0F172A' }}>
                Your Reading List is Empty
              </Typography>
              <Typography variant="body2" sx={{ color: '#64748B', mt: 0.5 }}>
                Save digital research papers, articles, and e-books from the Digital Repository to read later.
              </Typography>
            </Paper>
          ) : (
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' },
                gap: 3,
              }}
            >
              {bookmarks.map((bm) => (
                <Card
                  key={bm.id}
                  elevation={0}
                  sx={{
                    borderRadius: 3,
                    border: '1px solid #E2E8F0',
                    display: 'flex',
                    flexDirection: 'column',
                  }}
                >
                  <CardContent sx={{ p: 2.5, flex: 1, display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 800, color: '#0F172A' }}>
                      {bm.resource?.title}
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#64748B' }}>
                      by {bm.resource?.author}
                    </Typography>
                    {bm.resource?.abstract && (
                      <Typography variant="body2" sx={{ color: '#475569', fontSize: '0.82rem', mt: 0.5 }}>
                        {bm.resource.abstract}
                      </Typography>
                    )}
                  </CardContent>
                  <CardActions sx={{ p: 2.5, pt: 0 }}>
                    <Button
                      variant="contained"
                      fullWidth
                      onClick={() => handleViewPreview(bm.resource)}
                      sx={{
                        bgcolor: '#00843D',
                        color: '#FFFFFF',
                        fontWeight: 700,
                        textTransform: 'none',
                        borderRadius: 2,
                        boxShadow: 'none',
                        '&:hover': { bgcolor: '#006B31' },
                      }}
                    >
                      Read Now
                    </Button>
                  </CardActions>
                </Card>
              ))}
            </Box>
          )}
        </Box>
      )}

      {/* Preview Dialog */}
      {previewResource && (
        <Dialog open={Boolean(previewResource)} onClose={() => setPreviewResource(null)} maxWidth="md" fullWidth>
          <DialogTitle sx={{ fontWeight: 800, color: '#0F172A', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Chip
                label={`${previewResource.resource_type.replace('_', ' ')} • ${previewResource.file_format}`}
                size="small"
                sx={{ bgcolor: 'rgba(0,132,61,0.1)', color: '#00843D', fontWeight: 700, mb: 0.5 }}
              />
              <Typography variant="h6" sx={{ fontWeight: 800 }}>{previewResource.title}</Typography>
              <Typography variant="caption" sx={{ color: '#64748B' }}>
                by {previewResource.author} • {previewResource.publisher || 'NSBM Academic Press'} ({previewResource.published_year})
              </Typography>
            </Box>
            <IconButton onClick={() => setPreviewResource(null)}>
              <CloseIcon />
            </IconButton>
          </DialogTitle>
          <DialogContent dividers sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#0F172A' }}>
              Abstract & Executive Summary
            </Typography>
            <Typography variant="body2" sx={{ color: '#334155', lineHeight: 1.6 }}>
              {previewResource.abstract || 'No extended abstract provided for this asset.'}
            </Typography>
          </DialogContent>
          <DialogActions sx={{ p: 2.5 }}>
            <Button onClick={() => setPreviewResource(null)} sx={{ color: '#64748B', textTransform: 'none' }}>
              Close
            </Button>
            <Button
              variant="contained"
              onClick={() => handleDownload(previewResource.id, previewResource.file_url, previewResource.title)}
              startIcon={<DownloadIcon />}
              sx={{ bgcolor: '#00843D', color: '#FFFFFF', fontWeight: 700, textTransform: 'none', '&:hover': { bgcolor: '#006B31' } }}
            >
              Download Full Asset
            </Button>
          </DialogActions>
        </Dialog>
      )}
    </Box>
  );
}
