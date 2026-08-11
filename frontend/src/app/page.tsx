'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  Camera, 
  Cpu, 
  MapPin, 
  Zap, 
  Building2, 
  CheckCircle2, 
  ArrowRight, 
  Sparkles 
} from 'lucide-react';
import { analyticsApi } from '@/lib/api';

export default function LandingPage() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    analyticsApi.getDashboard()
      .then((data) => setStats(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  // Compute all values from real API data — no hardcoded fallbacks
  const totalReports = stats?.total_reports ?? null;
  const resolvedTotal = stats?.resolved_reports_total ?? null;
  const resolutionRatePct = stats?.resolution_rate_pct != null
    ? `${stats.resolution_rate_pct}%`
    : null;
  const avgResolutionDays = stats?.avg_resolution_time_days != null
    ? `${stats.avg_resolution_time_days} days`
    : null;

  const categories = [
    { title: 'Pothole & Road Damage', icon: '🕳️', color: 'border-amber-500/30 bg-amber-500/10' },
    { title: 'Broken Streetlight', icon: '💡', color: 'border-blue-500/30 bg-blue-500/10' },
    { title: 'Overflowing Trash', icon: '🗑️', color: 'border-emerald-500/30 bg-emerald-500/10' },
    { title: 'Damaged Sidewalk', icon: '🚧', color: 'border-purple-500/30 bg-purple-500/10' },
    { title: 'Fallen Tree / Hazard', icon: '🌳', color: 'border-teal-500/30 bg-teal-500/10' },
    { title: 'Graffiti & Vandalism', icon: '🎨', color: 'border-rose-500/30 bg-rose-500/10' },
  ];

  const workflowSteps = [
    { step: '01', title: 'Capture Photo', desc: 'Snap or upload a photo of any damaged city infrastructure.', icon: Camera },
    { step: '02', title: 'AI Classification', desc: 'Computer vision identifies issue category, damage score & severity.', icon: Cpu },
    { step: '03', title: 'Geospatial GPS', desc: 'Auto-extracts location and checks for nearby duplicate reports.', icon: MapPin },
    { step: '04', title: 'Smart Priority', desc: 'Priority algorithm scores urgency based on risk & community density.', icon: Zap },
    { step: '05', title: 'Department Dispatch', desc: 'Direct routing to Public Works, Sanitation, or Electrical team.', icon: Building2 },
    { step: '06', title: 'Citizen Verification', desc: 'Track repair progress and verify completion with before/after photos.', icon: CheckCircle2 },
  ];

  return (
    <div className="space-y-20 py-6">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-3xl glass-panel border border-slate-800 p-8 sm:p-14 text-center space-y-8">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-blue-600/15 blur-[120px] pointer-events-none rounded-full" />
        
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400 text-xs font-semibold uppercase tracking-wider">
          <Sparkles className="w-4 h-4" /> Next-Gen Civic Tech Platform
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight max-w-4xl mx-auto leading-tight">
          Make Your City Better with <span className="gradient-text">AI-Powered Infrastructure Ops</span>
        </h1>

        <p className="text-lg sm:text-xl text-slate-300 max-w-2xl mx-auto font-light leading-relaxed">
          Photograph infrastructure hazards. Computer vision classifies the issue, detects duplicates, scores priority, and dispatches municipal crews in real time.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Link
            href="/report"
            className="w-full sm:w-auto px-8 py-4 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-base flex items-center justify-center gap-3 shadow-xl shadow-blue-600/30 transition-all hover:scale-105"
          >
            <Camera className="w-5 h-5" />
            Report an Infrastructure Problem
          </Link>
          <Link
            href="/map"
            className="w-full sm:w-auto px-8 py-4 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-200 font-semibold text-base border border-slate-700 flex items-center justify-center gap-3 transition-all hover:border-slate-600"
          >
            <MapPin className="w-5 h-5 text-blue-400" />
            Explore Live City Map
          </Link>
        </div>

        {/* Live System Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-8 border-t border-slate-800/80 max-w-4xl mx-auto">
          {/* Total Reports */}
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
            {loading ? (
              <div className="h-9 w-16 bg-slate-800 rounded-lg animate-pulse mb-1" />
            ) : (
              <div className="text-3xl font-extrabold text-white">
                {totalReports !== null ? totalReports.toLocaleString() : '—'}
              </div>
            )}
            <div className="text-xs text-slate-400 font-medium">Total Reports</div>
          </div>

          {/* Issues Resolved */}
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
            {loading ? (
              <div className="h-9 w-16 bg-slate-800 rounded-lg animate-pulse mb-1" />
            ) : (
              <div className="text-3xl font-extrabold text-emerald-400">
                {resolvedTotal !== null ? resolvedTotal.toLocaleString() : '—'}
              </div>
            )}
            <div className="text-xs text-slate-400 font-medium">Issues Resolved</div>
          </div>

          {/* Resolution Rate */}
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
            {loading ? (
              <div className="h-9 w-14 bg-slate-800 rounded-lg animate-pulse mb-1" />
            ) : (
              <div className="text-3xl font-extrabold text-amber-400">
                {resolutionRatePct !== null ? resolutionRatePct : '—'}
              </div>
            )}
            <div className="text-xs text-slate-400 font-medium">Resolution Rate</div>
          </div>

          {/* Avg Resolution Time */}
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
            {loading ? (
              <div className="h-9 w-20 bg-slate-800 rounded-lg animate-pulse mb-1" />
            ) : (
              <div className="text-3xl font-extrabold text-blue-400">
                {avgResolutionDays !== null ? avgResolutionDays : '—'}
              </div>
            )}
            <div className="text-xs text-slate-400 font-medium">Avg Resolution Time</div>
          </div>
        </div>
      </section>

      {/* Infrastructure Categories Grid */}
      <section className="space-y-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-white tracking-tight">Active Infrastructure Categories</h2>
            <p className="text-slate-400 text-sm">Automated classification powered by Gemini Vision</p>
          </div>
          <Link href="/map" className="text-sm font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1">
            View active issues map <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {categories.map((cat, idx) => (
            <div
              key={idx}
              className={`p-5 rounded-2xl border ${cat.color} flex items-center gap-4 hover:scale-[1.02] transition-transform`}
            >
              <div className="text-3xl p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
                {cat.icon}
              </div>
              <div>
                <h3 className="font-semibold text-slate-100">{cat.title}</h3>
                <span className="text-xs text-slate-400 font-medium">Live Triage Active</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* How it Works Timeline */}
      <section className="space-y-8 py-6">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <h2 className="text-3xl font-bold text-white tracking-tight">End-to-End Civic Automation</h2>
          <p className="text-slate-400 text-sm">From citizen photo capture to municipal work order verification</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {workflowSteps.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                className="p-6 rounded-2xl glass-card border border-slate-800 space-y-4 hover:border-blue-500/40 transition-colors relative group"
              >
                <div className="flex items-center justify-between">
                  <div className="w-12 h-12 rounded-xl bg-blue-600/10 border border-blue-500/30 flex items-center justify-center text-blue-400 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                    <Icon className="w-6 h-6" />
                  </div>
                  <span className="text-2xl font-black text-slate-700 tracking-wider">{item.step}</span>
                </div>
                <h3 className="text-lg font-semibold text-white">{item.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{item.desc}</p>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
