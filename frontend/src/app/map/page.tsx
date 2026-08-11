'use client';

import React, { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { MapPin, Loader2, RefreshCw, AlertCircle } from 'lucide-react';
import { issueApi } from '@/lib/api';
import type { Issue } from '@/types';

// Dynamically import the map component to avoid SSR issues with Leaflet
const IssueMapInner = dynamic(() => import('@/components/map/IssueMapInner'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full flex items-center justify-center bg-slate-900/60 rounded-2xl">
      <div className="flex flex-col items-center gap-3 text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        <span className="text-sm font-medium">Loading map engine...</span>
      </div>
    </div>
  ),
});

const CATEGORY_FILTERS = ['ALL', 'Pothole', 'Streetlight', 'Trash', 'Sidewalk', 'Graffiti', 'Road Damage'];
const STATUS_FILTERS = ['ALL', 'SUBMITTED', 'IN_PROGRESS', 'VERIFICATION', 'RESOLVED', 'UNDER_REVIEW'];

export default function PublicMapPage() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null);

  const fetchIssues = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (selectedCategory !== 'ALL') params.category = selectedCategory.toLowerCase();
      if (selectedStatus !== 'ALL') params.status = selectedStatus;
      const data = await issueApi.list(params);
      setIssues(Array.isArray(data) ? data : []);
    } catch (err: any) {
      setError('Unable to load issues from the server. Make sure the backend is running.');
      setIssues([]);
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, selectedStatus]);

  useEffect(() => {
    fetchIssues();
  }, [fetchIssues]);

  // Issues that have valid location coordinates for map rendering
  const mappableIssues = issues.filter(
    (i) => i.location?.latitude && i.location?.longitude
  );

  return (
    <div className="space-y-4 py-4">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 glass-panel p-4 sm:p-5 rounded-2xl border border-slate-800">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <MapPin className="w-6 h-6 text-blue-500" />
            Public City Infrastructure Map
          </h1>
          <p className="text-slate-400 text-xs mt-1">
            Real-time geospatial feed of city hazards, active work orders, and resolved repairs
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchIssues}
            disabled={loading}
            className="p-2 rounded-xl bg-slate-800 border border-slate-700 text-slate-300 hover:text-white hover:border-blue-500/50 transition-colors disabled:opacity-50"
            title="Refresh data"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          {!loading && (
            <span className="text-xs text-slate-400 font-medium">
              {mappableIssues.length} mapped ·{' '}
              <span className="text-blue-400">{issues.length} total</span>
            </span>
          )}
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="flex flex-wrap items-center gap-2">
        {CATEGORY_FILTERS.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
              selectedCategory === cat
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20'
                : 'bg-slate-900 text-slate-300 border border-slate-800 hover:border-slate-700'
            }`}
          >
            {cat}
          </button>
        ))}
        <div className="h-5 w-px bg-slate-800 mx-1" />
        {STATUS_FILTERS.slice(0, 4).map((s) => (
          <button
            key={s}
            onClick={() => setSelectedStatus(s)}
            className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-colors ${
              selectedStatus === s
                ? 'bg-slate-700 text-white border border-slate-600'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            {s === 'ALL' ? 'All Status' : s.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="flex items-center gap-3 p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Layout: Map + Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-[600px]">
        {/* Map Panel (2 cols) */}
        <div className="lg:col-span-2 rounded-2xl overflow-hidden border border-slate-800 shadow-2xl bg-slate-900/60">
          {loading ? (
            <div className="w-full h-full flex items-center justify-center">
              <div className="flex flex-col items-center gap-3 text-slate-400">
                <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
                <span className="text-sm font-medium">Fetching geospatial data...</span>
              </div>
            </div>
          ) : (
            <IssueMapInner
              issues={mappableIssues}
              selectedIssue={selectedIssue}
              onSelectIssue={setSelectedIssue}
            />
          )}
        </div>

        {/* Issues Sidebar (1 col) */}
        <div className="glass-panel p-4 rounded-2xl border border-slate-800 flex flex-col h-full">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              {loading ? 'Loading...' : `${mappableIssues.length} Active Incidents`}
            </span>
            <span className="text-[11px] text-blue-400 font-semibold">Live Geospatial Feed</span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-3 pr-1">
            {loading ? (
              // Skeleton loading state
              Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 animate-pulse space-y-2">
                  <div className="h-3 bg-slate-800 rounded w-3/4" />
                  <div className="h-3 bg-slate-800 rounded w-1/2" />
                  <div className="h-3 bg-slate-800 rounded w-2/3" />
                </div>
              ))
            ) : mappableIssues.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center space-y-3 py-12">
                <MapPin className="w-10 h-10 text-slate-700" />
                <p className="text-slate-400 text-sm">No issues found matching filters.</p>
                <button
                  onClick={() => { setSelectedCategory('ALL'); setSelectedStatus('ALL'); }}
                  className="text-xs text-blue-400 underline"
                >
                  Clear filters
                </button>
              </div>
            ) : (
              mappableIssues.map((issue) => (
                <button
                  key={issue.id}
                  onClick={() => setSelectedIssue(selectedIssue?.id === issue.id ? null : issue)}
                  className={`w-full text-left p-4 rounded-xl border transition-all space-y-2 ${
                    selectedIssue?.id === issue.id
                      ? 'bg-blue-600/20 border-blue-500/60 shadow-lg shadow-blue-500/10'
                      : 'bg-slate-900/80 border-slate-800 hover:border-blue-500/40'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800 truncate">
                      {issue.id}
                    </span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full flex-shrink-0 ${
                      issue.severity === 'CRITICAL'
                        ? 'bg-rose-500/20 text-rose-400'
                        : issue.severity === 'HIGH'
                        ? 'bg-amber-500/20 text-amber-400'
                        : issue.severity === 'MEDIUM'
                        ? 'bg-yellow-500/20 text-yellow-400'
                        : 'bg-slate-500/20 text-slate-400'
                    }`}>
                      {issue.severity}
                    </span>
                  </div>

                  <h3 className="font-semibold text-white text-sm leading-tight">{issue.title}</h3>

                  {issue.location && (
                    <div className="text-xs text-slate-400 truncate">
                      📍 {issue.location.address || `${issue.location.latitude?.toFixed(4)}, ${issue.location.longitude?.toFixed(4)}`}
                    </div>
                  )}

                  <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-800/60">
                    <span className="text-slate-400">
                      👥 {issue.report_count ?? 1} Reports
                    </span>
                    <span className={`font-semibold ${
                      issue.status === 'RESOLVED'
                        ? 'text-emerald-400'
                        : issue.status === 'IN_PROGRESS'
                        ? 'text-blue-400'
                        : issue.status === 'VERIFICATION'
                        ? 'text-amber-400'
                        : 'text-slate-300'
                    }`}>
                      {issue.status?.replace('_', ' ')}
                    </span>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
