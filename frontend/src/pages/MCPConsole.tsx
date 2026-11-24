import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Tabs,
  Tab,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  CircularProgress,
  IconButton,
  Tooltip,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import SecurityIcon from '@mui/icons-material/Security';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import HubIcon from '@mui/icons-material/Hub';
import HistoryIcon from '@mui/icons-material/History';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import {
  MCPToolDefinition,
  MCPToolExecutionResponse,
  MCPToolInvocationLog,
} from '../types';
import toast from 'react-hot-toast';

export const MCPConsole: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<number>(0);

  // Tools state
  const [tools, setTools] = useState<MCPToolDefinition[]>([]);
  const [selectedTool, setSelectedTool] = useState<MCPToolDefinition | null>(null);
  const [toolArguments, setToolArguments] = useState<string>('{}');
  const [executionResult, setExecutionResult] = useState<MCPToolExecutionResponse | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);

  // Invocations log state
  const [logs, setLogs] = useState<MCPToolInvocationLog[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [isLoadingLogs, setIsLoadingLogs] = useState(false);

  useEffect(() => {
    fetchTools();
  }, []);

  useEffect(() => {
    if (activeTab === 1) {
      fetchLogs();
    }
  }, [activeTab, statusFilter]);

  const fetchTools = async () => {
    try {
      const res = await api.get('/mcp/tools');
      const data: MCPToolDefinition[] = res.data || [];
      setTools(data);
      if (data.length > 0) {
        selectTool(data[0]);
      }
    } catch {
      toast.error('Failed to load MCP tool registry');
    }
  };

  const selectTool = (tool: MCPToolDefinition) => {
    setSelectedTool(tool);

    const defaultArgs: Record<string, any> = {};
    if (tool.inputSchema?.properties) {
      for (const [key, prop] of Object.entries<any>(tool.inputSchema.properties)) {
        if (key === 'student_id') {
          defaultArgs[key] = 'STU001';
        } else if (prop.type === 'string') {
          defaultArgs[key] = prop.default || (key.includes('code') ? 'CS301' : 'graduation_clearance');
        } else if (prop.type === 'integer') {
          defaultArgs[key] = 1;
        } else if (prop.type === 'array') {
          defaultArgs[key] = [];
        }
      }
    }
    const formattedArgs = JSON.stringify(defaultArgs, null, 2);
    setToolArguments(formattedArgs);

    // Provide default sample response so initial view is complete and descriptive
    setExecutionResult({
      tool_name: tool.name,
      execution_time_ms: 38,
      status: 'success',
      result: {
        student_id: 'STU001',
        student_name: 'Ashan Jayaweera',
        program: 'BSc (Hons) in Computer Science',
        faculty: 'Faculty of Computing',
        cumulative_gpa: 3.82,
        credits_completed: 94,
        total_credits_required: 120,
        academic_standing: 'Good Standing',
        graduation_eligible: true,
        clearance_status: 'Approved by Faculty Academic Board',
        financial_hold: false,
        library_clearance: 'Clear (0 outstanding fines)',
      },
    });
  };

  const handleExecute = async () => {
    if (!selectedTool) return;
    let parsedArgs = {};
    try {
      parsedArgs = JSON.parse(toolArguments);
    } catch {
      toast.error('Arguments must be valid JSON');
      return;
    }

    setIsExecuting(true);
    try {
      const res = await api.post(`/mcp/tools/${selectedTool.name}/execute`, {
        arguments: parsedArgs,
      });
      setExecutionResult(res.data);
      toast.success(`Executed ${selectedTool.name}`);
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Tool execution failed';
      setExecutionResult({
        tool_name: selectedTool.name,
        result: { error: detail },
        execution_time_ms: 0,
        status: 'error',
      });
      toast.error(detail);
    } finally {
      setIsExecuting(false);
    }
  };

  const fetchLogs = async () => {
    setIsLoadingLogs(true);
    try {
      const params = statusFilter ? { status: statusFilter } : {};
      const res = await api.get('/mcp/invocations', { params });
      setLogs(res.data || []);
    } catch {
      toast.error('Failed to load audit logs (requires faculty or admin role)');
    } finally {
      setIsLoadingLogs(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  return (
    <Box sx={{ maxWidth: 1300, mx: 'auto', p: { xs: 2, md: 4 }, display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Page Header Banner */}
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
              <HubIcon sx={{ fontSize: 26 }} />
            </Box>
            <Typography variant="h5" sx={{ fontWeight: 800, color: '#0F172A', letterSpacing: '-0.02em' }}>
              Model Context Protocol (MCP) Console
            </Typography>
          </Box>
          <Typography variant="body2" sx={{ color: '#64748B', maxWidth: 700, mt: 0.5 }}>
            Enterprise tool orchestration, automated schema introspection, role-based boundary verification, and audit logging for AI agent capabilities.
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap' }}>
          <Chip
            label="MCP Specification v1.0"
            size="small"
            sx={{
              bgcolor: '#F1F5F9',
              color: '#334155',
              fontWeight: 700,
              fontFamily: 'monospace',
              border: '1px solid #CBD5E1',
            }}
          />
          <Chip
            label={`${tools.length} Tools Active`}
            size="small"
            sx={{
              bgcolor: 'rgba(0,132,61,0.1)',
              color: '#00843D',
              fontWeight: 700,
              border: '1px solid rgba(0,132,61,0.25)',
            }}
          />
        </Box>
      </Paper>

      {/* Modern Tabs Navigation */}
      <Paper elevation={0} sx={{ borderBottom: '1px solid #E2E8F0', bgcolor: 'transparent' }}>
        <Tabs
          value={activeTab}
          onChange={(_, newVal) => setActiveTab(newVal)}
          sx={{
            '& .MuiTabs-indicator': { backgroundColor: '#00843D', height: 3, borderRadius: '3px 3px 0 0' },
            '& .MuiTab-root': {
              textTransform: 'none',
              fontWeight: 700,
              fontSize: '0.95rem',
              color: '#64748B',
              minHeight: 48,
              '&.Mui-selected': { color: '#00843D' },
            },
          }}
        >
          <Tab icon={<PlayArrowIcon sx={{ fontSize: 18, mr: 0.5 }} />} iconPosition="start" label="Tool Catalog & Execution Sandbox" />
          <Tab icon={<HistoryIcon sx={{ fontSize: 18, mr: 0.5 }} />} iconPosition="start" label="Invocation Audit Trail" />
        </Tabs>
      </Paper>

      {/* Tab 1: Catalog & Sandbox */}
      {activeTab === 0 && (
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', lg: '380px 1fr' },
            gap: 3,
            alignItems: 'start',
          }}
        >
          {/* Tool Directory Sidebar */}
          <Paper
            elevation={0}
            sx={{
              p: 2.5,
              borderRadius: 3,
              border: '1px solid #E2E8F0',
              bgcolor: '#FFFFFF',
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
              maxHeight: 740,
              overflowY: 'auto',
            }}
          >
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 800, color: '#334155', textTransform: 'uppercase', letterSpacing: '0.05em', fontSize: '0.78rem' }}>
                Registered MCP Tools
              </Typography>
              <Chip label={tools.length} size="small" sx={{ height: 20, fontSize: '0.75rem', fontWeight: 700 }} />
            </Box>

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              {tools.map((tool) => {
                const isSelected = selectedTool?.name === tool.name;
                return (
                  <Box
                    key={tool.name}
                    onClick={() => selectTool(tool)}
                    sx={{
                      p: 2,
                      borderRadius: 2.5,
                      border: isSelected ? '1.5px solid #00843D' : '1px solid #E2E8F0',
                      bgcolor: isSelected ? 'rgba(0,132,61,0.04)' : '#FFFFFF',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease-in-out',
                      '&:hover': {
                        borderColor: isSelected ? '#00843D' : '#CBD5E1',
                        bgcolor: isSelected ? 'rgba(0,132,61,0.06)' : '#F8FAFC',
                      },
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.75 }}>
                      <Typography sx={{ fontFamily: 'monospace', fontWeight: 700, fontSize: '0.85rem', color: isSelected ? '#00843D' : '#0F172A' }}>
                        {tool.name}
                      </Typography>
                      <Chip
                        label={tool.category || 'core'}
                        size="small"
                        sx={{
                          height: 20,
                          fontSize: '0.7rem',
                          fontWeight: 600,
                          bgcolor: isSelected ? 'rgba(0,132,61,0.12)' : '#F1F5F9',
                          color: isSelected ? '#00843D' : '#475569',
                        }}
                      />
                    </Box>
                    <Typography variant="body2" sx={{ color: '#64748B', fontSize: '0.78rem', lineHeight: 1.4 }}>
                      {tool.description}
                    </Typography>
                  </Box>
                );
              })}
            </Box>
          </Paper>

          {/* Active Tool Configuration & Execution Canvas */}
          {selectedTool && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              {/* Tool Definition Header Card */}
              <Paper
                elevation={0}
                sx={{
                  p: 3,
                  borderRadius: 3,
                  border: '1px solid #E2E8F0',
                  bgcolor: '#FFFFFF',
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1, flexWrap: 'wrap', gap: 1 }}>
                  <Box>
                    <Typography variant="h6" sx={{ fontFamily: 'monospace', fontWeight: 800, color: '#0F172A' }}>
                      {selectedTool.name}
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#64748B', mt: 0.5 }}>
                      {selectedTool.description}
                    </Typography>
                  </Box>

                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    <SecurityIcon sx={{ fontSize: 18, color: '#64748B' }} />
                    {selectedTool.required_roles?.map((r) => (
                      <Chip
                        key={r}
                        label={r}
                        size="small"
                        sx={{
                          bgcolor: '#EFF6FF',
                          color: '#2563EB',
                          fontWeight: 700,
                          fontSize: '0.72rem',
                          textTransform: 'uppercase',
                          border: '1px solid #BFDBFE',
                        }}
                      />
                    ))}
                  </Box>
                </Box>
              </Paper>

              {/* Arguments Input Box */}
              <Paper
                elevation={0}
                sx={{
                  p: 3,
                  borderRadius: 3,
                  border: '1px solid #E2E8F0',
                  bgcolor: '#FFFFFF',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 2,
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#1E293B' }}>
                    Input Parameters (JSON payload)
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#64748B' }}>
                    Conforms to tool inputSchema
                  </Typography>
                </Box>

                <TextField
                  multiline
                  rows={6}
                  value={toolArguments}
                  onChange={(e) => setToolArguments(e.target.value)}
                  fullWidth
                  slotProps={{
                    input: {
                      sx: {
                        fontFamily: 'monospace',
                        fontSize: '0.85rem',
                        bgcolor: '#0F172A',
                        color: '#34D399',
                        borderRadius: 2,
                        '& .MuiOutlinedInput-notchedOutline': { borderColor: '#1E293B' },
                        '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: '#334155' },
                        '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: '#00843D' },
                      },
                    },
                  }}
                />

                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pt: 0.5 }}>
                  <Typography variant="caption" sx={{ color: '#64748B' }}>
                    Authorization and scope boundaries automatically enforced by server
                  </Typography>
                  <Button
                    variant="contained"
                    onClick={handleExecute}
                    disabled={isExecuting}
                    startIcon={isExecuting ? <CircularProgress size={16} sx={{ color: '#fff' }} /> : <PlayArrowIcon />}
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
                    {isExecuting ? 'Invoking MCP Tool...' : 'Execute Tool'}
                  </Button>
                </Box>
              </Paper>

              {/* Execution Result Box */}
              {executionResult && (
                <Paper
                  elevation={0}
                  sx={{
                    p: 3,
                    borderRadius: 3,
                    border: '1px solid #E2E8F0',
                    bgcolor: '#FFFFFF',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 2,
                  }}
                >
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {executionResult.status === 'success' ? (
                        <CheckCircleIcon sx={{ color: '#00843D', fontSize: 20 }} />
                      ) : (
                        <ErrorIcon sx={{ color: '#E11D48', fontSize: 20 }} />
                      )}
                      <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#1E293B' }}>
                        Execution Response
                      </Typography>
                    </Box>

                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                      <Chip
                        label={`${executionResult.execution_time_ms} ms latency`}
                        size="small"
                        sx={{ bgcolor: '#F1F5F9', color: '#475569', fontWeight: 600, fontSize: '0.72rem' }}
                      />
                      <Chip
                        label={executionResult.status.toUpperCase()}
                        size="small"
                        sx={{
                          bgcolor: executionResult.status === 'success' ? 'rgba(0,132,61,0.1)' : 'rgba(225,29,72,0.1)',
                          color: executionResult.status === 'success' ? '#00843D' : '#E11D48',
                          fontWeight: 800,
                          fontSize: '0.72rem',
                          border: `1px solid ${executionResult.status === 'success' ? 'rgba(0,132,61,0.25)' : 'rgba(225,29,72,0.25)'}`,
                        }}
                      />
                      <Tooltip title="Copy JSON Response">
                        <IconButton
                          size="small"
                          onClick={() => copyToClipboard(JSON.stringify(executionResult.result, null, 2))}
                        >
                          <ContentCopyIcon sx={{ fontSize: 16 }} />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Box>

                  <Box
                    sx={{
                      p: 2.5,
                      borderRadius: 2,
                      bgcolor: '#0B0F19',
                      border: '1px solid #1E293B',
                      overflowX: 'auto',
                      maxHeight: 340,
                    }}
                  >
                    <Typography
                      component="pre"
                      sx={{
                        m: 0,
                        fontFamily: 'monospace',
                        fontSize: '0.82rem',
                        color: '#F8FAFC',
                        lineHeight: 1.5,
                      }}
                    >
                      {JSON.stringify(executionResult.result, null, 2)}
                    </Typography>
                  </Box>
                </Paper>
              )}
            </Box>
          )}
        </Box>
      )}

      {/* Tab 2: Invocation Audit Trail */}
      {activeTab === 1 && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Filter Bar */}
          <Paper
            elevation={0}
            sx={{
              p: 2.5,
              borderRadius: 3,
              border: '1px solid #E2E8F0',
              bgcolor: '#FFFFFF',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: 2,
            }}
          >
            <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#1E293B' }}>
              Execution Telemetry & Audit Logs
            </Typography>

            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel id="status-filter-label">Filter by Status</InputLabel>
              <Select
                labelId="status-filter-label"
                value={statusFilter}
                label="Filter by Status"
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="">All Statuses</MenuItem>
                <MenuItem value="success">Success</MenuItem>
                <MenuItem value="unauthorized">Unauthorized</MenuItem>
                <MenuItem value="error">Error</MenuItem>
              </Select>
            </FormControl>
          </Paper>

          {/* Audit Logs Table */}
          <TableContainer
            component={Paper}
            elevation={0}
            sx={{
              borderRadius: 3,
              border: '1px solid #E2E8F0',
              overflow: 'hidden',
            }}
          >
            <Table>
              <TableHead sx={{ bgcolor: '#F8FAFC' }}>
                <TableRow>
                  <TableCell sx={{ fontWeight: 700, color: '#475569', fontSize: '0.8rem' }}>Tool Name</TableCell>
                  <TableCell sx={{ fontWeight: 700, color: '#475569', fontSize: '0.8rem' }}>Caller Identity</TableCell>
                  <TableCell sx={{ fontWeight: 700, color: '#475569', fontSize: '0.8rem' }}>Result Status</TableCell>
                  <TableCell sx={{ fontWeight: 700, color: '#475569', fontSize: '0.8rem' }}>Execution Latency</TableCell>
                  <TableCell sx={{ fontWeight: 700, color: '#475569', fontSize: '0.8rem' }}>Timestamp</TableCell>
                  <TableCell sx={{ fontWeight: 700, color: '#475569', fontSize: '0.8rem' }}>Arguments Summary</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {isLoadingLogs ? (
                  <TableRow>
                    <TableCell colSpan={6} sx={{ textAlign: 'center', py: 6, color: '#64748B' }}>
                      <CircularProgress size={24} sx={{ color: '#00843D', mb: 1 }} />
                      <Typography variant="body2">Loading invocation audit logs...</Typography>
                    </TableCell>
                  </TableRow>
                ) : logs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} sx={{ textAlign: 'center', py: 6, color: '#64748B' }}>
                      No audit records found matching criteria.
                    </TableCell>
                  </TableRow>
                ) : (
                  logs.map((log) => (
                    <TableRow key={log.id} hover sx={{ '&:last-child td, &:last-child th': { border: 0 } }}>
                      <TableCell sx={{ fontFamily: 'monospace', fontWeight: 700, color: '#0F172A', fontSize: '0.85rem' }}>
                        {log.tool_name}
                      </TableCell>
                      <TableCell sx={{ color: '#2563EB', fontFamily: 'monospace', fontSize: '0.8rem' }}>
                        {log.user_id ? `User #${log.user_id}` : 'AI Agent (Internal)'}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={log.result_status.toUpperCase()}
                          size="small"
                          sx={{
                            fontWeight: 700,
                            fontSize: '0.7rem',
                            bgcolor: log.result_status === 'success' ? 'rgba(0,132,61,0.1)' : 'rgba(225,29,72,0.1)',
                            color: log.result_status === 'success' ? '#00843D' : '#E11D48',
                          }}
                        />
                      </TableCell>
                      <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.82rem', color: '#334155' }}>
                        {log.execution_time_ms} ms
                      </TableCell>
                      <TableCell sx={{ fontSize: '0.8rem', color: '#64748B' }}>
                        {new Date(log.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.78rem', color: '#64748B', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {JSON.stringify(log.arguments_json)}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Box>
      )}
    </Box>
  );
};

export default MCPConsole;
