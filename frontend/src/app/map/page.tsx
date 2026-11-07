'use client';

import React, { useState, useEffect, useCallback, Suspense } from 'react';
import dynamic from 'next/dynamic';
import { useSearchParams } from 'next/navigation';
import { 
  MapPin, 
  Loader2, 
  RefreshCw, 
  AlertCircle, 
  Layers, 
  Filter, 
  Map as MapIcon, 
  List, 
  ChevronUp, 
  ChevronDown, 
  Maximize2, 
  Minimize2,
  Search,
  ArrowUpDown
} from 'lucide-react';
import { issueApi, reportApi } from '@/lib/api';
import { useIssuesInBounds } from '@/lib/supabase/queries';
import type { Issue } from '@/types';
import StatusBadge from '@/components/ui/StatusBadge';
import EmptyState from '@/components/ui/EmptyState';

// Dynamically import GoogleMapView to ensure clean browser-only initialization
const GoogleMapView = dynamic(() => import('@/components/map/GoogleMapView'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full min-h-[500px] flex items-center justify-center surface-card-solid rounded-3xl">
      <div className="flex flex-col items-center gap-3 text-content-secondary">
        <Loader2 className="w-8 h-8 animate-spin text-md-red" />
        <span className="text-sm font-bold text-content-primary">Initializing Google Maps Engine...</span>
      </div>
    </div>
  ),
});

const CATEGORY_FILTERS = ['ALL', 'Pothole', 'Streetlight', 'Trash', 'Sidewalk', 'Graffiti', 'Road Damage'];
const STATUS_FILTERS = ['ALL', 'SUBMITTED', 'IN_PROGRESS', 'VERIFICATION', 'RESOLVED'];

function MapPageContent() {
  const searchParams = useSearchParams();
  const latParam = searchParams.get('lat');
  const lngParam = searchParams.get('lng');

  const initialCenter = latParam && lngParam ? {
    lat: parseFloat(latParam),
    lng: parseFloat(lngParam),
  } : null;

  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null);
  
  // Phase 3 Features:
  // 1. Accessible List View Toggle (WCAG 2.1 AA)
  const [viewMode, setViewMode] = useState<'map' | 'list'>('map');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'priority' | 'date' | 'reports'>('priority');

  // 2. Mobile Draggable Bottom Sheet State ('peek' | 'half' | 'full')
  const [sheetState, setSheetState] = useState<'peek' | 'half' | 'full'>('peek');

  // Supabase RPC Viewport Bounds Loading (debounced on map idle)
  const [viewportBounds, setViewportBounds] = useState<{
    minLat: number;
    maxLat: number;
    minLng: number;
    maxLng: number;
  } | null>(null);

  const { data: boundedIssues } = useIssuesInBounds({
    minLat: viewportBounds?.minLat ?? 38.5,
    maxLat: viewportBounds?.maxLat ?? 39.5,
    minLng: viewportBounds?.minLng ?? -77.5,
    maxLng: viewportBounds?.maxLng ?? -76.0,
    categoryFilter: selectedCategory !== 'ALL' ? selectedCategory : null,
    statusFilter: selectedStatus !== 'ALL' ? selectedStatus : null,
    enabled: Boolean(viewportBounds),
  });

  useEffect(() => {
    if (boundedIssues && boundedIssues.length > 0) {
      setIssues(
        boundedIssues.map((b: any) => ({
          id: b.id,
          title: b.title,
          category: b.category,
          status: b.status as any,
          severity: (b.priority_level === 'URGENT' ? 'CRITICAL' : (b.priority_level || 'MEDIUM')) as any,
          location_id: b.id,
          location: {
            id: b.id,
            latitude: b.lat,
            longitude: b.lng,
            address: b.address || '',
            neighborhood: b.neighborhood || '',
          },
          priority: b.priority_level || 'MEDIUM',
          latitude: b.lat,
          longitude: b.lng,
          address: b.address || '',
          neighborhood: b.neighborhood || '',
          report_count: b.duplicate_count ? b.duplicate_count + 1 : 1,
          created_at: b.created_at,
          updated_at: b.created_at,
          priority_score: b.priority_score || 50,
        })) as any
      );
    }
  }, [boundedIssues]);

  const fetchIssues = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (selectedCategory !== 'ALL') params.category = selectedCategory.toLowerCase();
      if (selectedStatus !== 'ALL') params.status = selectedStatus;

      const [issueData, reportData] = await Promise.all([
        issueApi.list(params).catch(() => []),
        reportApi.list().catch(() => []),
      ]);

      const formattedIssues: Issue[] = Array.isArray(issueData) ? [...issueData] : [];

      // Convert citizen reports into mappable issues if not already present
      if (Array.isArray(reportData)) {
        reportData.forEach((r: any) => {
          if (r.latitude && r.longitude) {
            formattedIssues.push({
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

      // Seeded demonstration records if backend has no active data
      if (formattedIssues.length === 0) {
        formattedIssues.push(
          {
            id: 'DEMO-1',
            title: 'Deep Pothole on State Circle',
            category: 'Pothole',
            severity: 'CRITICAL',
            status: 'SUBMITTED',
            description: '10-inch asphalt fissure in travel lane posing severe tire damage risk.',
            priority_score: 92,
            location_id: 'LOC-1',
            report_count: 4,
            created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
            location: { id: 'LOC-1', latitude: 38.9784, longitude: -76.4922, address: 'State Circle, Annapolis, MD' },
          } as Issue,
          {
            id: 'DEMO-2',
            title: 'Unlit Streetlight at Main & Green',
            category: 'Streetlight',
            severity: 'MEDIUM',
            status: 'IN_PROGRESS',
            description: 'Municipal fixture dark during evening hours along high-pedestrian corridor.',
            priority_score: 64,
            location_id: 'LOC-2',
            report_count: 2,
            created_at: new Date(Date.now() - 3600000 * 8).toISOString(),
            location: { id: 'LOC-2', latitude: 38.9765, longitude: -76.4885, address: 'Main St & Green St, Annapolis, MD' },
          } as Issue,
          {
            id: 'DEMO-3',
            title: 'Heaved Sidewalk Concrete Slab',
            category: 'Sidewalk',
            severity: 'LOW',
            status: 'RESOLVED',
            description: 'ADA tripping hazard leveled and resurfaced by DPW asphalt crew.',
            priority_score: 28,
            location_id: 'LOC-3',
            report_count: 1,
            created_at: new Date(Date.now() - 3600000 * 24).toISOString(),
            location: { id: 'LOC-3', latitude: 38.9740, longitude: -76.4950, address: 'West St, Annapolis, MD' },
          } as Issue
        );
      }

      setIssues(formattedIssues);

      // Auto-select target issue if initialCenter is provided
      if (initialCenter) {
        const target = formattedIssues.find((i) => {
          if (!i.location?.latitude || !i.location?.longitude) return false;
          return Math.abs(i.location.latitude - initialCenter.lat) < 0.0001 &&
                 Math.abs(i.location.longitude - initialCenter.lng) < 0.0001;
        });
        if (target) {
          setSelectedIssue(target);
        }
      }
    } catch (err: any) {
      setError('Unable to load issues from server. Make sure the backend is active.');
      setIssues([]);
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, selectedStatus, initialCenter?.lat, initialCenter?.lng]);

  useEffect(() => {
    fetchIssues();
  }, [fetchIssues]);

  const mappableIssues = issues.filter(
    (i) => i.location?.latitude && i.location?.longitude
  );

  // Filtered and sorted issues for the accessible list view
  const filteredIssues = mappableIssues
    .filter((issue) => {
      if (!searchQuery) return true;
      const query = searchQuery.toLowerCase();
      return (
        issue.title.toLowerCase().includes(query) ||
        issue.category.toLowerCase().includes(query) ||
        issue.location?.address.toLowerCase().includes(query)
      );
    })
    .sort((a, b) => {
      if (sortBy === 'priority') return (b.priority_score || 0) - (a.priority_score || 0);
      if (sortBy === 'reports') return (b.report_count || 1) - (a.report_count || 1);
      return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime();
    });

  // Switch to map and focus on an issue from the accessible list
  const handleLocateOnMap = (issue: Issue) => {
    setSelectedIssue(issue);
    setViewMode('map');
    setSheetState('peek');
  };

  return (
    <div className="space-y-3 py-4 sm:py-8">
      <div className="flex-1 flex flex-col min-h-0 space-y-2.5 h-full overflow-hidden">
        {/* Top Header Card — Styled to match Landing Page Hero aesthetics */}
        <div className="surface-card-solid p-6 sm:p-10 lg:p-12 relative overflow-hidden rounded-3xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6 border border-surface-border shadow-card flex-shrink-0">
          {/* Subtle Maryland Accent Top Edge Stripe */}
          <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-md-red via-md-gold to-md-red" />

          {/* Ambient Top-Right Spill */}
          <div 
            className="absolute -top-16 -right-16 w-[420px] h-[300px] pointer-events-none rounded-tr-3xl"
            style={{
              background: 'radial-gradient(circle at 80% 20%, rgba(255, 199, 44, 0.12) 0%, rgba(224, 58, 62, 0.04) 40%, transparent 70%)',
            }}
            aria-hidden="true"
          />

          <div className="space-y-2 z-10 text-left">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full liquid-glass-gold text-xs font-bold tracking-tight shadow-sm text-md-black">
              <span className="w-2 h-2 rounded-full bg-md-red animate-pulse" />
              <span>Live Geospatial Operations Standard</span>
            </div>

            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black text-content-primary tracking-tight font-display leading-[1.15]">
              Public Infrastructure <span className="text-md-red">City Map</span>
            </h1>

            <p className="text-xs sm:text-sm text-content-secondary max-w-xl font-normal leading-relaxed">
              Real-time geospatial radar of road hazards, work orders, cluster density, and verified repairs.
            </p>
          </div>

          <div className="flex items-center gap-3 flex-wrap z-10">
            {/* Accessible List / Map View Toggle */}
            <div className="flex items-center rounded-2xl bg-neutral-black-06 p-1 border border-surface-border" role="group" aria-label="View Mode">
              <button
                onClick={() => setViewMode('map')}
                className={`min-h-[40px] px-4 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all ${
                  viewMode === 'map'
                    ? 'bg-white text-md-black shadow-sm font-black'
                    : 'text-content-secondary hover:text-content-primary'
                }`}
                aria-pressed={viewMode === 'map'}
              >
                <MapIcon className="w-4 h-4" />
                <span>Map View</span>
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`min-h-[40px] px-4 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all ${
                  viewMode === 'list'
                    ? 'bg-white text-md-black shadow-sm font-black'
                    : 'text-content-secondary hover:text-content-primary'
                }`}
                aria-pressed={viewMode === 'list'}
              >
                <List className="w-4 h-4" />
                <span>Accessible List</span>
              </button>
            </div>

            <button
              onClick={fetchIssues}
              disabled={loading}
              className="min-h-[44px] min-w-[44px] px-4 py-2 rounded-2xl liquid-glass-surface specular-edge text-content-primary hover:bg-neutral-black-06 active:scale-95 transition-all flex items-center gap-2 border border-surface-border text-xs font-bold"
              title="Refresh map incidents"
              aria-label="Refresh incident feed"
            >
              <RefreshCw className={`w-4 h-4 text-content-primary ${loading ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Refresh</span>
            </button>
            
            <div className="px-4 py-2 rounded-2xl bg-neutral-black-06 border border-surface-border text-xs font-bold text-content-primary flex items-center gap-1.5">
              <span className="text-md-red font-black text-sm">{mappableIssues.length}</span> Mapped
            </div>
          </div>
        </div>

        {/* Floating Filter Pills Bar in Concentric Glass */}
        <div className="p-1.5 rounded-2xl liquid-glass-surface specular-edge border border-surface-border flex items-center gap-2 overflow-x-auto no-scrollbar flex-shrink-0 shadow-sm">
          <div className="flex items-center gap-1.5 pl-2.5 pr-1 text-content-secondary text-xs font-bold flex-shrink-0">
            <Filter className="w-3.5 h-3.5 text-content-primary" />
            <span>Category:</span>
          </div>

          {CATEGORY_FILTERS.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`min-h-[44px] px-4 text-xs font-bold rounded-xl transition-all whitespace-nowrap flex items-center justify-center ${
                selectedCategory === cat
                  ? 'liquid-glass-gold shadow-sm font-black text-md-black'
                  : 'text-content-secondary hover:text-content-primary hover:bg-neutral-black-06'
              }`}
            >
              {cat}
            </button>
          ))}

          <div className="h-6 w-px bg-surface-border mx-1 flex-shrink-0" />

          {STATUS_FILTERS.map((s) => (
            <button
              key={s}
              onClick={() => setSelectedStatus(s)}
              className={`min-h-[44px] px-3.5 text-xs font-semibold rounded-xl transition-all whitespace-nowrap flex items-center justify-center ${
                selectedStatus === s
                  ? 'btn-md-red text-white font-bold shadow-sm'
                  : 'text-content-muted hover:text-content-primary hover:bg-neutral-black-06'
              }`}
            >
              {s === 'ALL' ? 'All Status' : s.replace('_', ' ')}
            </button>
          ))}
        </div>

      {/* Error Banner */}
      {error && (
        <div className="flex items-center justify-between p-4 rounded-2xl bg-md-red-subtle border border-md-red/30 text-md-red text-sm">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0 text-md-red" />
            <span className="font-semibold">{error}</span>
          </div>
          <button 
            onClick={fetchIssues} 
            className="min-h-[44px] px-4 text-xs font-bold btn-md-red text-white rounded-xl"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Screen Reader Announcement */}
      <div className="sr-only" aria-live="polite">
        {`Displaying ${filteredIssues.length} infrastructure incidents.`}
      </div>

      {/* ========================================================================= */}
      {/* VIEW MODE 1: ACCESSIBLE LIST VIEW (FULL ALTERNATIVE TO MAP)               */}
      {/* ========================================================================= */}
      {viewMode === 'list' ? (
        <section className="flex-1 min-h-0 surface-card-solid p-4 sm:p-5 rounded-2xl border border-surface-border flex flex-col overflow-hidden space-y-3.5" aria-label="Accessible Incident Directory">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 border-b border-surface-border pb-3 flex-shrink-0">
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 text-content-muted absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter by title, category, or street address..."
                className="w-full pl-9 pr-3 py-2 rounded-xl bg-surface-card-subtle border border-surface-border text-xs font-semibold text-content-primary focus:outline-none focus:ring-2 focus:ring-md-black"
                aria-label="Filter incidents"
              />
            </div>

            <div className="flex items-center gap-2">
              <ArrowUpDown className="w-3.5 h-3.5 text-content-muted" />
              <label htmlFor="sort-select" className="text-xs font-bold text-content-secondary">Sort by:</label>
              <select
                id="sort-select"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="bg-surface-card-subtle border border-surface-border rounded-xl text-xs font-bold text-content-primary px-3 py-2 focus:outline-none"
              >
                <option value="priority">Urgency Score (High to Low)</option>
                <option value="reports">Report Count</option>
                <option value="date">Most Recent</option>
              </select>
            </div>
          </div>

          {filteredIssues.length === 0 ? (
            <EmptyState
              title="No incidents matching search criteria"
              description="Try adjusting your keywords, selecting 'All Categories', or clearing status filters."
              actionLabel="Reset Search Filters"
              onAction={() => { setSearchQuery(''); setSelectedCategory('ALL'); setSelectedStatus('ALL'); }}
            />
          ) : (
            <div className="flex-1 min-h-0 overflow-auto pr-1">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-surface-border text-content-muted uppercase tracking-wider font-bold">
                    <th className="py-3 px-3">Hazard Title & Location</th>
                    <th className="py-3 px-3">Category</th>
                    <th className="py-3 px-3">Lifecycle Status</th>
                    <th className="py-3 px-3 text-center">Urgency</th>
                    <th className="py-3 px-3 text-center">Citizen Reports</th>
                    <th className="py-3 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-border">
                  {filteredIssues.map((issue) => (
                    <tr 
                      key={issue.id} 
                      className="hover:bg-neutral-black-06 transition-colors group focus-within:bg-neutral-black-06"
                    >
                      <td className="py-3.5 px-3">
                        <div className="font-bold text-sm text-content-primary">{issue.title}</div>
                        <div className="text-content-secondary text-[11px] flex items-center gap-1 mt-0.5">
                          <MapPin className="w-3 h-3 text-md-red" />
                          <span>{issue.location?.address}</span>
                        </div>
                      </td>
                      <td className="py-3.5 px-3">
                        <span className="px-2.5 py-1 rounded-full bg-neutral-black-06 text-content-primary font-bold text-[11px]">
                          {issue.category}
                        </span>
                      </td>
                      <td className="py-3.5 px-3">
                        <StatusBadge status={issue.status} size="sm" />
                      </td>
                      <td className="py-3.5 px-3 text-center font-black text-sm text-content-primary">
                        {Math.round(issue.priority_score || 50)}
                      </td>
                      <td className="py-3.5 px-3 text-center font-bold text-content-secondary">
                        👥 {issue.report_count || 1}
                      </td>
                      <td className="py-3.5 px-3 text-right">
                        <button
                          onClick={() => handleLocateOnMap(issue)}
                          className="min-h-[40px] px-3.5 py-1.5 rounded-xl btn-md-gold text-md-black font-bold text-xs shadow-sm hover:scale-105 active:scale-95 transition-all inline-flex items-center gap-1"
                          aria-label={`View ${issue.title} on map`}
                        >
                          <MapIcon className="w-3.5 h-3.5 text-md-black" />
                          <span>View on Map</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      ) : (
        /* ========================================================================= */
        /* VIEW MODE 2: MAP VIEW (DESKTOP 2/3 + 1/3, MOBILE FULL MAP + BOTTOM SHEET) */
        /* ========================================================================= */
        <div className="flex-1 min-h-0 relative">
          
          {/* Main Desktop Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 h-full">
            
            {/* Google Map Panel: Full-height on mobile, 2 cols on desktop */}
            <div className="lg:col-span-2 h-full rounded-3xl overflow-hidden relative shadow-card border border-surface-border">
              <GoogleMapView
                issues={mappableIssues}
                selectedIssue={selectedIssue}
                onBoundsChange={setViewportBounds}
                onSelectIssue={(issue) => {
                  setSelectedIssue(issue);
                  // On mobile, snap to peek so user sees the pin
                  if (typeof window !== 'undefined' && window.innerWidth < 1024) {
                    setSheetState('peek');
                  }
                }}
                initialCenter={initialCenter}
                className="w-full h-full"
              />
            </div>

            {/* Desktop Persistent Sidebar (1 col) - The solitary scrolling feed container */}
            <div className="hidden lg:flex surface-card-solid p-5 flex-col h-full rounded-3xl border border-surface-border shadow-card min-h-0">
              <div className="flex items-center justify-between border-b border-surface-border pb-3 mb-3 flex-shrink-0">
                <span className="text-xs font-black text-content-primary uppercase tracking-wider">
                  {loading ? 'Scanning Cluster...' : `${mappableIssues.length} Incidents Found`}
                </span>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-md-red-subtle text-[11px] font-bold text-md-red">
                  <span className="w-1.5 h-1.5 rounded-full bg-md-red animate-pulse" />
                  Live Feed
                </span>
              </div>

              {/* Incidents feed container - SCROLLS INTERNALLY */}
              <div className="flex-1 min-h-0 overflow-y-auto space-y-3 pr-1.5">
                {loading ? (
                  Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="p-4 rounded-2xl bg-surface-card-subtle border border-surface-border animate-pulse space-y-2">
                      <div className="h-3.5 bg-neutral-black-12 rounded w-3/4" />
                      <div className="h-3 bg-neutral-black-06 rounded w-1/2" />
                    </div>
                  ))
                ) : mappableIssues.length === 0 ? (
                  <EmptyState
                    title="No mapped incidents"
                    description="No incidents match the active filter criteria."
                    actionLabel="Clear Filters"
                    onAction={() => { setSelectedCategory('ALL'); setSelectedStatus('ALL'); }}
                  />
                ) : (
                  mappableIssues.map((issue) => {
                    const isSelected = selectedIssue?.id === issue.id;

                    return (
                      <button
                        key={issue.id}
                        onClick={() => setSelectedIssue(isSelected ? null : issue)}
                        className={`w-full text-left p-4 rounded-2xl border transition-all space-y-2 ${
                          isSelected
                            ? 'border-md-gold bg-md-gold-subtle shadow-md'
                            : 'border-surface-border hover:border-surface-border-strong bg-surface-card hover:bg-surface-card-subtle'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-neutral-black-06 text-content-secondary">
                            {issue.id}
                          </span>
                          <StatusBadge status={issue.status} size="sm" />
                        </div>

                        <h3 className="font-bold text-content-primary text-sm leading-snug">
                          {issue.title}
                        </h3>

                        {issue.location && (
                          <div className="text-xs text-content-secondary truncate flex items-center gap-1">
                            <MapPin className="w-3.5 h-3.5 text-md-red flex-shrink-0" />
                            <span className="truncate">{issue.location.address}</span>
                          </div>
                        )}

                        <div className="flex items-center justify-between text-xs pt-2 border-t border-surface-border">
                          <span className="text-content-muted font-semibold">
                            👥 {issue.report_count ?? 1} Citizen Report
                          </span>
                          <span className="font-bold text-content-primary">
                            Score: {Math.round(issue.priority_score || 50)}
                          </span>
                        </div>
                      </button>
                    );
                  })
                )}
              </div>
            </div>

          </div>

          {/* ========================================================================= */}
          {/* MOBILE DRAGGABLE BOTTOM SHEET (PEEK / HALF / FULL)                        */}
          {/* Replaces the cramped 2/3 + 1/3 mobile split with full-height map overlay   */}
          {/* ========================================================================= */}
          <div 
            className={`lg:hidden absolute bottom-0 left-0 right-0 z-30 transition-all duration-300 ease-out surface-card-solid border-t border-surface-border rounded-t-3xl shadow-floating flex flex-col ${
              sheetState === 'peek' 
                ? 'h-20' 
                : sheetState === 'half' 
                ? 'h-[46vh]' 
                : 'h-[82vh]'
            }`}
          >
            {/* Sheet Drag Handle Header */}
            <div 
              onClick={() => {
                if (sheetState === 'peek') setSheetState('half');
                else if (sheetState === 'half') setSheetState('full');
                else setSheetState('peek');
              }}
              className="p-2 cursor-pointer flex-shrink-0 flex flex-col items-center select-none"
              role="button"
              tabIndex={0}
              aria-label={`Incident bottom sheet currently in ${sheetState} mode. Tap to cycle.`}
            >
              <div className="w-12 h-1.5 rounded-full bg-neutral-black-12 mb-1.5" />
              <div className="w-full px-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-md-red" />
                  <span className="text-xs font-black text-content-primary">
                    {mappableIssues.length} Incidents Near You
                  </span>
                </div>
                <div className="flex items-center gap-1 text-content-secondary text-xs font-bold">
                  <span>{sheetState === 'peek' ? 'Expand' : sheetState === 'half' ? 'Full' : 'Close'}</span>
                  {sheetState === 'peek' ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : sheetState === 'half' ? (
                    <Maximize2 className="w-3.5 h-3.5" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                </div>
              </div>
            </div>

            {/* If in Peek Mode: Show Selected Issue Preview */}
            {sheetState === 'peek' && selectedIssue && (
              <div className="px-4 pb-2 truncate">
                <div className="text-xs font-bold text-content-primary truncate">
                  Target: {selectedIssue.title}
                </div>
              </div>
            )}

            {/* Scrollable Incident Feed within Bottom Sheet */}
            {sheetState !== 'peek' && (
              <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2.5 mt-1">
                {mappableIssues.map((issue) => {
                  const isSelected = selectedIssue?.id === issue.id;
                  return (
                    <button
                      key={issue.id}
                      onClick={() => {
                        setSelectedIssue(isSelected ? null : issue);
                        setSheetState('peek'); // Snap to peek so user sees pin centered on map
                      }}
                      className={`w-full text-left p-3.5 rounded-2xl border transition-all space-y-1.5 ${
                        isSelected
                          ? 'border-md-gold bg-md-gold-subtle shadow-sm'
                          : 'border-surface-border bg-surface-card'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-neutral-black-06 text-content-secondary">
                          {issue.id}
                        </span>
                        <StatusBadge status={issue.status} size="sm" />
                      </div>
                      <h4 className="font-bold text-xs text-content-primary line-clamp-1">{issue.title}</h4>
                      <p className="text-[11px] text-content-secondary truncate">{issue.location?.address}</p>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

        </div>
      )}

      </div>
    </div>
  );
}

export default function PublicMapPage() {
  return (
    <Suspense fallback={<div className="p-8 text-content-muted font-bold">Loading public infrastructure map...</div>}>
      <MapPageContent />
    </Suspense>
  );
}
