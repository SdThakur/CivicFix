'use client';

import React, { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  Layers, 
  PlusCircle, 
  ArrowRight,
  ShieldCheck,
  Check,
  X,
  Sparkles,
  Loader2,
  RefreshCw,
  MapPin,
  ThumbsUp
} from 'lucide-react';
import { reportApi, authApi } from '@/lib/api';

function DashboardContent() {
  const searchParams = useSearchParams();
  const showCreatedBanner = searchParams.get('created') === 'true';
  const showMergedBanner = searchParams.get('merged') === 'true';

  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [upvotedIds, setUpvotedIds] = useState<Set<number>>(new Set());

  const fetchReports = async () => {
    setLoading(true);
    setError(null);
    try {
      // Check auth user first if available
      try {
        const user = await authApi.me();
        setCurrentUser(user);
      } catch {
        // Not logged in or anonymous
      }

      const data = await reportApi.list();
      setReports(Array.isArray(data) ? data : []);
    } catch (err: any) {
      setError('Unable to fetch reports from server. Make sure the backend service is running.');
      setReports([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleUpvote = async (reportId: number) => {
    if (upvotedIds.has(reportId)) return;
    try {
      await reportApi.upvote(reportId);
      setUpvotedIds((prev) => new Set(prev).add(reportId));
      setReports((prev) =>
        prev.map((r) =>
          r.id === reportId ? { ...r, upvotes: (r.upvotes || 0) + 1 } : r
        )
      );
    } catch (err) {
      console.error('Error upvoting report', err);
    }
  };

  // Metrics calculated dynamically from real reports
  const totalReports = reports.length;
  const inProgressReports = reports.filter((r) => r.status === 'IN_PROGRESS' || r.status === 'ASSIGNED').length;
  const resolvedReports = reports.filter((r) => r.status === 'RESOLVED').length;
  const underReviewReports = reports.filter((r) => r.status === 'UNDER_REVIEW' || r.status === 'SUBMITTED').length;

  return (
    <div className="space-y-8 py-6">
      {/* Banners */}
      {showCreatedBanner && (
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
            <span>Your infrastructure report was submitted successfully! AI triage has routed it to the appropriate municipal department.</span>
          </div>
          <Link href="/report" className="font-semibold text-xs underline">
            Report Another
          </Link>
        </div>
      )}

      {showMergedBanner && (
        <div className="p-4 rounded-2xl bg-blue-500/10 border border-blue-500/30 text-blue-400 text-sm flex items-center gap-3">
          <Sparkles className="w-5 h-5 flex-shrink-0" />
          <span>Your confirmation was added to an existing issue. Priority score updated!</span>
        </div>
      )}

      {/* Greeting Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Citizen Dashboard</h1>
          <p className="text-slate-400 text-sm">
            {currentUser ? `Welcome back, ${currentUser.full_name}. ` : ''}
            Track your reported issues & monitor municipal repair progress.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchReports}
            disabled={loading}
            className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-blue-500 transition-colors disabled:opacity-50"
            title="Refresh reports"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <Link
            href="/report"
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold transition-all shadow-lg shadow-blue-600/20"
          >
            <PlusCircle className="w-4 h-4" />
            Report Issue
          </Link>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1 flex items-center gap-2">
            <Layers className="w-4 h-4 text-blue-400" /> Total Reports
          </div>
          <div className="text-2xl font-black text-white">{loading ? '...' : totalReports}</div>
          <div className="text-[11px] text-slate-500 mt-1">Submitted across city</div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1 flex items-center gap-2">
            <Clock className="w-4 h-4 text-amber-400" /> In Progress
          </div>
          <div className="text-2xl font-black text-amber-400">{loading ? '...' : inProgressReports}</div>
          <div className="text-[11px] text-amber-500/70 mt-1">Crew dispatched</div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Resolved
          </div>
          <div className="text-2xl font-black text-emerald-400">{loading ? '...' : resolvedReports}</div>
          <div className="text-[11px] text-emerald-500/70 mt-1">Repairs completed</div>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-slate-800">
          <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-sky-400" /> Under Review
          </div>
          <div className="text-2xl font-black text-sky-400">{loading ? '...' : underReviewReports}</div>
          <div className="text-[11px] text-sky-500/70 mt-1">Awaiting dispatch</div>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="flex items-center gap-3 p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Report List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white tracking-tight">Recent Infrastructure Reports</h2>
          <span className="text-xs text-slate-400">
            Showing {reports.length} live records
          </span>
        </div>

        {loading ? (
          <div className="glass-panel p-12 rounded-2xl border border-slate-800 flex flex-col items-center justify-center gap-3 text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            <span className="text-sm font-medium">Fetching infrastructure reports...</span>
          </div>
        ) : reports.length === 0 ? (
          <div className="glass-panel p-12 rounded-2xl border border-slate-800 flex flex-col items-center justify-center text-center space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500">
              <MapPin className="w-7 h-7" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">No reports found</h3>
              <p className="text-slate-400 text-sm max-w-sm mt-1">
                Be the first to photograph and report a road hazard, broken streetlight, or trash issue in your neighborhood!
              </p>
            </div>
            <Link
              href="/report"
              className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold transition-colors"
            >
              Submit First Report
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {reports.map((report) => (
              <div
                key={report.id}
                className="glass-panel p-6 rounded-2xl border border-slate-800 transition-all hover:border-slate-700 space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono px-2 py-1 rounded bg-slate-900 text-slate-400 border border-slate-800">
                      REP-{report.id}
                    </span>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                      {report.category || 'General'}
                    </span>
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        report.status === 'RESOLVED'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : report.status === 'IN_PROGRESS'
                          ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                          : report.status === 'VERIFICATION'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : 'bg-slate-800 text-slate-300 border border-slate-700'
                      }`}
                    >
                      {report.status?.replace('_', ' ')}
                    </span>
                  </div>

                  <div className="text-xs text-slate-400">
                    {new Date(report.created_at || Date.now()).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    })}
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-bold text-white">{report.title}</h3>
                  {report.description && (
                    <p className="text-slate-300 text-sm mt-1">{report.description}</p>
                  )}
                  {report.address && (
                    <div className="text-xs text-slate-400 mt-2 flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-slate-500" />
                      <span>{report.address}</span>
                    </div>
                  )}
                </div>

                {/* Status and Action bar */}
                <div className="flex items-center justify-between pt-3 border-t border-slate-800/80">
                  <div className="flex items-center gap-4 text-xs text-slate-400">
                    <span>Priority Score: <strong className="text-white">{report.priority_score ?? (report.priority === 'CRITICAL' ? 90 : report.priority === 'HIGH' ? 75 : 50)}/100</strong></span>
                    <span>Department: <strong className="text-slate-300">{report.department_code || 'Public Works'}</strong></span>
                  </div>

                  <button
                    onClick={() => handleUpvote(report.id)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
                      upvotedIds.has(report.id)
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-blue-500/50'
                    }`}
                  >
                    <ThumbsUp className="w-3.5 h-3.5" />
                    <span>Upvote ({report.upvotes || 0})</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function CitizenDashboard() {
  return (
    <Suspense fallback={<div className="p-8 text-slate-400">Loading dashboard...</div>}>
      <DashboardContent />
    </Suspense>
  );
}
