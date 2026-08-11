'use client';

import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  AlertTriangle, 
  Building2, 
  Clock, 
  CheckCircle2, 
  Flame,
  PieChart as PieIcon,
  Sparkles,
  MapPin,
  RefreshCw,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell, 
  XAxis, 
  YAxis, 
  Tooltip, 
  BarChart, 
  Bar 
} from 'recharts';
import Link from 'next/link';
import { analyticsApi, reportApi } from '@/lib/api';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4'];

export default function AdminAnalyticsPage() {
  const [stats, setStats] = useState<any>(null);
  const [resolutionTimes, setResolutionTimes] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const [dashboardData, resData, reportsData] = await Promise.all([
        analyticsApi.getDashboard(),
        analyticsApi.getResolutionTimes().catch(() => []),
        reportApi.list().catch(() => []),
      ]);
      setStats(dashboardData);
      setResolutionTimes(Array.isArray(resData) ? resData : []);
      setReports(Array.isArray(reportsData) ? reportsData : []);
    } catch (err: any) {
      setError('Unable to load analytics data. Ensure the backend server is online.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const categoryChartData = (stats?.category_breakdown || []).map((c: any, idx: number) => ({
    name: c.category || 'Other',
    value: c.count || 0,
    color: COLORS[idx % COLORS.length],
  }));

  const resolutionChartData = (resolutionTimes || []).map((r: any) => ({
    category: r.category || 'General',
    hours: parseFloat((r.avg_resolution_hours || 0).toFixed(1)),
    resolved: r.total_resolved || 0,
  }));

  return (
    <div className="space-y-8 py-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-2">
            <BarChart3 className="w-3.5 h-3.5" /> Municipal Infrastructure Analytics & Machine Intelligence
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">City Command Center</h1>
          <p className="text-slate-400 text-sm mt-1">Live aggregated reporting telemetry, category distribution, and department SLAs</p>
        </div>

        <button
          onClick={fetchAnalytics}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-blue-500 transition-colors disabled:opacity-50 text-xs font-semibold"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Metrics
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="flex items-center justify-between p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button 
            onClick={fetchAnalytics} 
            className="px-3 py-1.5 text-xs font-semibold bg-rose-500/20 hover:bg-rose-500/30 rounded-lg transition-colors"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Top Metrics Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">
            Total Reports
          </div>
          <div className="text-3xl font-black text-white">
            {loading ? '...' : stats?.total_reports ?? 0}
          </div>
          <div className="text-[11px] text-blue-400 mt-1 font-medium">All logged incidents</div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">
            Active Issues
          </div>
          <div className="text-3xl font-black text-amber-400">
            {loading ? '...' : stats?.active_issues ?? 0}
          </div>
          <div className="text-[11px] text-amber-500/70 mt-1 font-medium">Under active remediation</div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">
            Pending Work Orders
          </div>
          <div className="text-3xl font-black text-rose-400">
            {loading ? '...' : stats?.pending_work_orders ?? 0}
          </div>
          <div className="text-[11px] text-rose-500/70 mt-1 font-medium">Field crew queue</div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">
            Avg Resolution SLA
          </div>
          <div className="text-3xl font-black text-emerald-400">
            {loading ? '...' : `${stats?.avg_resolution_time_days ?? 2.4}d`}
          </div>
          <div className="text-[11px] text-emerald-500/70 mt-1 font-medium">Mean turnaround time</div>
        </div>
      </div>

      {/* Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Breakdown Pie Chart */}
        <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <PieIcon className="w-5 h-5 text-blue-400" /> Infrastructure Category Distribution
            </h3>
          </div>

          {loading ? (
            <div className="h-64 flex items-center justify-center text-slate-500">
              <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
            </div>
          ) : categoryChartData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-slate-500 text-sm">
              No category telemetry available.
            </div>
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryChartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {categoryChartData.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#1e293b',
                      borderRadius: '12px',
                      color: '#fff',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}

          <div className="flex flex-wrap gap-3 pt-2">
            {categoryChartData.map((cat: any) => (
              <div key={cat.name} className="flex items-center gap-1.5 text-xs text-slate-300">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: cat.color }} />
                <span>{cat.name}: <strong>{cat.value}</strong></span>
              </div>
            ))}
          </div>
        </div>

        {/* Resolution Time per Category Bar Chart */}
        <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-emerald-400" /> Mean Resolution Time (Hours)
            </h3>
          </div>

          {loading ? (
            <div className="h-64 flex items-center justify-center text-slate-500">
              <Loader2 className="w-6 h-6 animate-spin text-emerald-500" />
            </div>
          ) : resolutionChartData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-slate-500 text-sm">
              Resolution metrics will appear as work orders are closed.
            </div>
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={resolutionChartData}>
                  <XAxis dataKey="category" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      borderColor: '#1e293b',
                      borderRadius: '12px',
                      color: '#fff',
                    }}
                  />
                  <Bar dataKey="hours" fill="#10b981" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      {/* Top Neighborhood Hotspots */}
      <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <Flame className="w-5 h-5 text-rose-400" /> High-Activity Neighborhood Clusters
        </h3>

        {loading ? (
          <div className="p-8 flex items-center justify-center text-slate-500">
            <Loader2 className="w-6 h-6 animate-spin text-rose-500" />
          </div>
        ) : (stats?.top_neighborhoods || []).length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">
            No neighborhood hotspot clusters detected yet.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {stats.top_neighborhoods.map((n: any) => (
              <div key={n.neighborhood} className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-sm">{n.neighborhood}</span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 font-semibold">
                    {n.total_reports} Reports
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400 pt-1 border-t border-slate-800">
                  <span>Resolved: <strong className="text-emerald-400">{n.resolved_reports}</strong></span>
                  <span>Open: <strong className="text-amber-400">{n.open_issues}</strong></span>
                </div>
              </div>
      {/* Live Citizen Reports & Triage Feed Table */}
      <div className="glass-panel p-6 rounded-3xl border border-slate-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Building2 className="w-5 h-5 text-blue-400" /> Live Citizen Reports & Incoming Triage Tickets
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Review, inspect, and route reported infrastructure hazards to department crews
            </p>
          </div>
          <Link
            href="/service-requests"
            className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition-colors flex items-center gap-1.5 self-start sm:self-auto"
          >
            <span>Open Service Requests</span>
            <TrendingUp className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="p-8 flex items-center justify-center text-slate-500">
            <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          </div>
        ) : reports.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">
            No active citizen reports logged yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                  <th className="py-3 px-3">Tracking ID</th>
                  <th className="py-3 px-3">Category</th>
                  <th className="py-3 px-3">Title & Details</th>
                  <th className="py-3 px-3">Location</th>
                  <th className="py-3 px-3">Priority Score</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80 text-slate-300">
                {reports.map((r: any) => (
                  <tr key={r.id} className="hover:bg-slate-900/50 transition-colors">
                    <td className="py-3 px-3 font-mono font-bold text-blue-400">
                      {r.tracking_number || `REP-${r.id}`}
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-200 border border-slate-700">
                        {r.category || 'OTHER'}
                      </span>
                    </td>
                    <td className="py-3 px-3 max-w-xs">
                      <div className="font-bold text-white truncate">{r.title}</div>
                      <div className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">{r.description}</div>
                    </td>
                    <td className="py-3 px-3 text-slate-400 max-w-xs truncate">
                      📍 {r.address || `${r.latitude?.toFixed(4)}, ${r.longitude?.toFixed(4)}`}
                    </td>
                    <td className="py-3 px-3 font-bold text-white">
                      {r.priority_score ?? 50}/100
                    </td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${
                        r.status === 'RESOLVED'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : r.status === 'IN_PROGRESS'
                          ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                          : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      }`}>
                        {r.status?.replace('_', ' ') || 'SUBMITTED'}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <Link
                        href="/service-requests"
                        className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-blue-600 text-slate-200 hover:text-white font-semibold transition-colors text-[11px]"
                      >
                        Triage Ticket
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
