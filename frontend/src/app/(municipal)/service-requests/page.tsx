'use client';

import React, { useState, useEffect } from 'react';
import { 
  AlertCircle,
  Clock,
  CheckCircle2,
  PhoneCall,
  MoreVertical,
  Loader2,
  ChevronDown
} from 'lucide-react';
import { apiClient } from '@/lib/api';

export default function ServiceRequestsPage() {
  const [requests, setRequests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  const updateStatus = async (id: string, status: string) => {
    try {
      await apiClient.post(`/service-requests/${id}/status`, { status });
      fetchRequests();
    } catch (err) {
      console.error(err);
    }
  };

  const getSlaColor = (status: string) => {
    if (status === 'BREACHED') return 'bg-rose-500 animate-pulse';
    if (status === 'APPROACHING') return 'bg-amber-500';
    return 'bg-emerald-500';
  };

  const hasBreached = requests.some(r => r.sla_status === 'BREACHED');

  return (
    <div className="space-y-6 py-6">
      {hasBreached && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center gap-3 text-rose-400">
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
            <span className="text-sm font-semibold text-white">142 Healthy</span>
          </div>
          <div className="glass-panel px-4 py-2 rounded-xl border border-slate-800 flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-amber-500"></div>
            <span className="text-sm font-semibold text-white">12 Approaching</span>
          </div>
        </div>
      </div>

      <div className="glass-panel border border-slate-800 rounded-2xl overflow-hidden">
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
            <div className="hidden md:block overflow-x-auto">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="bg-slate-900/50 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="p-4 font-semibold">SR Number</th>
                    <th className="p-4 font-semibold">Title</th>
                    <th className="p-4 font-semibold">Status</th>
                    <th className="p-4 font-semibold">SLA</th>
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
                        <a href={`#`} className="text-blue-400 hover:underline font-semibold">{req.sr_number}</a>
                      </td>
                      <td className="p-4 text-slate-300 font-medium truncate max-w-[200px]">{req.title}</td>
                      <td className="p-4">
                        <select 
                          value={req.status}
                          onChange={(e) => updateStatus(req.id, e.target.value)}
                          className="bg-slate-800 border border-slate-700 text-xs font-semibold rounded-lg px-2 py-1 text-slate-300 focus:ring-1 focus:ring-blue-500 outline-none"
                        >
                          <option value="OPEN">OPEN</option>
                          <option value="IN_PROGRESS">IN PROGRESS</option>
                          <option value="RESOLVED">RESOLVED</option>
                          <option value="CLOSED">CLOSED</option>
                        </select>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <div className={`w-2.5 h-2.5 rounded-full ${getSlaColor(req.sla_status)}`}></div>
                          <span className="text-xs text-slate-400">{req.resolution_due}</span>
                        </div>
                      </td>
                      <td className="p-4 text-slate-300">{req.priority}</td>
                      <td className="p-4 text-slate-400">{new Date(req.created_at).toLocaleDateString()}</td>
                      <td className="p-4 text-slate-400">{req.assigned_to_name || 'Unassigned'}</td>
                      <td className="p-4 text-right">
                        <button className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-700">
                          <MoreVertical className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {requests.length === 0 && (
                    <tr>
                      <td colSpan={8} className="p-8 text-center text-slate-500">No service requests found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Mobile Stacked Cards */}
            <div className="block md:hidden space-y-3 p-4 bg-slate-950">
              {requests.map((req: any) => (
                <div key={req.id} className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3 relative">
                  <div className="flex justify-between items-start gap-2 pr-6">
                    <div>
                      <div className="text-xs font-bold text-blue-400 mb-1">{req.sr_number}</div>
                      <h3 className="text-sm font-semibold text-white leading-tight">{req.title}</h3>
                    </div>
                    <button className="absolute top-4 right-4 text-slate-400 p-1">
                      <MoreVertical className="w-4 h-4" />
                    </button>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="flex flex-col gap-1">
                      <span className="text-slate-500 font-medium">Status</span>
                      <select 
                        value={req.status}
                        onChange={(e) => updateStatus(req.id, e.target.value)}
                        className="bg-slate-800 border border-slate-700 font-semibold rounded px-1.5 py-1 text-slate-300 outline-none max-w-[120px]"
                      >
                        <option value="OPEN">OPEN</option>
                        <option value="IN_PROGRESS">IN PROGRESS</option>
                        <option value="RESOLVED">RESOLVED</option>
                        <option value="CLOSED">CLOSED</option>
                      </select>
                    </div>
                    <div className="flex flex-col gap-1">
                      <span className="text-slate-500 font-medium">Assigned To</span>
                      <span className="text-slate-300 truncate">{req.assigned_to_name || 'Unassigned'}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-slate-800/60 mt-1">
                    <div className="flex items-center gap-1.5">
                      <div className={`w-2 h-2 rounded-full ${getSlaColor(req.sla_status)}`}></div>
                      <span className="text-[10px] text-slate-400 font-medium">{req.resolution_due || 'No SLA'}</span>
                    </div>
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      req.priority === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400' :
                      req.priority === 'HIGH' ? 'bg-amber-500/20 text-amber-400' :
                      'bg-slate-800 text-slate-300'
                    }`}>
                      {req.priority}
                    </span>
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
    </div>
  );
}
