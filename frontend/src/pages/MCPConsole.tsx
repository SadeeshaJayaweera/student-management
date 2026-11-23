import React, { useState, useEffect } from 'react';
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
  const [activeTab, setActiveTab] = useState<'sandbox' | 'logs'>('sandbox');

  // Tools
  const [tools, setTools] = useState<MCPToolDefinition[]>([]);
  const [selectedTool, setSelectedTool] = useState<MCPToolDefinition | null>(null);
  const [toolArguments, setToolArguments] = useState<string>('{}');
  const [executionResult, setExecutionResult] = useState<MCPToolExecutionResponse | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);

  // Invocations Log
  const [logs, setLogs] = useState<MCPToolInvocationLog[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [isLoadingLogs, setIsLoadingLogs] = useState(false);

  useEffect(() => {
    fetchTools();
  }, []);

  useEffect(() => {
    if (activeTab === 'logs') {
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
    } catch (err) {
      toast.error('Failed to load MCP tool registry');
    }
  };

  const selectTool = (tool: MCPToolDefinition) => {
    setSelectedTool(tool);
    setExecutionResult(null);

    // Generate starter JSON based on inputSchema properties
    const defaultArgs: Record<string, any> = {};
    if (tool.inputSchema?.properties) {
      for (const [key, prop] of Object.entries<any>(tool.inputSchema.properties)) {
        if (key === 'student_id') {
          defaultArgs[key] = 'STU001';
        } else if (prop.type === 'string') {
          defaultArgs[key] = '';
        } else if (prop.type === 'integer') {
          defaultArgs[key] = 1;
        } else if (prop.type === 'array') {
          defaultArgs[key] = [];
        }
      }
    }
    setToolArguments(JSON.stringify(defaultArgs, null, 2));
  };

  const handleExecute = async () => {
    if (!selectedTool) return;
    let parsedArgs = {};
    try {
      parsedArgs = JSON.parse(toolArguments);
    } catch (err) {
      toast.error('Arguments must be valid JSON');
      return;
    }

    setIsExecuting(true);
    setExecutionResult(null);
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
    } catch (err) {
      toast.error('Failed to load audit logs (requires faculty or admin role)');
    } finally {
      setIsLoadingLogs(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white/10 backdrop-blur-md p-6 rounded-2xl border border-white/20 shadow-xl">
        <div>
          <h1 className="text-3xl font-extrabold text-white flex items-center gap-3">
            <span>⚙️</span> Model Context Protocol (MCP) Console
          </h1>
          <p className="text-gray-300 mt-1">
            Standardized tool execution orchestrator, schema introspection & access boundary audit logging
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-mono">
            MCP Protocol v1.0
          </span>
          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            {tools.length} Tools Registered
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-white/10 space-x-2">
        <button
          onClick={() => setActiveTab('sandbox')}
          className={`px-5 py-3 rounded-t-xl font-medium transition-all ${
            activeTab === 'sandbox'
              ? 'bg-indigo-600/40 text-white border-t border-x border-indigo-400/30'
              : 'text-gray-400 hover:text-white hover:bg-white/5'
          }`}
        >
          🧪 Tool Catalog & Execution Sandbox
        </button>
        <button
          onClick={() => setActiveTab('logs')}
          className={`px-5 py-3 rounded-t-xl font-medium transition-all ${
            activeTab === 'logs'
              ? 'bg-indigo-600/40 text-white border-t border-x border-indigo-400/30'
              : 'text-gray-400 hover:text-white hover:bg-white/5'
          }`}
        >
          📜 Invocation Audit Trail
        </button>
      </div>

      {/* Sandbox Tab */}
      {activeTab === 'sandbox' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Tool Catalog */}
          <div className="lg:col-span-1 bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-4 space-y-3 h-[700px] flex flex-col">
            <h3 className="text-sm font-bold text-gray-300 uppercase tracking-wider px-2">
              Registered Tools
            </h3>
            <div className="flex-1 overflow-y-auto space-y-2 pr-1">
              {tools.map((t) => (
                <button
                  key={t.name}
                  onClick={() => selectTool(t)}
                  className={`w-full text-left p-3.5 rounded-xl transition flex flex-col gap-1 border ${
                    selectedTool?.name === t.name
                      ? 'bg-indigo-600/30 border-indigo-400/40 text-white shadow'
                      : 'bg-black/20 border-white/5 text-gray-300 hover:bg-white/5'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm font-mono truncate">{t.name}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/10 font-sans">
                      {t.category}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 line-clamp-2">{t.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Execution & Result Panel */}
          <div className="lg:col-span-2 space-y-6">
            {selectedTool && (
              <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6 space-y-6 shadow-xl">
                <div>
                  <div className="flex items-center justify-between">
                    <h2 className="text-xl font-bold text-white font-mono">{selectedTool.name}</h2>
                    <div className="flex gap-2">
                      {selectedTool.required_roles.map((r) => (
                        <span
                          key={r}
                          className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 capitalize"
                        >
                          {r}
                        </span>
                      ))}
                    </div>
                  </div>
                  <p className="text-gray-300 text-sm mt-1">{selectedTool.description}</p>
                </div>

                {/* Arguments Editor */}
                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-200">
                    Input Arguments (JSON):
                  </label>
                  <textarea
                    rows={6}
                    value={toolArguments}
                    onChange={(e) => setToolArguments(e.target.value)}
                    className="w-full bg-gray-950/80 font-mono text-xs text-emerald-400 p-4 rounded-xl border border-gray-800 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                  <div className="flex justify-between items-center pt-1">
                    <span className="text-xs text-gray-400">
                      Validated against MCP inputSchema specification
                    </span>
                    <button
                      onClick={handleExecute}
                      disabled={isExecuting}
                      className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold px-6 py-2 rounded-xl transition flex items-center gap-2 shadow"
                    >
                      {isExecuting ? 'Invoking Tool...' : '⚡ Call Tool'}
                    </button>
                  </div>
                </div>

                {/* Execution Result Box */}
                {executionResult && (
                  <div className="space-y-2 pt-4 border-t border-white/10">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-gray-200">Execution Response:</span>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-gray-400">
                          Latency: {executionResult.execution_time_ms} ms
                        </span>
                        <span
                          className={`text-xs px-2.5 py-0.5 rounded-full font-semibold uppercase ${
                            executionResult.status === 'success'
                              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                              : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          }`}
                        >
                          {executionResult.status}
                        </span>
                      </div>
                    </div>
                    <pre className="bg-gray-950/90 font-mono text-xs text-gray-200 p-4 rounded-xl border border-gray-800 overflow-x-auto max-h-72">
                      {JSON.stringify(executionResult.result, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Audit Log Tab */}
      {activeTab === 'logs' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center bg-white/5 p-4 rounded-2xl border border-white/10">
            <span className="text-sm font-semibold text-gray-200">Filter Invocations:</span>
            <div className="flex gap-3">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-gray-800 text-white border border-gray-700 rounded-xl px-4 py-2 text-sm"
              >
                <option value="">All Statuses</option>
                <option value="success">Success</option>
                <option value="unauthorized">Unauthorized</option>
                <option value="error">Error</option>
              </select>
            </div>
          </div>

          {isLoadingLogs ? (
            <div className="text-center py-12 text-gray-400">Loading audit trail...</div>
          ) : logs.length === 0 ? (
            <div className="text-center py-12 bg-white/5 rounded-2xl border border-white/10 text-gray-400">
              No audit records matching filter criteria.
            </div>
          ) : (
            <div className="overflow-x-auto bg-white/5 rounded-2xl border border-white/10">
              <table className="w-full text-left text-sm text-gray-300">
                <thead className="bg-white/10 text-gray-200 uppercase text-xs font-semibold">
                  <tr>
                    <th className="px-6 py-4">Tool Name</th>
                    <th className="px-6 py-4">Caller User</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4">Execution (ms)</th>
                    <th className="px-6 py-4">Timestamp</th>
                    <th className="px-6 py-4">Arguments</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {logs.map((log) => (
                    <tr key={log.id} className="hover:bg-white/5 transition">
                      <td className="px-6 py-4 font-mono font-semibold text-white">
                        {log.tool_name}
                      </td>
                      <td className="px-6 py-4 text-xs font-mono text-indigo-300">
                        {log.user_id ? `User #${log.user_id}` : 'Anonymous'}
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                            log.result_status === 'success'
                              ? 'bg-emerald-500/20 text-emerald-400'
                              : log.result_status === 'unauthorized'
                              ? 'bg-amber-500/20 text-amber-400'
                              : 'bg-rose-500/20 text-rose-400'
                          }`}
                        >
                          {log.result_status}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-mono">{log.execution_time_ms} ms</td>
                      <td className="px-6 py-4 text-xs text-gray-400">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 font-mono text-xs text-gray-400 max-w-xs truncate">
                        {JSON.stringify(log.arguments_json)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
export default MCPConsole;
