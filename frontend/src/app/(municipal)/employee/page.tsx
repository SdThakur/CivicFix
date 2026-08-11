'use client';

import React, { useState, useEffect } from 'react';
import { 
  Building2, 
  CheckCircle2, 
  Clock, 
  Upload, 
  AlertTriangle, 
  UserCheck, 
  FileText, 
  Camera, 
  ArrowRight, 
  ShieldCheck, 
  Check,
  RefreshCw,
  Loader2,
  AlertCircle,
  MapPin
} from 'lucide-react';
import { workOrderApi, authApi } from '@/lib/api';
import type { WorkOrder } from '@/types';

export default function EmployeeDashboard() {
  const [workOrders, setWorkOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<any>(null);

  const [activeModal, setActiveModal] = useState<any>(null);
  const [repairNotes, setRepairNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchWorkOrders = async () => {
    setLoading(true);
    setError(null);
    try {
      try {
        const user = await authApi.me();
        setCurrentUser(user);
      } catch {
        // Not authenticated
      }
      const data = await workOrderApi.list();
      setWorkOrders(Array.isArray(data) ? data : []);
    } catch (err: any) {
      setError('Unable to fetch work orders from the server. Ensure backend service is running.');
      setWorkOrders([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkOrders();
  }, []);

  const handleStartWork = async (id: number | string) => {
    try {
      await workOrderApi.updateStatus(id, 'IN_PROGRESS');
      setWorkOrders((orders) =>
        orders.map((wo) => (wo.id === id ? { ...wo, status: 'IN_PROGRESS' } : wo))
      );
    } catch (err) {
      console.error('Error starting work order', err);
    }
  };

  const handleSubmitResolution = async (woId: number | string) => {
    setSubmitting(true);
    try {
      await workOrderApi.updateStatus(woId, 'COMPLETED');
      setWorkOrders((orders) =>
        orders.map((wo) => (wo.id === woId ? { ...wo, status: 'COMPLETED', notes: repairNotes } : wo))
      );
      setActiveModal(null);
      setRepairNotes('');
    } catch (err) {
      console.error('Error completing work order', err);
    } finally {
      setSubmitting(false);
    }
  };

  // Live KPI counts
  const totalAssigned = workOrders.length;
  const inProgressCount = workOrders.filter((w) => w.status === 'IN_PROGRESS').length;
  const completedCount = workOrders.filter((w) => w.status === 'COMPLETED').length;
  const pendingCount = workOrders.filter((w) => w.status === 'ASSIGNED' || w.status === 'PENDING').length;

  return (
    <div className="space-y-8 py-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <Building2 className="w-3.5 h-3.5" /> Department Operations & Dispatch
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Municipal Dispatch Queue</h1>
          <p className="text-slate-400 text-sm mt-1">Manage field repairs, update status, and attach completion verification</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchWorkOrders}
            disabled={loading}
            className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-blue-500 transition-colors disabled:opacity-50"
            title="Refresh work orders"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          {currentUser && (
            <span className="text-xs text-slate-400 bg-slate-900 px-3 py-2 rounded-xl border border-slate-800">
              Staff: <strong className="text-slate-200">{currentUser.full_name}</strong>
            </span>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1 flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-400" /> Total Work Orders
          </div>
          <div className="text-2xl font-black text-white">{loading ? '...' : totalAssigned}</div>
          <div className="text-[11px] text-slate-500 mt-1">Assigned to department</div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1 flex items-center gap-2">
            <Clock className="w-4 h-4 text-amber-400" /> In Progress
          </div>
          <div className="text-2xl font-black text-amber-400">{loading ? '...' : inProgressCount}</div>
          <div className="text-[11px] text-amber-500/70 mt-1">Currently being repaired</div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Completed
          </div>
          <div className="text-2xl font-black text-emerald-400">{loading ? '...' : completedCount}</div>
          <div className="text-[11px] text-emerald-500/70 mt-1">Repairs submitted</div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-400" /> Pending Dispatch
          </div>
          <div className="text-2xl font-black text-rose-400">{loading ? '...' : pendingCount}</div>
          <div className="text-[11px] text-rose-500/70 mt-1">Awaiting field crew</div>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="flex items-center gap-3 p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Work Orders List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white tracking-tight">Active Work Orders</h2>
          <span className="text-xs text-slate-400">Showing {workOrders.length} records</span>
        </div>

        {loading ? (
          <div className="glass-panel p-12 rounded-2xl border border-slate-800 flex flex-col items-center justify-center gap-3 text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            <span className="text-sm font-medium">Loading work orders queue...</span>
          </div>
        ) : workOrders.length === 0 ? (
          <div className="glass-panel p-12 rounded-2xl border border-slate-800 flex flex-col items-center justify-center text-center space-y-3">
            <div className="w-14 h-14 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500">
              <CheckCircle2 className="w-7 h-7 text-emerald-500" />
            </div>
            <h3 className="text-lg font-bold text-white">No active work orders</h3>
            <p className="text-slate-400 text-sm max-w-sm">
              All infrastructure work orders are currently fulfilled or awaiting new citizen reports.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {workOrders.map((wo) => (
              <div
                key={wo.id}
                className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4 hover:border-slate-700 transition-all flex flex-col justify-between"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                      WO-{wo.id}
                    </span>
                    <span
                      className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
                        wo.priority === 'CRITICAL'
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          : wo.priority === 'HIGH'
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                      }`}
                    >
                      {wo.priority || 'MEDIUM'}
                    </span>
                  </div>

                  <h3 className="text-lg font-bold text-white">{wo.title || `Work Order #${wo.id}`}</h3>
                  {wo.description && (
                    <p className="text-slate-300 text-sm">{wo.description}</p>
                  )}

                  <div className="space-y-1 text-xs text-slate-400 pt-2 border-t border-slate-800/80">
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      <span>Status: <strong className="text-slate-200">{wo.status?.replace('_', ' ')}</strong></span>
                    </div>
                    {wo.estimated_hours && (
                      <div className="flex items-center gap-1.5">
                        <FileText className="w-3.5 h-3.5 text-slate-500" />
                        <span>Estimated time: <strong className="text-slate-200">{wo.estimated_hours} hrs</strong></span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="pt-4 border-t border-slate-800/80 flex items-center justify-between gap-3">
                  {wo.status === 'ASSIGNED' || wo.status === 'PENDING' ? (
                    <button
                      onClick={() => handleStartWork(wo.id)}
                      className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold transition-colors flex items-center justify-center gap-2"
                    >
                      <Clock className="w-4 h-4" /> Start Repair
                    </button>
                  ) : wo.status === 'IN_PROGRESS' ? (
                    <button
                      onClick={() => setActiveModal(wo)}
                      className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-colors flex items-center justify-center gap-2"
                    >
                      <CheckCircle2 className="w-4 h-4" /> Submit Completion
                    </button>
                  ) : (
                    <div className="w-full py-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-semibold text-center flex items-center justify-center gap-1.5">
                      <ShieldCheck className="w-4 h-4" /> Completed & Verified
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Completion Modal */}
      {activeModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel p-6 rounded-3xl border border-slate-700 max-w-lg w-full space-y-4 shadow-2xl">
            <h3 className="text-xl font-bold text-white">Complete Work Order #{activeModal.id}</h3>
            <p className="text-slate-400 text-xs">
              Record repair details to resolve the issue and notify citizen reporters.
            </p>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300">Repair Action & Material Notes</label>
              <textarea
                value={repairNotes}
                onChange={(e) => setRepairNotes(e.target.value)}
                placeholder="e.g. Replaced LED luminaire fixture, repaired roadway with hot mix asphalt..."
                rows={4}
                className="w-full p-3 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm focus:outline-none focus:border-blue-500 placeholder-slate-500"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
              <button
                onClick={() => setActiveModal(null)}
                disabled={submitting}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={() => handleSubmitResolution(activeModal.id)}
                disabled={submitting}
                className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                Confirm Repair Completion
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
