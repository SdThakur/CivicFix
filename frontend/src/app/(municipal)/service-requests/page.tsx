'use client';

import React, { useState, useEffect } from 'react';
import {
  AlertCircle,
  Clock,
  CheckCircle2,
  PhoneCall,
  MoreVertical,
  Loader2,
  ChevronDown,
  X,
  UserCheck,
  Zap,
  Eye,
  Calendar,
  Building,
  History,
  RefreshCw,
  Search,
  SlidersHorizontal,
  Activity,
  ShieldAlert,
  Radio,
  FileText
} from 'lucide-react';
import { apiClient } from '@/lib/api';

export default function ServiceRequestsPage() {
  const [requests, setRequests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [openMenuId, setOpenMenuId] = useState<string | number | null>(null);
  const [selectedSR, setSelectedSR] = useState<any | null>(null);
  const [assigningId, setAssigningId] = useState<string | number | null>(null);
  const [assignedStaffId, setAssignedStaffId] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const fetchRequests = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get('/service-requests/');
      setRequests(res.data || []);
    } catch (err) {
      console.error(err);
      setError('Unable to fetch service requests from municipal dispatch backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, []);

  // Close 3-dot dropdown when clicking outside
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (!(e.target as HTMLElement).closest('.action-menu-container')) {
        setOpenMenuId(null);
      }
    };
    window.addEventListener('click', handleOutsideClick);
    return () => window.removeEventListener('click', handleOutsideClick);
  }, []);

  const updateStatus = async (id: string | number, status: string) => {
    try {
      await apiClient.post(`/service-requests/${id}/status`, { status });
      setOpenMenuId(null);
      fetchRequests();
    } catch (err) {
      console.error(err);
      alert('Failed to update service request status.');
    }
  };

  const assignStaff = async (srId: string | number) => {
    if (!assignedStaffId) return;
    try {
      await apiClient.patch(`/service-requests/${srId}`, {
        assigned_to_id: parseInt(assignedStaffId)
      });
      setAssigningId(null);
      setAssignedStaffId('');
      setOpenMenuId(null);
      fetchRequests();
    } catch (err) {
      console.error(err);
      alert('Failed to assign staff member.');
    }
  };

  const getSlaBadge = (status: string) => {
    if (status === 'BREACHED') return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded border border-rose-500/40 bg-rose-500/10 text-rose-400 text-[11px] font-mono font-bold animate-pulse shadow-[0_0_10px_rgba(244,63,94,0.3)]">
        <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
        BREACHED
      </span>
    );
    if (status === 'APPROACHING_BREACH' || status === 'APPROACHING') return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded border border-amber-500/40 bg-amber-500/10 text-amber-400 text-[11px] font-mono font-bold">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
        APPROACHING
      </span>
    );
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded border border-emerald-500/40 bg-emerald-500/10 text-emerald-400 text-[11px] font-mono font-medium">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
        HEALTHY
      </span>
    );
  };

  const getPriorityBadge = (priority: string) => {
    const p = (priority || 'MEDIUM').toUpperCase();
    if (p === 'URGENT' || p === 'CRITICAL' || p === 'P1') return (
      <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30 text-xs font-mono font-bold">P1 CRITICAL</span>
    );
    if (p === 'HIGH' || p === 'P2') return (
      <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30 text-xs font-mono font-semibold">P2 HIGH</span>
    );
    if (p === 'MEDIUM' || p === 'P3') return (
      <span className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 text-xs font-mono">P3 MEDIUM</span>
    );
    return (
      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 text-xs font-mono">P4 LOW</span>
    );
  };

  const breachedCount = requests.filter(r => r.sla_status === 'BREACHED').length;
  const healthyCount = requests.filter(r => r.sla_status === 'SLA_HEALTHY' || !r.sla_status).length;
  const approachingCount = requests.filter(r => r.sla_status === 'APPROACHING_BREACH' || r.sla_status === 'APPROACHING').length;
  const activeCount = requests.filter(r => r.status === 'IN_PROGRESS' || r.status === 'ASSIGNED' || r.status === 'UNDER_INSPECTION').length;

  const filteredRequests = requests.filter(req => {
    const matchesSearch = 
      (req.sr_number || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (req.issue_id ? `issue #${req.issue_id}` : '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (req.assigned_to_id ? `user #${req.assigned_to_id}` : '').toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || req.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6 py-4">
      {/* SLA Alert Banner */}
      {breachedCount > 0 && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/40 flex items-center justify-between text-rose-300 animate-in fade-in shadow-[0_0_20px_rgba(244,63,94,0.15)]">
          <div className="flex items-center gap-3">
            <ShieldAlert className="w-5 h-5 text-rose-400 flex-shrink-0 animate-pulse" />
            <span className="font-semibold text-sm">
              Critical SLA Alert: <strong className="font-mono text-rose-200">{breachedCount}</strong> service request{breachedCount > 1 ? 's have' : ' has'} breached target turnaround timelines.
            </span>
          </div>
          <button 
            onClick={() => setStatusFilter('ALL')}
            className="px-3 py-1 bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 text-xs font-mono font-bold rounded-lg transition-colors border border-rose-500/30"
          >
            Review SLA Breaches
          </button>
        </div>
      )}

      {/* Header & Control Bar */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-400 text-xs font-mono font-bold uppercase tracking-wider mb-2 border border-cyan-500/20">
            <Radio className="w-3.5 h-3.5 text-cyan-400 animate-pulse" /> Municipal Dispatch Telemetry
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight flex items-center gap-3 font-display-lg">
            311 Service Request Center
          </h1>
          <p className="text-slate-400 text-sm mt-1">Real-time municipal dispatching, response queue monitoring, and SLA health enforcement</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchRequests}
            disabled={loading}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900 border border-white/10 text-slate-300 hover:text-white hover:border-cyan-500/50 transition-all text-xs font-mono font-medium disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${loading ? 'animate-spin' : ''}`} />
            <span>SYNC DATA</span>
          </button>
        </div>
      </div>

      {/* Stitch KPI Telemetry Section */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1 */}
        <div className="glass-card rounded-2xl p-4 flex flex-col justify-between h-28 relative overflow-hidden group border border-white/10 hover:border-cyan-500/40 transition-all">
          <div className="flex justify-between items-start">
            <span className="text-xs font-medium text-slate-400">Total Logged Requests</span>
            <FileText className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="flex items-end justify-between">
            <span className="font-mono text-3xl font-extrabold text-white">{loading ? '...' : requests.length}</span>
            <span className="text-[11px] font-mono text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">Telemetry Active</span>
          </div>
        </div>

        {/* KPI 2 */}
        <div className="glass-card rounded-2xl p-4 flex flex-col justify-between h-28 relative overflow-hidden group border border-rose-500/30 shadow-[0_0_15px_rgba(244,63,94,0.1)]">
          <div className="flex justify-between items-start">
            <span className="text-xs font-medium text-slate-400">SLA Breaches</span>
            <AlertCircle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="flex items-end justify-between">
            <span className="font-mono text-3xl font-extrabold text-rose-400 drop-shadow-[0_0_8px_rgba(244,63,94,0.5)]">
              {loading ? '...' : breachedCount}
            </span>
            <span className="text-[11px] font-mono text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20 uppercase tracking-wider font-bold">
              {breachedCount > 0 ? 'CRITICAL' : 'NOMINAL'}
            </span>
          </div>
        </div>

        {/* KPI 3 */}
        <div className="glass-card rounded-2xl p-4 flex flex-col justify-between h-28 relative overflow-hidden group border border-amber-500/20">
          <div className="flex justify-between items-start">
            <span className="text-xs font-medium text-slate-400">Approaching SLA Deadline</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="flex items-end justify-between">
            <span className="font-mono text-3xl font-extrabold text-amber-400">
              {loading ? '...' : approachingCount}
            </span>
            <span className="text-[11px] font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
              Action Priority
            </span>
          </div>
        </div>

        {/* KPI 4 */}
        <div className="glass-card rounded-2xl p-4 flex flex-col justify-between h-28 relative overflow-hidden group border border-emerald-500/20">
          <div className="flex justify-between items-start">
            <span className="text-xs font-medium text-slate-400">Nominal SLA Healthy</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex items-end justify-between">
            <span className="font-mono text-3xl font-extrabold text-emerald-400">
              {loading ? '...' : healthyCount}
            </span>
            <span className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
              On Schedule
            </span>
          </div>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="glass-panel p-4 rounded-2xl border border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search SR Number, Issue ID, Staff..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900/80 border border-slate-800 rounded-xl text-xs text-white pl-10 pr-4 py-2 focus:ring-1 focus:ring-cyan-500 outline-none font-mono placeholder:text-slate-500"
          />
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-xs text-slate-400 font-mono uppercase">Filter Status:</span>
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 text-xs font-mono text-cyan-300 rounded-xl px-3 py-2 outline-none focus:ring-1 focus:ring-cyan-500"
          >
            <option value="ALL">ALL STATUSES</option>
            <option value="SUBMITTED">SUBMITTED</option>
            <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
            <option value="UNDER_INSPECTION">UNDER INSPECTION</option>
            <option value="ASSIGNED">ASSIGNED</option>
            <option value="IN_PROGRESS">IN PROGRESS</option>
            <option value="RESOLVED">RESOLVED</option>
            <option value="CLOSED">CLOSED</option>
            <option value="REJECTED">REJECTED</option>
          </select>
        </div>
      </div>

      {/* Main SLA Health Telemetry Table Container */}
      <div className="glass-panel border border-white/10 rounded-2xl overflow-visible relative shadow-[0_0_25px_rgba(0,0,0,0.4)]">
        <div className="p-4 border-b border-white/10 flex justify-between items-center bg-slate-900/40">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400 animate-pulse" />
            <h3 className="font-mono text-sm text-white font-bold uppercase tracking-wider">
              SLA Health Telemetry Log
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-400">
            Showing <strong className="text-cyan-400">{filteredRequests.length}</strong> entries
          </span>
        </div>

        {error && (
          <div className="flex items-center justify-between p-4 bg-rose-500/10 border-b border-rose-500/30 text-rose-300 text-sm font-mono">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={fetchRequests}
              className="px-3 py-1.5 text-xs font-bold bg-rose-500/20 hover:bg-rose-500/30 rounded-lg transition-colors border border-rose-500/30"
            >
              Retry Connection
            </button>
          </div>
        )}

        {loading ? (
          <div className="p-16 flex flex-col items-center justify-center gap-3">
            <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">Retrieving Dispatch Stream...</span>
          </div>
        ) : (
          <>
            {/* Desktop Table */}
            <div className="hidden md:block overflow-x-auto min-h-[350px]">
              <table className="w-full text-left text-xs whitespace-nowrap">
                <thead className="bg-slate-900/80 text-slate-400 border-b border-white/10 font-mono text-[11px] uppercase tracking-wider">
                  <tr>
                    <th className="p-4 font-bold">SR Tracking ID</th>
                    <th className="p-4 font-bold">Current Status</th>
                    <th className="p-4 font-bold">SLA Health</th>
                    <th className="p-4 font-bold">Priority</th>
                    <th className="p-4 font-bold">Logged Date</th>
                    <th className="p-4 font-bold">Assigned Dispatch</th>
                    <th className="p-4 font-bold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 font-mono">
                  {filteredRequests.map((req: any) => (
                    <tr 
                      key={req.id} 
                      className={`hover:bg-cyan-500/[0.03] transition-colors group ${
                        req.sla_status === 'BREACHED' ? 'bg-rose-500/[0.02]' : ''
                      }`}
                    >
                      <td className="p-4">
                        <button 
                          onClick={() => setSelectedSR(req)}
                          className="font-bold text-cyan-400 hover:text-cyan-300 hover:underline flex items-center gap-1.5 group-hover:translate-x-0.5 transition-transform"
                        >
                          <span>{req.sr_number}</span>
                          <Eye className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </button>
                        <div className="text-[10px] text-slate-500 font-mono mt-0.5">Issue #{req.issue_id}</div>
                      </td>
                      <td className="p-4">
                        <select
                          value={req.status}
                          onChange={(e) => updateStatus(req.id, e.target.value)}
                          className="bg-slate-900 border border-slate-700 text-xs font-mono font-bold rounded-lg px-2.5 py-1.5 text-slate-200 focus:ring-1 focus:ring-cyan-500 outline-none"
                        >
                          <option value="SUBMITTED">SUBMITTED</option>
                          <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
                          <option value="UNDER_INSPECTION">UNDER INSPECTION</option>
                          <option value="VERIFIED">VERIFIED</option>
                          <option value="ASSIGNED">ASSIGNED</option>
                          <option value="IN_PROGRESS">IN PROGRESS</option>
                          <option value="RESOLVED">RESOLVED</option>
                          <option value="CLOSED">CLOSED</option>
                          <option value="REJECTED">REJECTED</option>
                        </select>
                      </td>
                      <td className="p-4">
                        {getSlaBadge(req.sla_status)}
                      </td>
                      <td className="p-4">
                        {getPriorityBadge(req.priority_override)}
                      </td>
                      <td className="p-4 text-slate-400">
                        {new Date(req.created_at).toLocaleDateString()}
                      </td>
                      <td className="p-4 text-slate-300">
                        {assigningId === req.id ? (
                          <div className="flex items-center gap-2">
                            <input
                              type="number"
                              placeholder="Staff ID"
                              value={assignedStaffId}
                              onChange={(e) => setAssignedStaffId(e.target.value)}
                              className="w-20 bg-slate-900 border border-cyan-500/50 rounded px-2 py-1 text-xs text-white outline-none font-mono"
                            />
                            <button
                              onClick={() => assignStaff(req.id)}
                              className="px-2 py-1 bg-cyan-600 hover:bg-cyan-500 text-black font-bold rounded text-xs transition-colors"
                            >
                              Save
                            </button>
                            <button
                              onClick={() => setAssigningId(null)}
                              className="text-slate-400 hover:text-white text-xs px-1"
                            >
                              ✕
                            </button>
                          </div>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 text-slate-300 font-mono">
                            <UserCheck className="w-3.5 h-3.5 text-purple-400" />
                            {req.assigned_to_id ? `User #${req.assigned_to_id}` : <span className="text-slate-500 italic">Unassigned</span>}
                          </span>
                        )}
                      </td>
                      <td className="p-4 text-right relative action-menu-container">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setOpenMenuId(openMenuId === req.id ? null : req.id);
                          }}
                          className="text-slate-400 hover:text-cyan-400 p-2 rounded-lg hover:bg-slate-800 transition-colors"
                        >
                          <MoreVertical className="w-4 h-4" />
                        </button>

                        {/* Dropdown Menu */}
                        {openMenuId === req.id && (
                          <div className="absolute right-4 top-12 z-50 w-56 bg-slate-950 border border-cyan-500/30 rounded-xl shadow-[0_0_25px_rgba(0,0,0,0.8)] py-1.5 text-left animate-in fade-in slide-in-from-top-2">
                            <button
                              onClick={() => {
                                setSelectedSR(req);
                                setOpenMenuId(null);
                              }}
                              className="w-full px-4 py-2.5 text-xs font-mono text-slate-200 hover:bg-cyan-500/10 hover:text-cyan-300 flex items-center gap-2 transition-colors"
                            >
                              <Eye className="w-4 h-4 text-cyan-400" /> Inspect Detailed Drawer
                            </button>
                            <button
                              onClick={() => {
                                setAssigningId(req.id);
                                setOpenMenuId(null);
                              }}
                              className="w-full px-4 py-2.5 text-xs font-mono text-slate-200 hover:bg-cyan-500/10 hover:text-purple-300 flex items-center gap-2 transition-colors"
                            >
                              <UserCheck className="w-4 h-4 text-purple-400" /> Assign Dispatch Staff
                            </button>
                            <button
                              onClick={() => updateStatus(req.id, 'IN_PROGRESS')}
                              className="w-full px-4 py-2.5 text-xs font-mono text-slate-200 hover:bg-cyan-500/10 hover:text-amber-300 flex items-center gap-2 transition-colors"
                            >
                              <Zap className="w-4 h-4 text-amber-400" /> Dispatch Crew (In Progress)
                            </button>
                            <button
                              onClick={() => updateStatus(req.id, 'RESOLVED')}
                              className="w-full px-4 py-2.5 text-xs font-mono text-emerald-400 hover:bg-emerald-500/10 flex items-center gap-2 border-t border-slate-800 transition-colors mt-1 pt-2"
                            >
                              <CheckCircle2 className="w-4 h-4" /> Mark Fully Resolved
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                  {filteredRequests.length === 0 && (
                    <tr>
                      <td colSpan={7} className="p-12 text-center text-slate-500 font-mono text-xs">
                        No 311 service requests matched your search filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Mobile Stacked Cards */}
            <div className="block md:hidden space-y-3 p-4 bg-slate-950">
              {filteredRequests.map((req: any) => (
                <div key={req.id} className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3 relative action-menu-container">
                  <div className="flex justify-between items-start gap-2 pr-6">
                    <div>
                      <div className="text-xs font-mono font-bold text-cyan-400 mb-1">{req.sr_number}</div>
                      <h3 className="text-sm font-semibold text-white leading-tight">Linked Issue #{req.issue_id}</h3>
                    </div>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        setOpenMenuId(openMenuId === req.id ? null : req.id);
                      }}
                      className="absolute top-4 right-4 text-slate-400 p-1 hover:text-white rounded"
                    >
                      <MoreVertical className="w-4 h-4" />
                    </button>

                    {/* Mobile Menu */}
                    {openMenuId === req.id && (
                      <div className="absolute right-4 top-12 z-50 w-48 bg-slate-950 border border-cyan-500/30 rounded-xl shadow-2xl py-1 text-left">
                        <button
                          onClick={() => {
                            setSelectedSR(req);
                            setOpenMenuId(null);
                          }}
                          className="w-full px-3 py-2 text-xs font-mono text-slate-200 hover:bg-slate-800 flex items-center gap-2"
                        >
                          <Eye className="w-4 h-4 text-cyan-400" /> View Details
                        </button>
                        <button
                          onClick={() => updateStatus(req.id, 'RESOLVED')}
                          className="w-full px-3 py-2 text-xs font-mono text-emerald-400 hover:bg-slate-800 flex items-center gap-2 border-t border-slate-800"
                        >
                          <CheckCircle2 className="w-4 h-4" /> Mark Resolved
                        </button>
                      </div>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                    <div className="flex flex-col gap-1">
                      <span className="text-slate-500 font-medium">Status</span>
                      <select
                        value={req.status}
                        onChange={(e) => updateStatus(req.id, e.target.value)}
                        className="bg-slate-800 border border-slate-700 font-bold rounded px-2 py-1 text-cyan-300 outline-none"
                      >
                        <option value="SUBMITTED">SUBMITTED</option>
                        <option value="IN_PROGRESS">IN PROGRESS</option>
                        <option value="RESOLVED">RESOLVED</option>
                        <option value="CLOSED">CLOSED</option>
                      </select>
                    </div>
                    <div className="flex flex-col gap-1">
                      <span className="text-slate-500 font-medium">Assigned To</span>
                      <span className="text-slate-300 truncate">User #{req.assigned_to_id || 'Unassigned'}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-slate-800/80 mt-1">
                    {getSlaBadge(req.sla_status)}
                    <button
                      onClick={() => setSelectedSR(req)}
                      className="text-xs font-mono text-cyan-400 font-bold hover:underline"
                    >
                      Inspect Drawer →
                    </button>
                  </div>
                </div>
              ))}
              {filteredRequests.length === 0 && (
                <div className="text-center p-8 font-mono text-xs text-slate-500">No requests found.</div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Stitch-Inspired Slide-Over Incident Detail Drawer */}
      {selectedSR && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/80 backdrop-blur-md transition-opacity">
          <div className="w-full md:max-w-2xl bg-slate-950 border-l border-white/10 h-full overflow-y-auto p-6 shadow-[-20px_0_40px_rgba(0,0,0,0.8)] animate-in slide-in-from-right space-y-6 flex flex-col justify-between">
            <div className="space-y-6">
              {/* Drawer Top Header */}
              <div className="flex items-start justify-between border-b border-white/10 pb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 text-[10px] font-mono font-bold uppercase tracking-wider">
                      311 Service Ticket
                    </span>
                    {getSlaBadge(selectedSR.sla_status)}
                  </div>
                  <h2 className="text-3xl font-extrabold text-white tracking-tight font-display-lg mt-1">{selectedSR.sr_number}</h2>
                </div>
                <button 
                  onClick={() => setSelectedSR(null)}
                  className="p-2 text-slate-400 hover:text-white rounded-full hover:bg-slate-900 border border-transparent hover:border-slate-800 transition-all"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Grid Context Cards */}
              <div className="grid grid-cols-2 gap-4 text-xs font-mono">
                <div className="glass-card p-4 rounded-xl border border-white/10">
                  <div className="text-slate-400 font-semibold mb-1 flex items-center gap-1.5 uppercase">
                    <Building className="w-3.5 h-3.5 text-cyan-400" /> Linked Issue ID
                  </div>
                  <div className="font-bold text-white text-sm">Issue #{selectedSR.issue_id}</div>
                </div>

                <div className="glass-card p-4 rounded-xl border border-white/10">
                  <div className="text-slate-400 font-semibold mb-1 flex items-center gap-1.5 uppercase">
                    <UserCheck className="w-3.5 h-3.5 text-purple-400" /> Assigned Dispatcher
                  </div>
                  <div className="font-bold text-white text-sm">
                    {selectedSR.assigned_to_id ? `User #${selectedSR.assigned_to_id}` : 'Unassigned'}
                  </div>
                </div>
              </div>

              {/* Key SLA Deadlines */}
              <div className="space-y-3">
                <h3 className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-amber-400" /> Key SLA Deadlines & Response Targets
                </h3>
                <div className="p-4 rounded-2xl bg-slate-900/60 border border-white/10 space-y-3 text-xs font-mono">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Initial Response Due:</span>
                    <span className="text-cyan-300 font-bold">
                      {selectedSR.sla_response_due_at ? new Date(selectedSR.sla_response_due_at).toLocaleString() : 'Not Set'}
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-cyan-500 h-full w-[65%] shadow-[0_0_8px_rgba(0,242,255,0.8)]"></div>
                  </div>
                  <div className="flex justify-between items-center pt-1">
                    <span className="text-slate-400">Full Resolution Due:</span>
                    <span className="text-amber-300 font-bold">
                      {selectedSR.sla_resolution_due_at ? new Date(selectedSR.sla_resolution_due_at).toLocaleString() : 'Not Set'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Live Action Log Timeline */}
              <div className="space-y-3">
                <h3 className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider flex items-center justify-between border-b border-white/10 pb-2">
                  <span className="flex items-center gap-2"><History className="w-4 h-4 text-emerald-400" /> Status Transition Action Log</span>
                  <span className="text-cyan-400 text-[10px]">LIVE SYNC</span>
                </h3>
                <div className="space-y-3">
                  {selectedSR.status_history && selectedSR.status_history.length > 0 ? (
                    selectedSR.status_history.map((hist: any, index: number) => (
                      <div key={hist.id || index} className="p-3.5 rounded-xl bg-slate-900/80 border border-white/5 text-xs font-mono space-y-1 relative pl-4 border-l-2 border-l-emerald-500">
                        <div className="flex justify-between text-slate-400">
                          <span className="font-bold text-emerald-400 uppercase">{hist.to_status}</span>
                          <span className="text-[11px]">{new Date(hist.created_at).toLocaleString()}</span>
                        </div>
                        {hist.notes && <p className="text-slate-300 italic pt-1">{hist.notes}</p>}
                      </div>
                    ))
                  ) : (
                    <div className="p-4 rounded-xl bg-slate-900/40 border border-white/5 text-xs font-mono text-slate-500 text-center">
                      Initial status registered: <strong className="text-cyan-400">{selectedSR.status}</strong>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Bottom Drawer Actions */}
            <div className="pt-4 border-t border-white/10 flex items-center justify-between gap-3">
              <button
                onClick={() => updateStatus(selectedSR.id, 'RESOLVED')}
                className="flex-1 py-2.5 px-4 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 font-mono text-xs font-bold rounded-xl border border-emerald-500/40 transition-all flex items-center justify-center gap-2"
              >
                <CheckCircle2 className="w-4 h-4" /> Mark Fully Resolved
              </button>
              <button
                onClick={() => setSelectedSR(null)}
                className="py-2.5 px-5 bg-slate-800 hover:bg-slate-700 text-white font-mono text-xs font-bold rounded-xl border border-slate-700 transition-colors"
              >
                Close Drawer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

