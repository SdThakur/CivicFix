'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import dynamic from 'next/dynamic';
import { 
  Camera, 
  MapPin, 
  ArrowRight, 
  ShieldAlert,
  Loader2,
  ExternalLink,
  Info
} from 'lucide-react';
import { analyticsApi, issueApi, reportApi } from '@/lib/api';
import type { Issue } from '@/types';
import StatusBadge from '@/components/ui/StatusBadge';
import CursorAmbient from '@/components/glass/CursorAmbient';

// Dynamically import GoogleMapView for the live mini-map to avoid SSR conflicts
const GoogleMapView = dynamic(() => import('@/components/map/GoogleMapView'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full min-h-[360px] flex items-center justify-center bg-surface-canvas rounded-2xl">
      <div className="flex flex-col items-center gap-2.5 text-content-secondary">
        <Loader2 className="w-6 h-6 animate-spin text-md-red" />
        <span className="text-xs font-bold text-content-primary">Connecting Live Mini-Map...</span>
      </div>
    </div>
  ),
});

export default function LandingPage() {
  const [stats, setStats] = useState<any>(null);
  const [recentIssues, setRecentIssues] = useState<Issue[]>([]);
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      analyticsApi.getDashboard().catch(() => null),
      issueApi.list().catch(() => []),
      reportApi.list().catch(() => []),
    ])
      .then(([dash, issues, reports]) => {
        if (dash) setStats(dash);

        const list: Issue[] = Array.isArray(issues) ? [...issues] : [];

        if (Array.isArray(reports)) {
          reports.forEach((r: any) => {
            if (r.latitude && r.longitude) {
              list.push({
                id: `REP-${r.id}` as any,
                title: r.title || 'Citizen Hazard Report',
                category: r.category || 'OTHER',
                severity: (r.priority as any) || 'MEDIUM',
                status: (r.status as any) || 'SUBMITTED',
                description: r.description || '',
                priority_score: r.ai_score || 50.0,
                location_id: String(r.id),
                report_count: 1,
                created_at: r.created_at || new Date().toISOString(),
                location: {
                  id: String(r.id),
                  latitude: r.latitude,
                  longitude: r.longitude,
                  address: r.address || `${r.latitude.toFixed(4)}, ${r.longitude.toFixed(4)}`,
                },
              } as Issue);
            }
          });
        }

        // High-fidelity fallback Maryland municipal demonstration records if backend has no records yet
        if (list.length === 0) {
          list.push(
            {
              id: 'DEMO-1',
              title: 'Deep Pothole on State Circle',
              category: 'Pothole',
              severity: 'CRITICAL',
              status: 'SUBMITTED',
              description: '10-inch pothole in travel lane posing severe tire damage risk.',
              priority_score: 92,
              location_id: 'LOC-1',
              report_count: 4,
              created_at: new Date().toISOString(),
              location: { id: 'LOC-1', latitude: 38.9784, longitude: -76.4922, address: 'State Circle, Annapolis, MD' },
            } as Issue,
            {
              id: 'DEMO-2',
              title: 'Unlit Streetlight at Main & Green',
              category: 'Streetlight',
              severity: 'MEDIUM',
              status: 'IN_PROGRESS',
              description: 'Municipal fixture flickering and dark during evening commute.',
              priority_score: 64,
              location_id: 'LOC-2',
              report_count: 2,
              created_at: new Date().toISOString(),
              location: { id: 'LOC-2', latitude: 38.9765, longitude: -76.4885, address: 'Main St & Green St, Annapolis, MD' },
            } as Issue,
            {
              id: 'DEMO-3',
              title: 'Heaved Sidewalk Concrete Slab',
              category: 'Sidewalk',
              severity: 'LOW',
              status: 'RESOLVED',
              description: 'Tripping hazard leveled and resurfaced by DPW crew.',
              priority_score: 28,
              location_id: 'LOC-3',
              report_count: 1,
              created_at: new Date().toISOString(),
              location: { id: 'LOC-3', latitude: 38.9740, longitude: -76.4950, address: 'West St, Annapolis, MD' },
            } as Issue
          );
        }

        setRecentIssues(list);
      })
      .finally(() => setLoading(false));
  }, []);

  const totalReports = stats?.total_reports ?? (recentIssues.length > 0 ? recentIssues.length : 12);
  const resolvedTotal = stats?.resolved_reports_total ?? recentIssues.filter(i => i.status === 'RESOLVED').length;
  const resolutionRatePct = stats?.resolution_rate_pct != null
    ? `${stats.resolution_rate_pct}%`
    : '83.3%';
  const avgResolutionDays = stats?.avg_resolution_time_days != null
    ? `${stats.avg_resolution_time_days} days`
    : '2.4 days';

  // 6 Pipeline Steps for the Horizontal Timeline
  const workflowSteps = [
    { step: '01', title: 'Capture Photo', desc: 'Citizen snaps clear photo of hazard with auto-extracted EXIF location.' },
    { step: '02', title: 'AI Classification', desc: 'Gemini Vision identifies infrastructure category, severity, and damage scope.' },
    { step: '03', title: 'Geospatial Radar', desc: '100m proximity scan auto-detects existing reports to merge duplicate reports.' },
    { step: '04', title: 'Urgency Scoring', desc: 'Algorithmic formula ranks public safety hazard risk on a 0-100 index.' },
    { step: '05', title: 'Municipal Dispatch', desc: 'Auto-generates dispatch work orders to DPW, Transportation, or Sanitation.' },
    { step: '06', title: 'Citizen Verification', desc: 'Before/after photo audit closes the ticket with full transparent proof.' },
  ];

  return (
    <div className="space-y-1 py-4 sm:py-8">
      {/* Subtle Cursor-Following Ambient Layer (Compositor-Only, z-index: -1) */}
      <CursorAmbient />
      
      {/* ========================================================================= */}
      {/* PHASE 2 REQUIREMENT 1: SPLIT HERO WITH HEADLINE/CTAS & LIVE MINI-MAP      */}
      {/* ========================================================================= */}
      <section className="surface-card-solid p-6 sm:p-10 lg:p-12 relative overflow-hidden rounded-3xl border border-surface-border shadow-card">
        {/* Subtle Maryland Accent Top Edge Stripe */}
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-md-red via-md-gold to-md-red" />

        {/* Ambient Top-Right Luminous Spill (Mirrors background sunset atmosphere) */}
        <div 
          className="absolute -top-16 -right-16 w-[560px] h-[420px] pointer-events-none rounded-tr-3xl"
          style={{
            background: 'radial-gradient(circle at 80% 20%, rgba(255, 199, 44, 0.16) 0%, rgba(224, 58, 62, 0.06) 42%, transparent 72%)',
          }}
          aria-hidden="true"
        />
        
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
          
          {/* Left Column (7 cols): Headline, Subtext, CTAs, Real Telemetry */}
          <div className="lg:col-span-7 space-y-6 text-left">
            
            {/* Operational Standard Pill */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full liquid-glass-gold text-xs font-bold tracking-tight shadow-sm text-md-black">
              <div className="w-4 h-4 rounded-full overflow-hidden bg-white/90 p-0.5 flex items-center justify-center shadow-xs">
                <Image src="/logo.png" alt="" width={14} height={14} className="w-full h-full object-contain" />
              </div>
              <span>Maryland Civic Operations Standard</span>
            </div>

            {/* Display Heading: High-Contrast Black with Maryland Red Focus */}
            <h1 className="text-3xl sm:text-5xl lg:text-5xl font-black tracking-tight text-content-primary font-display leading-[1.12]">
              Make Your City Better with <span className="text-md-red">AI-Powered Infrastructure Ops</span>
            </h1>

            {/* High-Legibility Left-Aligned Subhead */}
            <p className="text-base sm:text-lg text-content-secondary max-w-xl font-normal leading-relaxed">
              Photograph infrastructure hazards. Computer vision classifies the issue, detects duplicates, scores priority, and dispatches municipal crews in real time.
            </p>

            {/* Primary & Secondary CTAs (Touch target >= 44px) */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3.5 pt-1">
              <Link
                href="/report"
                className="min-h-[48px] px-7 py-3 rounded-2xl btn-md-red text-white font-bold text-sm sm:text-base flex items-center justify-center gap-2.5 shadow-md hover:scale-[1.02] active:scale-[0.98] transition-all"
              >
                <Camera className="w-4 h-4 text-white" />
                <span>Report an Infrastructure Problem</span>
              </Link>

              <Link
                href="/map"
                className="min-h-[48px] px-7 py-3 rounded-2xl btn-md-gold text-md-black font-bold text-sm sm:text-base flex items-center justify-center gap-2.5 shadow-md hover:scale-[1.02] active:scale-[0.98] transition-all"
              >
                <MapPin className="w-4 h-4 text-md-black" />
                <span>Explore Live City Map</span>
              </Link>
            </div>

            {/* Real Telemetry KPI Metrics with Skeleton Loaders and Demo Label */}
            <div className="pt-4 border-t border-surface-border space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold tracking-wider text-content-secondary uppercase">
                  Live Dispatch Telemetry
                </span>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-neutral-black-06 border border-surface-border text-[10px] font-bold text-content-secondary">
                  <span className="w-1.5 h-1.5 rounded-full bg-md-gold animate-pulse" />
                  Demo data
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {/* Total Reports */}
                <div className="p-3.5 rounded-2xl bg-surface-card-subtle border border-surface-border text-left">
                  {loading ? (
                    <div className="space-y-2">
                      <div className="h-6 w-12 bg-neutral-black-06 animate-pulse rounded" />
                      <div className="h-3 w-16 bg-neutral-black-06 animate-pulse rounded" />
                    </div>
                  ) : (
                    <>
                      <div className="text-xl sm:text-2xl font-black text-content-primary font-display">
                        {totalReports}
                      </div>
                      <div className="text-[11px] font-semibold text-content-muted mt-0.5">Total Reports</div>
                    </>
                  )}
                </div>

                {/* Issues Resolved */}
                <div className="p-3.5 rounded-2xl bg-surface-card-subtle border border-surface-border text-left">
                  {loading ? (
                    <div className="space-y-2">
                      <div className="h-6 w-12 bg-neutral-black-06 animate-pulse rounded" />
                      <div className="h-3 w-16 bg-neutral-black-06 animate-pulse rounded" />
                    </div>
                  ) : (
                    <>
                      <div className="text-xl sm:text-2xl font-black text-content-primary font-display">
                        {resolvedTotal}
                      </div>
                      <div className="text-[11px] font-semibold text-content-muted mt-0.5">Issues Resolved</div>
                    </>
                  )}
                </div>

                {/* Resolution Rate */}
                <div className="p-3.5 rounded-2xl bg-surface-card-subtle border border-surface-border text-left">
                  {loading ? (
                    <div className="space-y-2">
                      <div className="h-6 w-14 bg-neutral-black-06 animate-pulse rounded" />
                      <div className="h-3 w-16 bg-neutral-black-06 animate-pulse rounded" />
                    </div>
                  ) : (
                    <>
                      <div className="text-xl sm:text-2xl font-black text-content-primary font-display">
                        {resolutionRatePct}
                      </div>
                      <div className="text-[11px] font-semibold text-content-muted mt-0.5">Resolution Rate</div>
                    </>
                  )}
                </div>

                {/* Avg Resolution Time */}
                <div className="p-3.5 rounded-2xl bg-surface-card-subtle border border-surface-border text-left">
                  {loading ? (
                    <div className="space-y-2">
                      <div className="h-6 w-14 bg-neutral-black-06 animate-pulse rounded" />
                      <div className="h-3 w-16 bg-neutral-black-06 animate-pulse rounded" />
                    </div>
                  ) : (
                    <>
                      <div className="text-xl sm:text-2xl font-black text-content-primary font-display">
                        {avgResolutionDays}
                      </div>
                      <div className="text-[11px] font-semibold text-content-muted mt-0.5">Avg Turnaround</div>
                    </>
                  )}
                </div>
              </div>
            </div>

          </div>

          {/* Right Column (5 cols): Embedded Live Mini-Map */}
          <div className="lg:col-span-5 h-[380px] sm:h-[430px] lg:h-[460px] w-full">
            <div className="h-full rounded-2xl overflow-hidden border border-surface-border relative shadow-card flex flex-col bg-surface-canvas">
              
              {/* Floating Mini-Map Glass Header */}
              <div className="absolute top-3 left-3 right-3 z-20 flex items-center justify-between pointer-events-auto">
                <div className="liquid-glass-surface specular-edge px-3 py-1.5 rounded-xl border border-surface-border text-xs font-bold text-content-primary flex items-center gap-2 shadow-sm backdrop-blur-md">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-md-red opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-md-red"></span>
                  </span>
                  <span>Live Reports</span>
                  <span className="px-1.5 py-0.2 rounded-full bg-md-gold text-md-black text-[10px] font-black">
                    {recentIssues.length} active
                  </span>
                </div>

                <Link
                  href="/map"
                  className="liquid-glass-surface specular-edge px-3 py-1.5 rounded-xl border border-surface-border text-xs font-bold text-content-primary hover:text-md-red flex items-center gap-1 shadow-sm backdrop-blur-md transition-colors"
                >
                  <span>Full Map</span>
                  <ExternalLink className="w-3 h-3 ml-0.5" />
                </Link>
              </div>

              {/* Embedded Google Map Component */}
              <GoogleMapView
                issues={recentIssues}
                selectedIssue={selectedIssue}
                onSelectIssue={setSelectedIssue}
                compact={true}
                className="w-full h-full"
              />

              {/* Floating Bottom Status Indicator */}
              <div className="absolute bottom-3 left-3 right-3 z-20 pointer-events-none">
                <div className="liquid-glass-surface specular-edge p-2.5 rounded-xl border border-surface-border text-xs text-content-primary flex items-center justify-between shadow-floating backdrop-blur-md pointer-events-auto">
                  {selectedIssue ? (
                    <div className="flex items-center gap-2 min-w-0 pr-2">
                      <StatusBadge status={selectedIssue.status} size="sm" />
                      <span className="font-bold text-xs truncate text-content-primary">
                        {selectedIssue.title}
                      </span>
                    </div>
                  ) : (
                    <span className="font-semibold text-xs text-content-secondary truncate">
                      Tap any pin to view triage data
                    </span>
                  )}
                  <Link 
                    href="/map" 
                    className="text-[11px] font-bold text-md-red hover:underline flex-shrink-0"
                  >
                    Explore all →
                  </Link>
                </div>
              </div>

            </div>
          </div>

        </div>
      </section>

      {/* ========================================================================= */}
      {/* PHASE 2 REQUIREMENT 2 & 3: HORIZONTAL TIMELINE (VERTICAL ON MOBILE)       */}
      {/* Collapsed from the 6 squircle icon badge cards into a connected track     */}
      {/* ========================================================================= */}
      <section className="space-y-6">
        <div className="border-b border-surface-border pb-3 flex flex-col sm:flex-row sm:items-end justify-between gap-2">
          <div>
            <h2 className="text-2xl font-black tracking-tight text-content-primary font-display">
              End-to-End Civic Automation
            </h2>
            <p className="text-xs sm:text-sm text-content-secondary mt-0.5">
              Continuous municipal pipeline from citizen smartphone upload to verified street-level closeout.
            </p>
          </div>
          <div className="text-[11px] font-semibold text-content-muted">
            Automated Lifecycle: 6 Milestones
          </div>
        </div>

        {/* Desktop View: Horizontal Connected Milestone Track */}
        <div className="hidden md:block surface-card-solid p-6 rounded-3xl border border-surface-border relative">
          {/* Continuous Connecting Line Behind Nodes */}
          <div className="absolute top-[42px] left-12 right-12 h-0.5 bg-neutral-black-12 z-0" />

          <div className="grid grid-cols-6 gap-3 relative z-10">
            {workflowSteps.map((step) => (
              <div key={step.step} className="group text-left space-y-3">
                {/* Milestone Node */}
                <div className="w-10 h-10 rounded-full border-2 border-md-black bg-white flex items-center justify-center font-black text-xs text-md-black shadow-sm group-hover:bg-md-gold group-hover:border-md-gold transition-colors">
                  {step.step}
                </div>
                {/* Step Details */}
                <div className="space-y-1 pr-2">
                  <h3 className="font-bold text-sm text-content-primary leading-tight group-hover:text-md-red transition-colors">
                    {step.title}
                  </h3>
                  <p className="text-xs text-content-secondary leading-snug">
                    {step.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Mobile View: Vertical Connected Timeline */}
        <div className="md:hidden surface-card-solid p-5 rounded-2xl border border-surface-border relative">
          {/* Continuous Vertical Line */}
          <div className="absolute top-8 bottom-8 left-[35px] w-0.5 bg-neutral-black-12 z-0" />

          <div className="space-y-6 relative z-10">
            {workflowSteps.map((step) => (
              <div key={step.step} className="flex items-start gap-4">
                <div className="w-9 h-9 rounded-full border-2 border-md-black bg-white flex-shrink-0 flex items-center justify-center font-black text-xs text-md-black shadow-sm">
                  {step.step}
                </div>
                <div className="space-y-0.5 pt-1">
                  <h3 className="font-bold text-sm text-content-primary">
                    {step.title}
                  </h3>
                  <p className="text-xs text-content-secondary leading-relaxed">
                    {step.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* PHASE 2 REQUIREMENT 4: ASYMMETRIC CARD RHYTHM (NO SQUIRCLE ICON BADGES)   */}
      {/* ========================================================================= */}
      <section className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-2 border-b border-surface-border pb-3">
          <div>
            <h2 className="text-2xl font-black tracking-tight text-content-primary font-display">
              Active Infrastructure Categories
            </h2>
            <p className="text-xs sm:text-sm text-content-secondary mt-0.5">
              Automated computer vision triage trained on municipal public works standards
            </p>
          </div>
          <Link 
            href="/map" 
            className="text-xs font-bold text-md-red hover:underline flex items-center gap-1 min-h-[44px] items-center"
          >
            <span>View active issues map</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Asymmetric Bento-Style Layout with Left-Aligned Text */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
          
          {/* Featured Primary Hazard: Spans 7 columns on desktop */}
          <div className="md:col-span-7 surface-card-solid p-6 rounded-3xl border border-surface-border hover:border-surface-border-strong transition-all flex flex-col justify-between space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-3 py-1 rounded-full bg-md-red-subtle text-md-red font-black text-xs tracking-wider uppercase border border-md-red/20">
                  Priority 1 Corridor Service
                </span>
                <span className="text-xs font-bold text-content-muted">Roads & Highways</span>
              </div>
              <h3 className="text-xl sm:text-2xl font-black text-content-primary font-display leading-tight">
                Roadway & Pothole Hazard Response
              </h3>
              <p className="text-sm text-content-secondary leading-relaxed">
                Automated asphalt fissure depth estimation, travel lane classification, and high-speed corridor risk scoring. Directly routes to State and County DPW asphalt patching units.
              </p>
            </div>

            <div className="pt-4 border-t border-surface-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-4 text-xs font-bold text-content-primary">
                <div>
                  <span className="text-content-muted block text-[10px] uppercase font-semibold">Triage Speed</span>
                  <span>Instant (&lt; 2s)</span>
                </div>
                <div className="h-6 w-px bg-surface-border" />
                <div>
                  <span className="text-content-muted block text-[10px] uppercase font-semibold">Dispatch Target</span>
                  <span>24 - 48 Hours</span>
                </div>
              </div>

              <Link
                href="/report?category=pothole"
                className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl btn-md-red text-white text-xs font-bold shadow-sm hover:scale-[1.02] transition-transform"
              >
                <span>Report Pothole</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Secondary Medium Card: Electrical & Lighting (Spans 5 cols) */}
          <div className="md:col-span-5 surface-card-solid p-6 rounded-3xl border border-surface-border hover:border-surface-border-strong transition-all flex flex-col justify-between space-y-4">
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 rounded-full bg-md-gold-subtle text-md-black font-black text-[11px] tracking-wide uppercase border border-md-gold/30">
                  Public Safety
                </span>
                <span className="text-xs font-bold text-content-muted">Electrical Bureau</span>
              </div>
              <h3 className="text-lg font-bold text-content-primary">
                Broken Streetlights & Signal Outages
              </h3>
              <p className="text-xs text-content-secondary leading-relaxed">
                Dark intersections and malfunctioning pedestrian signals scored with school zone and transit hub priority multipliers.
              </p>
            </div>

            <div className="pt-3 border-t border-surface-border flex items-center justify-between">
              <span className="text-xs font-semibold text-content-muted">BGE & Municipal Grid</span>
              <Link 
                href="/report?category=streetlight" 
                className="text-xs font-bold text-content-primary hover:text-md-red flex items-center gap-1"
              >
                <span>Report Light</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Tertiary Row: 4 Varied Compact Cards (3 cols each on desktop) */}
          <div className="md:col-span-3 surface-card-solid p-5 rounded-2xl border border-surface-border hover:border-surface-border-strong transition-all flex flex-col justify-between space-y-3">
            <div className="space-y-1.5">
              <div className="text-[10px] font-black tracking-wider text-content-muted uppercase">Sanitation</div>
              <h4 className="font-bold text-sm text-content-primary">Overflowing Waste & Illegal Dumping</h4>
              <p className="text-xs text-content-secondary leading-snug">
                Municipal trash container spillover and bulk debris blocking alleys.
              </p>
            </div>
            <Link href="/report?category=trash" className="text-xs font-bold text-content-primary hover:text-md-red flex items-center gap-1">
              <span>Report Waste →</span>
            </Link>
          </div>

          <div className="md:col-span-3 surface-card-solid p-5 rounded-2xl border border-surface-border hover:border-surface-border-strong transition-all flex flex-col justify-between space-y-3">
            <div className="space-y-1.5">
              <div className="text-[10px] font-black tracking-wider text-content-muted uppercase">ADA Accessibility</div>
              <h4 className="font-bold text-sm text-content-primary">Damaged Sidewalks & Curb Ramps</h4>
              <p className="text-xs text-content-secondary leading-snug">
                Concrete heaves, broken pedestrian curbs, wheelchair ramp obstacles.
              </p>
            </div>
            <Link href="/report?category=sidewalk" className="text-xs font-bold text-content-primary hover:text-md-red flex items-center gap-1">
              <span>Report Sidewalk →</span>
            </Link>
          </div>

          <div className="md:col-span-3 surface-card-solid p-5 rounded-2xl border border-surface-border hover:border-surface-border-strong transition-all flex flex-col justify-between space-y-3">
            <div className="space-y-1.5">
              <div className="text-[10px] font-black tracking-wider text-content-muted uppercase">Parks & Forestry</div>
              <h4 className="font-bold text-sm text-content-primary">Fallen Trees & Storm Hazards</h4>
              <p className="text-xs text-content-secondary leading-snug">
                Fallen branches across utility lines or blocking vehicular traffic.
              </p>
            </div>
            <Link href="/report?category=tree" className="text-xs font-bold text-content-primary hover:text-md-red flex items-center gap-1">
              <span>Report Tree →</span>
            </Link>
          </div>

          <div className="md:col-span-3 surface-card-solid p-5 rounded-2xl border border-surface-border hover:border-surface-border-strong transition-all flex flex-col justify-between space-y-3">
            <div className="space-y-1.5">
              <div className="text-[10px] font-black tracking-wider text-content-muted uppercase">Urban Care</div>
              <h4 className="font-bold text-sm text-content-primary">Graffiti & Surface Vandalism</h4>
              <p className="text-xs text-content-secondary leading-snug">
                Defaced public monuments, road signs, and municipal property.
              </p>
            </div>
            <Link href="/report?category=graffiti" className="text-xs font-bold text-content-primary hover:text-md-red flex items-center gap-1">
              <span>Report Graffiti →</span>
            </Link>
          </div>

        </div>
      </section>

      {/* ========================================================================= */}
      {/* QUICK DISPATCH CALLOUT (SOLID WHITE SURFACE WITH LIQUID GLASS ACCENT)    */}
      {/* ========================================================================= */}
      <section className="surface-card-solid p-8 sm:p-10 rounded-3xl text-left sm:text-center space-y-4 bg-surface-card-subtle border border-surface-border">
        <h3 className="text-2xl font-black text-content-primary font-display">
          Spot an Infrastructure Hazard in Your Neighborhood?
        </h3>
        <p className="text-sm text-content-secondary max-w-xl sm:mx-auto leading-relaxed">
          No paperwork, no phone holds. Snap a photo and let our AI engine handle duplicate checking, priority scoring, and crew dispatch.
        </p>
        <div className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center justify-center gap-3">
          <Link
            href="/report"
            className="inline-flex items-center justify-center gap-2 min-h-[48px] px-8 py-3 rounded-2xl btn-md-red text-white text-sm font-bold shadow-md hover:scale-105 transition-all"
          >
            <Camera className="w-4 h-4 text-white" />
            <span>Submit a Report Now</span>
          </Link>
          <Link
            href="/map"
            className="inline-flex items-center justify-center gap-2 min-h-[48px] px-8 py-3 rounded-2xl btn-md-gold text-md-black text-sm font-bold shadow-md hover:scale-105 transition-all"
          >
            <MapPin className="w-4 h-4 text-md-black" />
            <span>View Full Community Map</span>
          </Link>
        </div>
      </section>

    </div>
  );
}
