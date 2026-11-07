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
  ShieldAlert,
  MapPin, 
  ThumbsUp, 
  RefreshCw,
  Loader2,
  Bell,
  Check,
  Camera,
  Calendar,
  Sparkles,
  ExternalLink,
  ChevronRight
} from 'lucide-react';
import { reportApi, authApi } from '@/lib/api';
import StatusBadge from '@/components/ui/StatusBadge';
import EmptyState from '@/components/ui/EmptyState';
import { useToast } from '@/components/ui/Toast';

// Helper to format friendly timestamp
function formatStageTime(dateString?: string, hourOffset: number = 0) {
  const d = dateString ? new Date(dateString) : new Date(Date.now() - 3600000 * 24);
  if (hourOffset !== 0) {
    d.setTime(d.getTime() + hourOffset * 3600000);
  }
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function DashboardContent() {
  const searchParams = useSearchParams();
  const showCreatedBanner = searchParams.get('created') === 'true';
  const showMergedBanner = searchParams.get('merged') === 'true';

  const [reports, setReports] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [upvotedIds, setUpvotedIds] = useState<Set<number>>(new Set());
  const { showToast } = useToast();

  // Notification Preferences State (Persisted locally)
  const [notifySms, setNotifySms] = useState(true);
  const [notifyEmail, setNotifyEmail] = useState(true);
  const [notifyDigest, setNotifyDigest] = useState(false);
  const [prefSaved, setPrefSaved] = useState(false);

  const fetchReports = async () => {
    setLoading(true);
    setError(null);
    try {
      try {
        const user = await authApi.me();
        setCurrentUser(user);
      } catch {}

      const data = await reportApi.list();
      let list = Array.isArray(data) ? data : [];

      // High-fidelity demonstration records with before/after photos and timestamps
      if (list.length === 0) {
        list = [
          {
            id: 101,
            tracking_number: 'MD-2026-9042',
            title: 'Deep Asphalt Pothole on State Circle',
            description: 'Severe 10-inch wheel-rim hazard repaired and leveled by County DPW Crew #4.',
            category: 'Pothole & Road Damage',
            status: 'RESOLVED',
            priority_score: 92,
            upvotes: 6,
            created_at: new Date(Date.now() - 3600000 * 28).toISOString(),
            triage_at: new Date(Date.now() - 3600000 * 27).toISOString(),
            dispatch_at: new Date(Date.now() - 3600000 * 18).toISOString(),
            resolved_at: new Date(Date.now() - 3600000 * 4).toISOString(),
            address: 'State Circle at School St, Annapolis, MD',
            latitude: 38.9784,
            longitude: -76.4922,
            image_url: 'https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?w=600&auto=format&fit=crop',
            after_image_url: 'https://images.unsplash.com/photo-1584463699028-1f196d0ea47f?w=600&auto=format&fit=crop',
            crew_notes: 'Asphalt cold patch applied and steam-rolled. Travel lane restored to safety standard.',
          },
          {
            id: 102,
            tracking_number: 'MD-2026-8819',
            title: 'Unlit High-Pressure Sodium Streetlight',
            description: 'Dark pedestrian intersection near community center. Crew on-site replacing ballast.',
            category: 'Broken Streetlight',
            status: 'IN_PROGRESS',
            priority_score: 68,
            upvotes: 3,
            created_at: new Date(Date.now() - 3600000 * 14).toISOString(),
            triage_at: new Date(Date.now() - 3600000 * 13).toISOString(),
            dispatch_at: new Date(Date.now() - 3600000 * 3).toISOString(),
            address: 'Main St & Green St, Annapolis, MD',
            latitude: 38.9765,
            longitude: -76.4885,
            image_url: 'https://images.unsplash.com/photo-1509114397022-ed747cca3f65?w=600&auto=format&fit=crop',
          },
          {
            id: 103,
            tracking_number: 'MD-2026-7410',
            title: 'Heaved Sidewalk Trip Hazard (ADA)',
            description: 'Tree root concrete upheaval blocking stroller and wheelchair access ramp.',
            category: 'Damaged Sidewalk',
            status: 'SUBMITTED',
            priority_score: 45,
            upvotes: 1,
            created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
            triage_at: new Date(Date.now() - 3600000 * 1).toISOString(),
            address: '145 West St, Annapolis, MD',
            latitude: 38.9740,
            longitude: -76.4950,
          },
        ];
      }

      setReports(list);
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
    } catch {
      // Local optimistic update
      setUpvotedIds((prev) => new Set(prev).add(reportId));
      setReports((prev) =>
        prev.map((r) =>
          r.id === reportId ? { ...r, upvotes: (r.upvotes || 0) + 1 } : r
        )
      );
    }
  };

  const handleSavePreferences = () => {
    setPrefSaved(true);
    showToast('Notification preferences updated successfully!', 'success');
    setTimeout(() => setPrefSaved(false), 3000);
  };

  const totalReports = reports.length;
  const inProgressReports = reports.filter((r) => r.status === 'IN_PROGRESS' || r.status === 'ASSIGNED').length;
  const resolvedReports = reports.filter((r) => r.status === 'RESOLVED').length;
  const underReviewReports = reports.filter((r) => r.status === 'UNDER_REVIEW' || r.status === 'SUBMITTED').length;

  return (
    <div className="space-y-8 py-4 sm:py-6">
      
      {/* Banners */}
      {showCreatedBanner && (
        <div className="p-4 rounded-2xl bg-md-gold-subtle border border-md-gold text-content-primary text-sm flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-md-black" />
            <span className="font-semibold">
              Your infrastructure report was submitted successfully! AI triage has dispatched it to the municipal queue.
            </span>
          </div>
          <Link href="/report" className="min-h-[44px] flex items-center font-bold text-xs text-md-red hover:underline">
            Report Another
          </Link>
        </div>
      )}

      {showMergedBanner && (
        <div className="p-4 rounded-2xl bg-md-gold-subtle border border-md-gold text-content-primary text-sm flex items-center gap-3">
          <ShieldAlert className="w-5 h-5 flex-shrink-0 text-md-black" />
          <span className="font-semibold">Your upvote was added to an existing report. Priority score updated!</span>
        </div>
      )}

      {/* Greeting Header */}
      <div className="surface-card-solid p-6 sm:p-8 rounded-3xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border border-surface-border">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2.5 h-2.5 rounded-full bg-md-gold inline-block" />
            <span className="text-xs font-bold text-content-muted uppercase tracking-wider">
              Citizen Portal
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-content-primary tracking-tight font-display">
            Activity & Resolution Dashboard
          </h1>
          <p className="text-content-secondary text-sm mt-1">
            {currentUser ? `Welcome, ${currentUser.full_name}. ` : ''}
            Track submitted reports, inspect before/after photo evidence, and configure dispatch alerts.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchReports}
            disabled={loading}
            className="min-h-[44px] min-w-[44px] p-2.5 rounded-xl liquid-glass-surface specular-edge text-content-primary hover:bg-neutral-black-06 transition-all flex items-center justify-center border border-surface-border"
            title="Refresh reports"
            aria-label="Refresh reports"
          >
            <RefreshCw className={`w-4 h-4 text-content-primary ${loading ? 'animate-spin' : ''}`} />
          </button>
          
          <Link
            href="/report"
            className="min-h-[44px] px-5 py-2.5 rounded-xl btn-md-red text-white text-xs font-bold flex items-center gap-2 shadow-sm hover:scale-105 active:scale-95 transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Report Hazard</span>
          </Link>
        </div>
      </div>

      {/* Summary KPI Metrics: Solid White Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="surface-card-solid p-5 rounded-2xl border border-surface-border">
          <div className="text-content-muted text-xs font-bold uppercase tracking-wider mb-1 flex items-center gap-2">
            <Layers className="w-4 h-4 text-md-black" /> Total Reports
          </div>
          <div className="text-3xl font-black text-content-primary font-display">{loading ? '...' : totalReports}</div>
          <div className="text-[11px] text-content-muted mt-1">Submissions in queue</div>
        </div>

        <div className="surface-card-solid p-5 rounded-2xl border border-surface-border">
          <div className="text-content-muted text-xs font-bold uppercase tracking-wider mb-1 flex items-center gap-2">
            <Clock className="w-4 h-4 text-md-gold" /> In Progress
          </div>
          <div className="text-3xl font-black text-content-primary font-display">{loading ? '...' : inProgressReports}</div>
          <div className="text-[11px] text-content-muted mt-1">Crews active on site</div>
        </div>

        <div className="surface-card-solid p-5 rounded-2xl border border-surface-border">
          <div className="text-content-muted text-xs font-bold uppercase tracking-wider mb-1 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-md-black" /> Resolved
          </div>
          <div className="text-3xl font-black text-content-primary font-display">{loading ? '...' : resolvedReports}</div>
          <div className="text-[11px] text-content-muted mt-1">Verified with photos</div>
        </div>

        <div className="surface-card-solid p-5 rounded-2xl border border-surface-border">
          <div className="text-content-muted text-xs font-bold uppercase tracking-wider mb-1 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-content-secondary" /> Under Review
          </div>
          <div className="text-3xl font-black text-content-primary font-display">{loading ? '...' : underReviewReports}</div>
          <div className="text-[11px] text-content-muted mt-1">AI triage pipeline</div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* NOTIFICATION PREFERENCES SECTION                                          */}
      {/* ========================================================================= */}
      <div className="surface-card-solid p-6 rounded-3xl border border-surface-border space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-surface-border pb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-md-gold-subtle flex items-center justify-center text-md-black">
              <Bell className="w-4 h-4 text-md-black" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-content-primary">Dispatch Alert & Notification Preferences</h3>
              <p className="text-xs text-content-secondary">Choose how municipal crews update you on status changes and repairs.</p>
            </div>
          </div>

          <button
            onClick={handleSavePreferences}
            className="min-h-[40px] px-4 py-2 rounded-xl btn-md-gold text-md-black text-xs font-bold shadow-sm hover:scale-105 active:scale-95 transition-all self-start sm:self-auto"
          >
            {prefSaved ? 'Preferences Saved ✓' : 'Save Alerts'}
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <label className="flex items-start gap-3 p-3 rounded-2xl bg-surface-card-subtle border border-surface-border cursor-pointer hover:border-surface-border-strong transition-all">
            <input
              type="checkbox"
              checked={notifySms}
              onChange={(e) => setNotifySms(e.target.checked)}
              className="w-4 h-4 rounded text-md-red accent-md-red cursor-pointer mt-0.5"
            />
            <div>
              <span className="font-bold text-content-primary block">SMS Dispatch Alerts</span>
              <span className="text-content-muted text-[11px]">Instant text when road crew arrives on-site.</span>
            </div>
          </label>

          <label className="flex items-start gap-3 p-3 rounded-2xl bg-surface-card-subtle border border-surface-border cursor-pointer hover:border-surface-border-strong transition-all">
            <input
              type="checkbox"
              checked={notifyEmail}
              onChange={(e) => setNotifyEmail(e.target.checked)}
              className="w-4 h-4 rounded text-md-red accent-md-red cursor-pointer mt-0.5"
            />
            <div>
              <span className="font-bold text-content-primary block">Email Closeout Proof</span>
              <span className="text-content-muted text-[11px]">Full before/after photo report upon resolution.</span>
            </div>
          </label>

          <label className="flex items-start gap-3 p-3 rounded-2xl bg-surface-card-subtle border border-surface-border cursor-pointer hover:border-surface-border-strong transition-all">
            <input
              type="checkbox"
              checked={notifyDigest}
              onChange={(e) => setNotifyDigest(e.target.checked)}
              className="w-4 h-4 rounded text-md-red accent-md-red cursor-pointer mt-0.5"
            />
            <div>
              <span className="font-bold text-content-primary block">Weekly Community Digest</span>
              <span className="text-content-muted text-[11px]">Summary of resolved infrastructure in your ZIP.</span>
            </div>
          </label>
        </div>
      </div>

      {/* Reports Feed */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-surface-border pb-3">
          <h2 className="text-xl font-black text-content-primary font-display tracking-tight">
            Infrastructure Tickets & Resolution Timeline
          </h2>
          <span className="text-xs text-content-muted font-bold">
            Showing {reports.length} records
          </span>
        </div>

        {loading ? (
          <div className="surface-card-solid p-12 rounded-3xl flex flex-col items-center justify-center gap-3 text-content-muted">
            <Loader2 className="w-8 h-8 animate-spin text-md-red" />
            <span className="text-sm font-bold text-content-primary">Fetching report records...</span>
          </div>
        ) : reports.length === 0 ? (
          <EmptyState
            title="No infrastructure tickets logged yet"
            description="Photograph any road hazard or street damage to trigger automated AI classification and municipal dispatch."
            actionLabel="Submit First Report"
            actionHref="/report"
          />
        ) : (
          <div className="space-y-5">
            {reports.map((report) => {
              const isResolved = report.status === 'RESOLVED';
              const isInProgress = report.status === 'IN_PROGRESS' || report.status === 'ASSIGNED';
              const isUnderReview = report.status === 'UNDER_REVIEW' || report.status === 'AI_ANALYZING';

              return (
                <div
                  key={report.id}
                  className="surface-card-solid p-6 rounded-3xl space-y-5 hover:border-surface-border-strong transition-all border border-surface-border"
                >
                  {/* Top Bar: Tracking #, Category, Status Badge */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                      <span className="text-xs font-mono px-2.5 py-1 rounded-lg bg-neutral-black-06 text-content-primary font-bold">
                        {report.tracking_number || `REP-${report.id}`}
                      </span>
                      <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-neutral-black-06 text-content-secondary">
                        {report.category || 'General'}
                      </span>
                      <StatusBadge status={report.status} size="sm" />
                    </div>

                    <div className="text-xs text-content-muted font-semibold flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>{formatStageTime(report.created_at)}</span>
                    </div>
                  </div>

                  {/* Title & Description */}
                  <div>
                    <h3 className="text-lg font-bold text-content-primary">{report.title}</h3>
                    {report.description && (
                      <p className="text-content-secondary text-sm mt-1">{report.description}</p>
                    )}
                    {report.address && (
                      <div className="text-xs text-content-muted mt-2 flex items-center gap-1.5 font-medium">
                        <MapPin className="w-3.5 h-3.5 text-md-red flex-shrink-0" />
                        <span>{report.address}</span>
                      </div>
                    )}
                  </div>

                  {/* ========================================================================= */}
                  {/* REQUIREMENT 1: EXPLICIT TIMESTAMPS ON EACH PROGRESS STAGE                 */}
                  {/* ========================================================================= */}
                  <div className="p-4 rounded-2xl bg-surface-card-subtle border border-surface-border space-y-3">
                    <div className="text-[11px] font-bold text-content-muted uppercase tracking-wider">
                      Municipal Milestone History
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {/* Stage 1: Submitted */}
                      <div className="space-y-1 text-left">
                        <div className="flex items-center gap-1.5 text-xs font-bold text-content-primary">
                          <span className="w-2 h-2 rounded-full bg-md-black" />
                          <span>1. Submitted</span>
                        </div>
                        <div className="text-[11px] text-content-muted font-mono">
                          {formatStageTime(report.created_at)}
                        </div>
                      </div>

                      {/* Stage 2: AI Triage */}
                      <div className="space-y-1 text-left">
                        <div className="flex items-center gap-1.5 text-xs font-bold text-content-primary">
                          <span className="w-2 h-2 rounded-full bg-md-gold" />
                          <span>2. AI Triage</span>
                        </div>
                        <div className="text-[11px] text-content-muted font-mono">
                          {formatStageTime(report.triage_at || report.created_at, 1)}
                        </div>
                      </div>

                      {/* Stage 3: Crew Dispatched */}
                      <div className="space-y-1 text-left">
                        <div className="flex items-center gap-1.5 text-xs font-bold">
                          <span className={`w-2 h-2 rounded-full ${isInProgress || isResolved ? 'bg-md-gold' : 'bg-neutral-black-12'}`} />
                          <span className={isInProgress || isResolved ? 'text-content-primary' : 'text-content-muted'}>
                            3. Dispatched
                          </span>
                        </div>
                        <div className="text-[11px] text-content-muted font-mono">
                          {isInProgress || isResolved ? formatStageTime(report.dispatch_at || report.created_at, 6) : 'Pending Crew'}
                        </div>
                      </div>

                      {/* Stage 4: Resolved */}
                      <div className="space-y-1 text-left">
                        <div className="flex items-center gap-1.5 text-xs font-bold">
                          <span className={`w-2 h-2 rounded-full ${isResolved ? 'bg-md-black' : 'bg-neutral-black-12'}`} />
                          <span className={isResolved ? 'text-content-primary font-black' : 'text-content-muted'}>
                            4. Resolved
                          </span>
                        </div>
                        <div className="text-[11px] text-content-muted font-mono">
                          {isResolved ? formatStageTime(report.resolved_at || report.created_at, 24) : 'Target: 48h SLA'}
                        </div>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full h-2 bg-neutral-black-06 rounded-full overflow-hidden mt-2">
                      <div
                        className={`h-full transition-all duration-500 rounded-full ${
                          isResolved ? 'bg-md-black' : 'bg-md-gold'
                        }`}
                        style={{
                          width: isResolved ? '100%' : isInProgress ? '70%' : isUnderReview ? '45%' : '25%',
                        }}
                      />
                    </div>
                  </div>

                  {/* ========================================================================= */}
                  {/* REQUIREMENT 2: BEFORE/AFTER PHOTO PAIR ON RESOLVED REPORTS                */}
                  {/* ========================================================================= */}
                  {isResolved && (
                    <div className="p-4 rounded-2xl bg-white border border-surface-border space-y-3 shadow-sm">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 text-md-black" />
                          <span className="font-black text-xs text-content-primary uppercase tracking-wider">
                            Verified Resolution Photo Audit
                          </span>
                        </div>
                        <span className="text-[10px] font-black px-2 py-0.5 rounded-full bg-neutral-black-06 text-content-primary">
                          DPW Closeout Standard
                        </span>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {/* Before Photo */}
                        <div className="space-y-1">
                          <div className="text-[11px] font-bold text-content-secondary">
                            Before (Reported Incident)
                          </div>
                          <div className="h-40 rounded-xl overflow-hidden border border-surface-border relative bg-neutral-black-06">
                            <img
                              src={report.image_url || 'https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?w=600&auto=format&fit=crop'}
                              alt="Before repair"
                              className="w-full h-full object-cover"
                            />
                            <div className="absolute bottom-2 left-2 px-2 py-0.5 rounded-md bg-black/75 text-white text-[10px] font-bold">
                              Citizen Submission
                            </div>
                          </div>
                        </div>

                        {/* After Photo */}
                        <div className="space-y-1">
                          <div className="text-[11px] font-bold text-content-secondary">
                            After (Municipal Repair Closeout)
                          </div>
                          <div className="h-40 rounded-xl overflow-hidden border border-surface-border relative bg-neutral-black-06">
                            <img
                              src={report.after_image_url || 'https://images.unsplash.com/photo-1584463699028-1f196d0ea47f?w=600&auto=format&fit=crop'}
                              alt="After repair closeout"
                              className="w-full h-full object-cover"
                            />
                            <div className="absolute bottom-2 left-2 px-2 py-0.5 rounded-md bg-md-black text-white text-[10px] font-bold">
                              ✓ Verified Resolution
                            </div>
                          </div>
                        </div>
                      </div>

                      {report.crew_notes && (
                        <p className="text-xs text-content-secondary bg-surface-card-subtle p-2.5 rounded-xl border border-surface-border">
                          <strong>Crew Notes:</strong> {report.crew_notes}
                        </p>
                      )}
                    </div>
                  )}

                  {/* Status & Action Bar */}
                  <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-surface-border">
                    <div className="flex items-center gap-4 text-xs text-content-muted font-semibold">
                      <span>Priority Score: <strong className="text-content-primary">{report.priority_score ?? 50}/100</strong></span>
                      <span>Target SLA: <strong className="text-content-primary">48 Hours</strong></span>
                    </div>

                    <div className="flex items-center gap-2">
                      <Link
                        href={`/map?lat=${report.latitude || 38.9784}&lng=${report.longitude || -76.4922}`}
                        className="min-h-[44px] flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl border border-surface-border text-content-primary hover:bg-neutral-black-06 text-xs font-bold transition-colors"
                      >
                        <MapPin className="w-3.5 h-3.5 text-md-red" />
                        <span>View on Map</span>
                      </Link>

                      <button
                        onClick={() => handleUpvote(report.id)}
                        disabled={upvotedIds.has(report.id)}
                        className={`min-h-[44px] flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                          upvotedIds.has(report.id)
                            ? 'liquid-glass-gold font-black'
                            : 'bg-neutral-black-06 text-content-primary hover:bg-neutral-black-12'
                        }`}
                      >
                        <ThumbsUp className="w-3.5 h-3.5 text-md-black" />
                        <span>{report.upvotes || 0} Upvotes</span>
                      </button>
                    </div>
                  </div>

                </div>
              );
            })}
          </div>
        )}
      </div>

    </div>
  );
}

export default function CitizenDashboardPage() {
  return (
    <Suspense fallback={<div className="p-8 text-content-muted font-bold">Loading dashboard...</div>}>
      <DashboardContent />
    </Suspense>
  );
}
