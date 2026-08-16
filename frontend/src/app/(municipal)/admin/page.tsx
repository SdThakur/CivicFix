'use client';

import React, { useState, useEffect, useCallback } from 'react';
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
  AlertCircle,
  Radio,
  ShieldCheck,
  Activity,
  ArrowUpRight
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
import { useRouter } from 'next/navigation';
import { analyticsApi, reportApi, issueApi, serviceRequestApi } from '@/lib/api';

const COLORS = ['#00f2ff', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#3b82f6'];

export default function AdminAnalyticsPage() {
  const router = useRouter();
  const [stats, setStats] = useState<any>(null);
  const [resolutionTimes, setResolutionTimes] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [triagingId, setTriagingId] = useState<number | null>(null);
  const [triageError, setTriageError] = useState<string | null>(null);

  const triageReport = useCallback(async (report: any) => {
    setTriagingId(report.id);
    setTriageError(null);
    try {
      // Step 1: Create an Issue from the report
      const issue = await issueApi.create({
        title: report.title,
        description: report.description || `Triaged from report ${report.tracking_number || report.id}`,
        category: report.category || 'OTHER',
        latitude: report.latitude,
        longitude: report.longitude,
        address: report.address || '',
        neighborhood: report.neighborhood || '',
        priority: report.priority || 'MEDIUM',
      }, report.id);

      // Step 2: Create a ServiceRequest linked to the issue
      await serviceRequestApi.createFromIssue(issue.id);

      // Step 3: Navigate to the SR center
      router.push('/service-requests');
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Triage failed. Please try again.';
      setTriageError(msg);
    } finally {
      setTriagingId(null);
    }
  }, [router]);

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
      setError('Unable to load analytics telemetry. Ensure the backend server is online.');
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
    <div className="space-y-8 py-4">
      {/* Top Bar Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-400 text-xs font-mono font-bold uppercase tracking-wider mb-2 border border-cyan-500/20">
            <Radio className="w-3.5 h-3.5 text-cyan-400 animate-pulse" /> Municipal Infrastructure Analytics & Machine Intelligence
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight font-display-lg">City Command Center</h1>
          <p className="text-slate-400 text-sm mt-1">Live aggregated reporting telemetry, category distribution, and department SLAs</p>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]"></div>
            <span className="font-mono text-xs font-bold text-emerald-400 uppercase">Telemetry: Active</span>
          </div>
          <button
            onClick={fetchAnalytics}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 border border-white/10 text-slate-300 hover:text-white hover:border-cyan-500/50 transition-all disabled:opacity-50 text-xs font-mono font-medium"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${loading ? 'animate-spin' : ''}`} />
            <span>SYNC METRICS</span>
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="flex items-center justify-between p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm font-mono shadow-[0_0_20px_rgba(244,63,94,0.15)]">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button 
            onClick={fetchAnalytics} 
            className="px-3 py-1.5 text-xs font-bold bg-rose-500/20 hover:bg-rose-500/30 rounded-lg transition-colors border border-rose-500/30"
          >
            Retry Connection
          </button>
        </div>
      )}

      {/* Top Telemetry KPI Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1 */}
        <div className="glass-card p-5 rounded-2xl border border-white/10 hover:border-cyan-500/30 transition-all group">
          <div className="flex justify-between items-start mb-2">
            <span className="text-slate-400 text-xs font-mono font-medium uppercase tracking-wider">Total Reports</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-mono font-extrabold text-white">
            {loading ? '...' : stats?.total_reports ?? 0}
          </div>
          <div className="text-[11px] font-mono text-cyan-400 mt-2 flex items-center gap-1">
            <TrendingUp className="w-3 h-3" /> All logged incidents stream
          </div>
        </div>

        {/* KPI 2 */}
        <div className="glass-card p-5 rounded-2xl border border-amber-500/20 hover:border-amber-500/40 transition-all group">
          <div className="flex justify-between items-start mb-2">
            <span className="text-slate-400 text-xs font-mono font-medium uppercase tracking-wider">Active Remediation</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-mono font-extrabold text-amber-400 drop-shadow-[0_0_8px_rgba(245,158,11,0.3)]">
            {loading ? '...' : stats?.active_issues ?? 0}
          </div>
          <div className="text-[11px] font-mono text-amber-400/80 mt-2">Under active field remediation</div>
        </div>

        {/* KPI 3 */}
        <div className="glass-card p-5 rounded-2xl border border-rose-500/20 hover:border-rose-500/40 transition-all group">
          <div className="flex justify-between items-start mb-2">
            <span className="text-slate-400 text-xs font-mono font-medium uppercase tracking-wider">Pending Work Orders</span>
            <Clock className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-3xl font-mono font-extrabold text-rose-400 drop-shadow-[0_0_8px_rgba(244,63,94,0.3)]">
            {loading ? '...' : stats?.pending_work_orders ?? 0}
          </div>
          <div className="text-[11px] font-mono text-rose-400/80 mt-2">Field crew dispatch queue</div>
        </div>

        {/* KPI 4 */}
        <div className="glass-card p-5 rounded-2xl border border-emerald-500/20 hover:border-emerald-500/40 transition-all group">
          <div className="flex justify-between items-start mb-2">
            <span className="text-slate-400 text-xs font-mono font-medium uppercase tracking-wider">Avg Resolution SLA</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-mono font-extrabold text-emerald-400">
            {loading ? '...' : `${stats?.avg_resolution_time_days ?? 2.4}d`}
          </div>
          <div className="text-[11px] font-mono text-emerald-400/80 mt-2">Mean turnaround timeframe</div>
        </div>
      </div>

      {/* Stitch Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Breakdown Pie Chart */}
        <div className="glass-panel p-6 rounded-3xl border border-white/10 space-y-4 shadow-[0_0_20px_rgba(0,0,0,0.4)]">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <h3 className="text-base font-mono font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <PieIcon className="w-4 h-4 text-cyan-400" /> Infrastructure Category Telemetry
            </h3>
            <span className="text-xs font-mono text-slate-400">{categoryChartData.length} Categories</span>
          </div>

          {loading ? (
            <div className="h-64 flex flex-col items-center justify-center gap-2 text-slate-500 font-mono text-xs">
              <Loader2 className="w-6 h-6 animate-spin text-cyan-400" />
              <span>Rendering Distribution...</span>
            </div>
          ) : categoryChartData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-slate-500 font-mono text-xs">
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
                    innerRadius={65}
                    outerRadius={95}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {categoryChartData.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={entry.color} stroke="#070a12" strokeWidth={2} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#070a12',
                      borderColor: 'rgba(255, 255, 255, 0.1)',
                      borderRadius: '12px',
                      color: '#fff',
                      fontFamily: 'JetBrains Mono, monospace',
                      fontSize: '12px',
                      boxShadow: '0 0 20px rgba(0,0,0,0.8)'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}

          <div className="flex flex-wrap gap-3 pt-2 font-mono text-xs">
            {categoryChartData.map((cat: any) => (
              <div key={cat.name} className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-900/60 border border-white/5 text-slate-300">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: cat.color }} />
                <span>{cat.name}: <strong className="text-white">{cat.value}</strong></span>
              </div>
            ))}
          </div>
        </div>

        {/* Resolution Time per Category Bar Chart */}
        <div className="glass-panel p-6 rounded-3xl border border-white/10 space-y-4 shadow-[0_0_20px_rgba(0,0,0,0.4)]">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <h3 className="text-base font-mono font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Clock className="w-4 h-4 text-emerald-400" /> Mean Resolution Time (Hours)
            </h3>
            <span className="text-xs font-mono text-emerald-400">Target SLA</span>
          </div>

          {loading ? (
            <div className="h-64 flex flex-col items-center justify-center gap-2 text-slate-500 font-mono text-xs">
              <Loader2 className="w-6 h-6 animate-spin text-emerald-400" />
              <span>Calculating SLA Averages...</span>
            </div>
          ) : resolutionChartData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-slate-500 font-mono text-xs">
              Resolution metrics will populate as work orders close.
            </div>
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={resolutionChartData}>
                  <XAxis dataKey="category" stroke="#64748b" fontSize={11} fontFamily="JetBrains Mono, monospace" />
                  <YAxis stroke="#64748b" fontSize={11} fontFamily="JetBrains Mono, monospace" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#070a12',
                      borderColor: 'rgba(255, 255, 255, 0.1)',
                      borderRadius: '12px',
                      color: '#fff',
                      fontFamily: 'JetBrains Mono, monospace',
                      fontSize: '12px',
                    }}
                  />
                  <Bar dataKey="hours" fill="#10b981" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      {/* Top Neighborhood Hotspots Cluster */}
      <div className="glass-panel p-6 rounded-3xl border border-white/10 space-y-4 shadow-[0_0_20px_rgba(0,0,0,0.4)]">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <h3 className="text-base font-mono font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Flame className="w-4 h-4 text-rose-400" /> High-Activity Neighborhood Clusters (DBSCAN Spatial Analysis)
          </h3>
        </div>

        {loading ? (
          <div className="p-8 flex items-center justify-center text-slate-500 font-mono text-xs">
            <Loader2 className="w-6 h-6 animate-spin text-rose-400" />
          </div>
        ) : (stats?.top_neighborhoods || []).length === 0 ? (
          <div className="p-8 text-center text-slate-500 font-mono text-xs">
            No neighborhood hotspot clusters detected yet.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono">
            {stats.top_neighborhoods.map((n: any) => (
              <div key={n.neighborhood} className="p-4 rounded-2xl bg-slate-900/90 border border-white/10 space-y-2 hover:border-rose-500/40 transition-all">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-sm flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-rose-400" /> {n.neighborhood}
                  </span>
                  <span className="text-[11px] px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold border border-rose-500/30">
                    {n.total_reports} Incidents
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-white/5">
                  <span>Resolved: <strong className="text-emerald-400">{n.resolved_reports}</strong></span>
                  <span>Active Open: <strong className="text-amber-400">{n.open_issues}</strong></span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Live Citizen Reports & Triage Feed Table */}
      <div className="glass-panel p-6 rounded-3xl border border-white/10 space-y-4 shadow-[0_0_25px_rgba(0,0,0,0.4)]">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-3">
          <div>
            <h3 className="text-base font-mono font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Building2 className="w-4 h-4 text-cyan-400" /> Incoming Triage Tickets & Citizen Reports
            </h3>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Inspect citizen field reports and triage into dispatched service requests
            </p>
          </div>
          <Link
            href="/service-requests"
            className="px-4 py-2 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-xs font-mono font-bold transition-all flex items-center gap-1.5 self-start sm:self-auto"
          >
            <span>DISPATCH CENTER</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Triage error banner */}
        {triageError && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 flex items-center gap-2 text-rose-300 text-xs font-mono">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-400" />
            <span>{triageError}</span>
            <button onClick={() => setTriageError(null)} className="ml-auto hover:text-rose-200">✕</button>
          </div>
        )}

        {loading ? (
          <div className="p-12 flex flex-col items-center justify-center gap-2 text-slate-500 font-mono text-xs">
            <Loader2 className="w-6 h-6 animate-spin text-cyan-400" />
            <span>Streaming Incoming Reports...</span>
          </div>
        ) : reports.length === 0 ? (
          <div className="p-8 text-center text-slate-500 font-mono text-xs">
            No active citizen reports logged yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse font-mono">
              <thead>
                <tr className="border-b border-white/10 text-slate-400 font-bold uppercase tracking-wider">
                  <th className="py-3 px-3">Tracking ID</th>
                  <th className="py-3 px-3">Category</th>
                  <th className="py-3 px-3">Report Details</th>
                  <th className="py-3 px-3">Location</th>
                  <th className="py-3 px-3">Priority Score</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-slate-300">
                {reports.map((r: any) => (
                  <tr key={r.id} className="hover:bg-cyan-500/[0.03] transition-colors">
                    <td className="py-3.5 px-3 font-bold text-cyan-400">
                      {r.tracking_number || `REP-${r.id}`}
                    </td>
                    <td className="py-3.5 px-3">
                      <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-slate-900 text-slate-200 border border-slate-800">
                        {r.category || 'OTHER'}
                      </span>
                    </td>
                    <td className="py-3.5 px-3 max-w-xs">
                      <div className="font-bold text-white truncate">{r.title}</div>
                      <div className="text-[11px] text-slate-400 line-clamp-1 mt-0.5 font-sans">{r.description}</div>
                    </td>
                    <td className="py-3.5 px-3 text-slate-400 max-w-xs truncate">
                      📍 {r.address || `${r.latitude?.toFixed(4)}, ${r.longitude?.toFixed(4)}`}
                    </td>
                    <td className="py-3.5 px-3 font-bold text-white">
                      <span className={`px-2 py-0.5 rounded text-[11px] ${
                        (r.priority_score ?? 50) >= 75 ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30' :
                        (r.priority_score ?? 50) >= 50 ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30' :
                        'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                      }`}>
                        {r.priority_score ?? 50}/100
                      </span>
                    </td>
                    <td className="py-3.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        r.status === 'RESOLVED'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                          : r.status === 'IN_PROGRESS'
                          ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                          : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                      }`}>
                        {r.status?.replace('_', ' ') || 'SUBMITTED'}
                      </span>
                    </td>
                    <td className="py-3.5 px-3 text-right">
                      <button
                        onClick={() => triageReport(r)}
                        disabled={triagingId === r.id}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-cyan-500/10 hover:bg-cyan-500 text-cyan-300 hover:text-black font-bold transition-all text-xs border border-cyan-500/30 disabled:opacity-60 disabled:cursor-not-allowed"
                      >
                        {triagingId === r.id ? (
                          <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Triaging...</>
                        ) : (
                          'Triage Ticket'
                        )}
                      </button>
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
