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
  History
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

  const fetchRequests = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get('/service-requests/');
      setRequests(res.data || []);
    } catch (err) {
      console.error(err);
      setError('Unable to fetch service requests.');
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

  const getSlaColor = (status: string) => {
    if (status === 'BREACHED') return 'bg-rose-500 animate-pulse';
    if (status === 'APPROACHING_BREACH' || status === 'APPROACHING') return 'bg-amber-500';
    return 'bg-emerald-500';
  };

  const hasBreached = requests.some(r => r.sla_status === 'BREACHED');
  const healthyCount = requests.filter(r => r.sla_status === 'SLA_HEALTHY' || !r.sla_status).length;
  const approachingCount = requests.filter(r => r.sla_status === 'APPROACHING_BREACH' || r.sla_status === 'APPROACHING').length;

  return (
    <div className="space-y-6 py-6">
      {hasBreached && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center gap-3 text-rose-400 animate-in fade-in">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span className="font-semibold text-sm">Action Required: You have service requests that have breached their SLA deadlines.</span>
        </div>
      )}

      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">311 Service Request Center</h1>
          <p className="text-slate-400 text-sm mt-1">Dispatch and monitor citizen service requests</p>
        </div>
        <div className="flex gap-3">
          <div className="glass-panel px-4 py-2 rounded-xl border border-slate-800 flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500"></div>
            <span className="text-sm font-semibold text-white">{healthyCount} Healthy</span>
          </div>
          <div className="glass-panel px-4 py-2 rounded-xl border border-slate-800 flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-amber-500"></div>
            <span className="text-sm font-semibold text-white">{approachingCount} Approaching</span>
          </div>
        </div>
      </div>

      <div className="glass-panel border border-slate-800 rounded-2xl overflow-visible">
        {error && (
          <div className="flex items-center justify-between p-4 bg-rose-500/10 border-b border-rose-500/30 text-rose-400 text-sm">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={fetchRequests}
              className="px-3 py-1.5 text-xs font-semibold bg-rose-500/20 hover:bg-rose-500/30 rounded-lg transition-colors"
            >
              Try Again
            </button>
          </div>
        )}
        {loading ? (
          <div className="p-12 flex flex-col items-center gap-3">
            <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
            <span className="text-sm text-slate-400">Loading requests...</span>
          </div>
        ) : (
          <>
            {/* Desktop Table */}
            <div className="hidden md:block overflow-x-auto min-h-[300px]">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="bg-slate-900/50 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="p-4 font-semibold">SR Number</th>
                    <th className="p-4 font-semibold">Status</th>
                    <th className="p-4 font-semibold">SLA Health</th>
                    <th className="p-4 font-semibold">Priority</th>
                    <th className="p-4 font-semibold">Created</th>
                    <th className="p-4 font-semibold">Assigned To</th>
                    <th className="p-4 font-semibold text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {requests.map((req: any) => (
                    <tr key={req.id} className="hover:bg-slate-800/20 transition-colors">
                      <td className="p-4">
                        <button 
                          onClick={() => setSelectedSR(req)}
                          className="text-blue-400 hover:text-blue-300 hover:underline font-bold"
                        >
                          {req.sr_number}
                        </button>
                      </td>
                      <td className="p-4">
                        <select
                          value={req.status}
                          onChange={(e) => updateStatus(req.id, e.target.value)}
                          className="bg-slate-800 border border-slate-700 text-xs font-semibold rounded-lg px-2.5 py-1.5 text-slate-300 focus:ring-1 focus:ring-blue-500 outline-none"
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
                        <div className="flex items-center gap-2">
                          <div className={`w-2.5 h-2.5 rounded-full ${getSlaColor(req.sla_status)}`}></div>
                          <span className="text-xs text-slate-300 font-medium">{req.sla_status || 'SLA_HEALTHY'}</span>
                        </div>
                      </td>
                      <td className="p-4">
                        <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                          req.priority_override === 'URGENT' || req.priority_override === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                          req.priority_override === 'HIGH' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                          'bg-slate-800 text-slate-300 border border-slate-700'
                        }`}>
                          {req.priority_override || 'MEDIUM'}
                        </span>
                      </td>
                      <td className="p-4 text-slate-400">{new Date(req.created_at).toLocaleDateString()}</td>
                      <td className="p-4 text-slate-400">
                        {assigningId === req.id ? (
                          <div className="flex items-center gap-2">
                            <input
                              type="number"
                              placeholder="User ID"
                              value={assignedStaffId}
                              onChange={(e) => setAssignedStaffId(e.target.value)}
                              className="w-20 bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs text-white"
                            />
                            <button
                              onClick={() => assignStaff(req.id)}
                              className="px-2 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-bold"
                            >
                              Save
                            </button>
                            <button
                              onClick={() => setAssigningId(null)}
                              className="text-slate-400 hover:text-white text-xs"
                            >
                              ✕
                            </button>
                          </div>
                        ) : (
                          <span>User #{req.assigned_to_id || 'Unassigned'}</span>
                        )}
                      </td>
                      <td className="p-4 text-right relative action-menu-container">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setOpenMenuId(openMenuId === req.id ? null : req.id);
                          }}
                          className="text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-800 transition-colors"
                        >
                          <MoreVertical className="w-4 h-4" />
                        </button>

                        {/* Dropdown Menu */}
                        {openMenuId === req.id && (
                          <div className="absolute right-4 top-12 z-50 w-52 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl py-1 text-left animate-in fade-in slide-in-from-top-2">
                            <button
                              onClick={() => {
                                setSelectedSR(req);
                                setOpenMenuId(null);
                              }}
                              className="w-full px-4 py-2.5 text-xs font-semibold text-slate-200 hover:bg-slate-800 flex items-center gap-2 transition-colors"
                            >
                              <Eye className="w-4 h-4 text-blue-400" /> View Detailed Request
                            </button>
                            <button
                              onClick={() => {
                                setAssigningId(req.id);
                                setOpenMenuId(null);
                              }}
                              className="w-full px-4 py-2.5 text-xs font-semibold text-slate-200 hover:bg-slate-800 flex items-center gap-2 transition-colors"
                            >
                              <UserCheck className="w-4 h-4 text-purple-400" /> Assign Staff Member
                            </button>
                            <button
                              onClick={() => updateStatus(req.id, 'IN_PROGRESS')}
                              className="w-full px-4 py-2.5 text-xs font-semibold text-slate-200 hover:bg-slate-800 flex items-center gap-2 transition-colors"
                            >
                              <Zap className="w-4 h-4 text-amber-400" /> Mark In Progress
                            </button>
                            <button
                              onClick={() => updateStatus(req.id, 'RESOLVED')}
                              className="w-full px-4 py-2.5 text-xs font-semibold text-emerald-400 hover:bg-slate-800 flex items-center gap-2 border-t border-slate-800 transition-colors"
                            >
                              <CheckCircle2 className="w-4 h-4" /> Mark Resolved
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                  {requests.length === 0 && (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-slate-500">No service requests found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Mobile Stacked Cards */}
            <div className="block md:hidden space-y-3 p-4 bg-slate-950">
              {requests.map((req: any) => (
                <div key={req.id} className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3 relative action-menu-container">
                  <div className="flex justify-between items-start gap-2 pr-6">
                    <div>
                      <div className="text-xs font-bold text-blue-400 mb-1">{req.sr_number}</div>
                      <h3 className="text-sm font-semibold text-white leading-tight">Issue #{req.issue_id}</h3>
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
                      <div className="absolute right-4 top-12 z-50 w-48 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl py-1 text-left">
                        <button
                          onClick={() => {
                            setSelectedSR(req);
                            setOpenMenuId(null);
                          }}
                          className="w-full px-3 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-800 flex items-center gap-2"
                        >
                          <Eye className="w-4 h-4 text-blue-400" /> View Details
                        </button>
                        <button
                          onClick={() => updateStatus(req.id, 'RESOLVED')}
                          className="w-full px-3 py-2 text-xs font-semibold text-emerald-400 hover:bg-slate-800 flex items-center gap-2 border-t border-slate-800"
                        >
                          <CheckCircle2 className="w-4 h-4" /> Mark Resolved
                        </button>
                      </div>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="flex flex-col gap-1">
                      <span className="text-slate-500 font-medium">Status</span>
                      <select
                        value={req.status}
                        onChange={(e) => updateStatus(req.id, e.target.value)}
                        className="bg-slate-800 border border-slate-700 font-semibold rounded px-1.5 py-1 text-slate-300 outline-none max-w-[120px]"
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

                  <div className="flex items-center justify-between pt-3 border-t border-slate-800/60 mt-1">
                    <div className="flex items-center gap-1.5">
                      <div className={`w-2 h-2 rounded-full ${getSlaColor(req.sla_status)}`}></div>
                      <span className="text-[10px] text-slate-400 font-medium">{req.sla_status || 'SLA_HEALTHY'}</span>
                    </div>
                    <button
                      onClick={() => setSelectedSR(req)}
                      className="text-xs text-blue-400 font-semibold hover:underline"
                    >
                      View Details →
                    </button>
                  </div>
                </div>
              ))}
              {requests.length === 0 && (
                <div className="text-center p-6 text-sm text-slate-500">No service requests found.</div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Service Request Detail Slide-Over Drawer */}
      {selectedSR && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full md:max-w-xl bg-slate-900 border-l border-slate-800 h-full overflow-y-auto p-6 shadow-2xl animate-in slide-in-from-right space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <span className="text-xs font-extrabold text-blue-400 uppercase tracking-wider">311 Service Request</span>
                <h2 className="text-2xl font-black text-white mt-0.5">{selectedSR.sr_number}</h2>
              </div>
              <button 
                onClick={() => setSelectedSR(null)}
                className="p-2 text-slate-400 hover:text-white rounded-full hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-800">
                <div className="text-xs text-slate-400 font-semibold mb-1 flex items-center gap-1">
                  <Building className="w-3.5 h-3.5 text-blue-400" /> Linked Issue ID
                </div>
                <div className="font-bold text-white">Issue #{selectedSR.issue_id}</div>
              </div>

              <div className="p-3 rounded-xl bg-slate-800/50 border border-slate-800">
                <div className="text-xs text-slate-400 font-semibold mb-1 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-amber-400" /> SLA Status
                </div>
                <div className="font-bold text-white flex items-center gap-2">
                  <div className={`w-2.5 h-2.5 rounded-full ${getSlaColor(selectedSR.sla_status)}`}></div>
                  {selectedSR.sla_status || 'SLA_HEALTHY'}
                </div>
              </div>
            </div>

            {/* Timestamps */}
            <div className="space-y-3">
              <h3 className="text-xs font-extrabold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Calendar className="w-4 h-4 text-purple-400" /> Key SLA Deadlines
              </h3>
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">Response Due:</span>
                  <span className="text-slate-200 font-semibold">{selectedSR.sla_response_due_at ? new Date(selectedSR.sla_response_due_at).toLocaleString() : 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Resolution Due:</span>
                  <span className="text-slate-200 font-semibold">{selectedSR.sla_resolution_due_at ? new Date(selectedSR.sla_resolution_due_at).toLocaleString() : 'N/A'}</span>
                </div>
              </div>
            </div>

            {/* Status History */}
            <div className="space-y-3">
              <h3 className="text-xs font-extrabold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <History className="w-4 h-4 text-emerald-400" /> Status Change Log
              </h3>
              <div className="space-y-2">
                {selectedSR.status_history && selectedSR.status_history.length > 0 ? (
                  selectedSR.status_history.map((hist: any) => (
                    <div key={hist.id} className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
                      <div className="flex justify-between text-slate-400">
                        <span className="font-bold text-emerald-400">{hist.to_status}</span>
                        <span>{new Date(hist.created_at).toLocaleString()}</span>
                      </div>
                      {hist.notes && <p className="text-slate-300 italic">{hist.notes}</p>}
                    </div>
                  ))
                ) : (
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-500 text-center">
                    Initial status logged: {selectedSR.status}
                  </div>
                )}
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedSR(null)}
                className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white text-sm font-semibold rounded-xl"
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
