'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Camera, 
  Upload, 
  CheckCircle2, 
  AlertTriangle, 
  MapPin, 
  ArrowRight, 
  Sparkles, 
  Info, 
  Check, 
  RefreshCw,
  Loader2,
  AlertCircle,
  Crosshair,
  ShieldCheck,
  RotateCcw,
  EyeOff,
  Trash2,
  ThumbsUp,
  WifiOff
} from 'lucide-react';
import { useAuth } from '@/lib/supabase/auth';
import { getSupabaseBrowserClient } from '@/lib/supabase/client';
import { useNearbyIssues, useOptimisticUpvote } from '@/lib/supabase/queries';
import { extractExifGps, compressAndConvertToWebP } from '@/lib/imageProcessor';
import { 
  saveDraftToIndexedDb, 
  getLatestDraftFromIndexedDb, 
  clearDraftFromIndexedDb,
  enqueueOfflineUpload,
  getQueuedUploads,
  removeQueuedUpload
} from '@/lib/offlineQueue';

const CATEGORIES = [
  { id: 'Pothole & Road Damage', label: 'Pothole & Road', dept: 'DPW-HWY' },
  { id: 'Broken Streetlight', label: 'Streetlight', dept: 'ELECTRICAL' },
  { id: 'Overflowing Trash', label: 'Trash & Dumping', dept: 'SANITATION' },
  { id: 'Damaged Sidewalk', label: 'Sidewalk Ramp', dept: 'DPW-SIDEWALK' },
  { id: 'Fallen Tree / Hazard', label: 'Fallen Tree', dept: 'PARKS-FORESTRY' },
  { id: 'Graffiti & Vandalism', label: 'Graffiti', dept: 'URBAN-CARE' },
  { id: 'Water Main / Leak', label: 'Water Leak', dept: 'WATER-SEWER' },
  { id: 'Other Hazard', label: 'Other Hazard', dept: 'GENERAL-OPS' },
];

export default function ReportWizardPage() {
  const router = useRouter();
  const { user, signInAnonymously } = useAuth();
  const supabase = getSupabaseBrowserClient();

  // Screen 1: 'upload' (Instant camera/upload) | Screen 2: 'review' (Unified review & submit)
  const [screen, setScreen] = useState<'upload' | 'review'>('upload');

  // Photo & WebP Blob state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [processedWebpBlob, setProcessedWebpBlob] = useState<Blob | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // Location State
  const [location, setLocation] = useState<{
    lat: number;
    lng: number;
    address: string;
  }>({
    lat: 38.9784, // Maryland State Circle baseline
    lng: -76.4922,
    address: 'State Circle, Annapolis, MD',
  });

  // Privacy & Approximate Location Toggle
  const [isApproximate, setIsApproximate] = useState(false);

  // Form Fields
  const [category, setCategory] = useState<string>('Pothole & Road Damage');
  const [description, setDescription] = useState('');
  const [title, setTitle] = useState('');

  // Async Ingestion & Pipeline State
  const [submitting, setSubmitting] = useState(false);
  const [submittedReportId, setSubmittedReportId] = useState<string | null>(null);
  const [pipelineStatus, setPipelineStatus] = useState<'PENDING' | 'PROCESSING' | 'DONE' | 'FAILED' | null>(null);
  const [aiResultCategory, setAiResultCategory] = useState<string | null>(null);
  const [aiConfidence, setAiConfidence] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Draft persistence state
  const [hasSavedDraft, setHasSavedDraft] = useState(false);
  const [isOffline, setIsOffline] = useState(!navigator.onLine);

  // 100m Duplicate candidate detection via Supabase RPC
  const { data: nearbyCandidates, isLoading: candidatesLoading } = useNearbyIssues({
    lat: location.lat,
    lng: location.lng,
    radiusMeters: 100.0,
    enabled: screen === 'review' && !isNaN(location.lat),
  });

  const upvoteMutation = useOptimisticUpvote();

  // ─── 1. CHECK OFFLINE QUEUE & SAVED DRAFTS ON MOUNT ─────────────────────────
  useEffect(() => {
    const handleOnline = () => {
      setIsOffline(false);
      flushOfflineUploads();
    };
    const handleOffline = () => setIsOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Check for existing drafts in IndexedDB
    getLatestDraftFromIndexedDb().then((draft) => {
      if (draft && draft.photoBlob) {
        setHasSavedDraft(true);
      }
    });

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const flushOfflineUploads = async () => {
    const queue = await getQueuedUploads();
    if (!queue || queue.length === 0) return;

    for (const item of queue) {
      try {
        const fileId = `${Date.now()}_offline.webp`;
        const path = `reports/${item.userId}/${fileId}`;
        const { error: uploadError } = await supabase.storage.from('reports').upload(path, item.imageBlob, {
          contentType: 'image/webp',
          upsert: true,
        });
        if (!uploadError) {
          const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
          const session = (await supabase.auth.getSession()).data.session;
          await fetch(`${apiBase}/reports`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${session?.access_token || ''}`,
            },
            body: JSON.stringify({
              image_path: path,
              lat: item.lat,
              lng: item.lng,
              description: item.description,
            }),
          });
          await removeQueuedUpload(item.id);
        }
      } catch (err) {
        console.warn('Could not flush item:', err);
      }
    }
  };

  // ─── 2. RESTORE DRAFT FROM INDEXEDDB ─────────────────────────────────────────
  const handleRestoreDraft = async () => {
    const draft = await getLatestDraftFromIndexedDb();
    if (!draft) return;

    const url = URL.createObjectURL(draft.photoBlob);
    setProcessedWebpBlob(draft.photoBlob);
    setPreviewUrl(url);
    setLocation({
      lat: draft.lat,
      lng: draft.lng,
      address: draft.address,
    });
    setIsApproximate(draft.isApproximate);
    setCategory(draft.category || 'Pothole & Road Damage');
    setDescription(draft.description || '');
    setHasSavedDraft(false);
    setScreen('review');
  };

  const handleDiscardDraft = async () => {
    await clearDraftFromIndexedDb('current_draft');
    setHasSavedDraft(false);
  };

  // ─── 3. FILE SELECTION & EXIF GPS EXTRACTION ────────────────────────────────
  const handleFileChange = async (file: File) => {
    setSelectedFile(file);
    const localUrl = URL.createObjectURL(file);
    setPreviewUrl(localUrl);

    // 1. Read EXIF GPS BEFORE compression
    const gps = await extractExifGps(file);
    if (gps) {
      setLocation({
        lat: gps.latitude,
        lng: gps.longitude,
        address: `${gps.latitude.toFixed(4)}, ${gps.longitude.toFixed(4)} (EXIF GPS)`,
      });
    } else {
      // Prompt GPS fallback if no EXIF coordinates found
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            setLocation({
              lat: pos.coords.latitude,
              lng: pos.coords.longitude,
              address: `${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)} (Device GPS)`,
            });
          },
          () => {},
          { enableHighAccuracy: true, timeout: 5000 }
        );
      }
    }

    // 2. Compress & Convert to WebP (~1600px) in the background
    try {
      const webp = await compressAndConvertToWebP(file, 1600, 0.85);
      setProcessedWebpBlob(webp);

      // Save initial draft to IndexedDB
      await saveDraftToIndexedDb({
        id: 'current_draft',
        photoBlob: webp,
        lat: gps?.latitude || location.lat,
        lng: gps?.longitude || location.lng,
        address: location.address,
        isApproximate: false,
        category,
        description,
        updatedAt: new Date().toISOString(),
      });
    } catch (err) {
      console.warn('WebP conversion fallback', err);
    }

    setScreen('review');
  };

  // ─── 4. APPROXIMATE LOCATION TOGGLE ─────────────────────────────────────────
  const handleToggleApproximate = () => {
    setIsApproximate((prev) => {
      const next = !prev;
      if (next) {
        // Round to 3 decimal places (~100m) for privacy preservation
        setLocation((loc) => ({
          ...loc,
          lat: Number(loc.lat.toFixed(3)),
          lng: Number(loc.lng.toFixed(3)),
          address: `${loc.lat.toFixed(3)}, ${loc.lng.toFixed(3)} (Approx. ~100m Privacy)`,
        }));
      }
      return next;
    });
  };

  // ─── 5. UPVOTE EXISTING NEARBY DUPLICATE ────────────────────────────────────
  const handleUpvoteExisting = async (issueId: string) => {
    try {
      let currentUserId = user?.id;
      if (!currentUserId) {
        const { user: anonUser } = await signInAnonymously();
        currentUserId = anonUser?.id;
      }
      if (currentUserId) {
        await upvoteMutation.mutateAsync({ issueId, userId: currentUserId });
      }
      await clearDraftFromIndexedDb('current_draft');
      router.push('/dashboard?upvoted=true');
    } catch (err) {
      console.error(err);
      router.push('/dashboard?upvoted=true');
    }
  };

  // ─── 6. REALTIME SUBSCRIPTION FOR REPORT STATUS ─────────────────────────────
  const watchReportStatus = useCallback((reportId: string) => {
    // 1. Supabase Realtime channel watcher
    const channel = supabase
      .channel(`report-live-${reportId}`)
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'reports',
          filter: `id=eq.${reportId}`,
        },
        (payload: any) => {
          const row = payload.new;
          if (row) {
            setPipelineStatus(row.status);
            if (row.category) setAiResultCategory(row.category);
            if (row.ai_confidence) setAiConfidence(Math.round(row.ai_confidence * 100));
            if (row.status === 'DONE' || row.status === 'FAILED') {
              supabase.removeChannel(channel);
            }
          }
        }
      )
      .subscribe();

    // 2. Polling Fallback (every 2.5s) to guarantee resilience
    let pollAttempts = 0;
    const interval = setInterval(async () => {
      pollAttempts++;
      if (pollAttempts > 24) {
        clearInterval(interval);
        return;
      }
      try {
        const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
        const session = (await supabase.auth.getSession()).data.session;
        const res = await fetch(`${apiBase}/reports/${reportId}`, {
          headers: {
            Authorization: `Bearer ${session?.access_token || ''}`,
          },
        });
        if (res.ok) {
          const data = await res.json();
          setPipelineStatus(data.status);
          if (data.category) setAiResultCategory(data.category);
          if (data.ai_confidence) setAiConfidence(Math.round(data.ai_confidence * 100));
          if (data.status === 'DONE' || data.status === 'FAILED') {
            clearInterval(interval);
            supabase.removeChannel(channel);
          }
        }
      } catch {}
    }, 2500);

    return () => {
      clearInterval(interval);
      supabase.removeChannel(channel);
    };
  }, [supabase]);

  // ─── 7. SUBMIT REPORT (ASYNC 202 INGESTION) ──────────────────────────────────
  const handleSubmitReport = async () => {
    setSubmitting(true);
    setErrorMessage(null);

    try {
      // 1. Ensure user authentication (Anonymous guest if not signed in)
      let currentUserId = user?.id;
      let session = (await supabase.auth.getSession()).data.session;
      if (!currentUserId || !session) {
        const { user: anonUser } = await signInAnonymously();
        currentUserId = anonUser?.id;
        session = (await supabase.auth.getSession()).data.session;
      }

      if (!currentUserId || !session) {
        throw new Error('Authentication session could not be established.');
      }

      const blobToUpload = processedWebpBlob || selectedFile;
      if (!blobToUpload) {
        throw new Error('Please take or upload a photo first.');
      }

      // Check offline mode
      if (!navigator.onLine) {
        await enqueueOfflineUpload({
          id: `queue_${Date.now()}`,
          userId: currentUserId,
          imageBlob: blobToUpload,
          lat: location.lat,
          lng: location.lng,
          description: description || `Report on ${category}`,
          category,
          queuedAt: new Date().toISOString(),
        });
        setSubmitting(false);
        setPipelineStatus('PENDING');
        setErrorMessage('Device is offline. Report has been safely queued in IndexedDB and will transmit once reconnected.');
        return;
      }

      // 2. Upload WebP to Supabase Storage: reports/<user_id>/<uuid>.webp
      const reportUuid = crypto.randomUUID();
      const storagePath = `reports/${currentUserId}/${reportUuid}.webp`;

      const { error: storageError } = await supabase.storage
        .from('reports')
        .upload(storagePath, blobToUpload, {
          contentType: 'image/webp',
          upsert: true,
        });

      if (storageError) {
        throw new Error(`Storage upload failed: ${storageError.message}`);
      }

      // 3. POST /reports with { image_path, lat, lng, description } -> HTTP 202 Accepted
      const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const response = await fetch(`${apiBase}/reports`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          image_path: storagePath,
          lat: location.lat,
          lng: location.lng,
          description: description || `Reported on right-of-way. Category: ${category}`,
        }),
      });

      if (response.status !== 202 && !response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to submit report.');
      }

      const resData = await response.json();
      setSubmittedReportId(resData.id);
      setPipelineStatus('PENDING');

      // Clear draft from IndexedDB
      await clearDraftFromIndexedDb('current_draft');

      // 4. Watch report live status
      watchReportStatus(resData.id);

    } catch (err: any) {
      console.error(err);
      setErrorMessage(err.message || 'An error occurred during submission.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6 py-4 sm:py-8">
      
      {/* ========================================================================= */}
      {/* SCREEN 1: INSTANT CAMERA & UPLOAD SCREEN                                   */}
      {/* ========================================================================= */}
      {screen === 'upload' && (
        <div className="space-y-5">
          {/* Saved Draft Notification Banner */}
          {hasSavedDraft && (
            <div className="p-4 rounded-2xl liquid-glass-gold border border-md-gold/40 flex items-center justify-between gap-3 text-md-black shadow-sm">
              <div className="flex items-center gap-2.5">
                <RotateCcw className="w-5 h-5 flex-shrink-0 text-md-black" />
                <div>
                  <span className="font-bold text-xs block">Unsaved Draft Found</span>
                  <span className="text-[11px] opacity-80">
                    You have an in-progress hazard report from earlier in IndexedDB.
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleRestoreDraft}
                  className="px-3 py-1.5 rounded-xl bg-md-black text-white text-xs font-bold hover:bg-neutral-800 transition"
                >
                  Resume
                </button>
                <button
                  type="button"
                  onClick={handleDiscardDraft}
                  className="p-1.5 rounded-xl hover:bg-black/5 text-md-black/60 transition"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* Camera-First Hero Card */}
          <div className="p-8 sm:p-10 rounded-3xl liquid-glass border border-white/50 dark:border-white/10 shadow-glass text-center space-y-6">
            <div className="w-16 h-16 rounded-2xl bg-md-gold/20 flex items-center justify-center mx-auto text-md-black dark:text-md-gold border border-md-gold/30">
              <Camera className="w-8 h-8" />
            </div>

            <div className="space-y-2">
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-content-primary">
                Report Infrastructure
              </h1>
              <p className="text-sm text-content-secondary max-w-md mx-auto">
                Snap or upload a photo of road hazards, broken signals, or street defects. EXIF GPS and computer vision handle the rest.
              </p>
            </div>

            {/* Action Buttons */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-md mx-auto pt-2">
              <label className="flex items-center justify-center gap-3 px-6 py-4 rounded-2xl bg-md-red text-white font-bold text-sm shadow-md hover:bg-md-red-dark transition cursor-pointer">
                <Camera className="w-5 h-5" />
                <span>Snap Photo</span>
                <input
                  type="file"
                  accept="image/*"
                  capture="environment"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleFileChange(file);
                  }}
                />
              </label>

              <label className="flex items-center justify-center gap-3 px-6 py-4 rounded-2xl liquid-glass-frosted border border-content-secondary/20 font-bold text-sm text-content-primary hover:bg-white/40 dark:hover:bg-white/10 transition cursor-pointer">
                <Upload className="w-5 h-5 text-content-secondary" />
                <span>Upload File</span>
                <input
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleFileChange(file);
                  }}
                />
              </label>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* SCREEN 2: REVIEW & ASYNC PIPELINE SCREEN                                  */}
      {/* ========================================================================= */}
      {screen === 'review' && (
        <div className="space-y-6">
          
          {/* Top Bar Navigation */}
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={() => setScreen('upload')}
              className="text-xs font-bold text-content-secondary hover:text-content-primary flex items-center gap-1.5 transition"
            >
              ← Back to Photo Capture
            </button>
            {isOffline && (
              <span className="flex items-center gap-1.5 text-xs text-amber-600 dark:text-amber-400 font-semibold">
                <WifiOff className="w-3.5 h-3.5" /> Offline Mode (IndexedDB Queue)
              </span>
            )}
          </div>

          {/* Photo Preview & Location Panel */}
          <div className="p-6 rounded-3xl liquid-glass border border-white/50 dark:border-white/10 shadow-glass space-y-5">
            {previewUrl && (
              <div className="relative rounded-2xl overflow-hidden aspect-video bg-neutral-900 border border-black/10">
                <img src={previewUrl} alt="Report preview" className="w-full h-full object-cover" />
                <div className="absolute top-3 left-3 px-3 py-1.5 rounded-full liquid-glass-frosted border border-white/30 text-[11px] font-bold text-white flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-md-gold" /> WebP Preprocessed (~1600px)
                </div>
              </div>
            )}

            {/* Location & Approximate Privacy Toggle */}
            <div className="p-4 rounded-2xl bg-surface-overlay/40 border border-content-secondary/15 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-md-red" />
                  <span className="text-xs font-bold text-content-primary">Location Coordinates</span>
                </div>
                <button
                  type="button"
                  onClick={handleToggleApproximate}
                  className={`px-2.5 py-1 rounded-xl text-xs font-bold transition flex items-center gap-1.5 ${
                    isApproximate
                      ? 'bg-md-gold/20 text-md-black dark:text-md-gold border border-md-gold/40'
                      : 'bg-surface-canvas border border-content-secondary/20 text-content-secondary'
                  }`}
                >
                  <EyeOff className="w-3.5 h-3.5" />
                  {isApproximate ? 'Approximate (Active)' : 'Make Approximate'}
                </button>
              </div>

              <p className="text-xs font-mono text-content-secondary">
                {location.address}
              </p>

              <p className="text-[11px] text-content-tertiary">
                Privacy notice: Location is only used to dispatch city repair teams and detect right-of-way duplicates. Approximate mode bounds coordinates to ~100 meters.
              </p>
            </div>
          </div>

          {/* 100m Upvote Existing Candidate (Before AI Ingestion) */}
          {nearbyCandidates && nearbyCandidates.length > 0 && (
            <div className="p-5 rounded-2xl liquid-glass-gold border border-md-gold/40 shadow-sm space-y-3">
              <div className="flex items-center gap-2 text-md-black">
                <AlertTriangle className="w-4 h-4 text-md-red" />
                <span className="font-bold text-xs uppercase tracking-wider">Nearby Existing Issue Found</span>
              </div>
              <p className="text-xs text-md-black/80">
                A matching infrastructure report was detected within 100 meters. Upvote it to increase priority instead of creating a duplicate ticket!
              </p>
              <div className="p-3 rounded-xl bg-white/70 dark:bg-black/30 border border-md-gold/30 flex items-center justify-between gap-3">
                <div>
                  <span className="text-xs font-bold block text-content-primary">{nearbyCandidates[0].title}</span>
                  <span className="text-[11px] text-content-secondary">
                    {nearbyCandidates[0].distance_meters}m away · {nearbyCandidates[0].upvotes} citizen upvotes
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => handleUpvoteExisting(nearbyCandidates[0].id)}
                  disabled={upvoteMutation.isPending}
                  className="px-4 py-2 rounded-xl bg-md-black text-white text-xs font-bold hover:bg-neutral-800 transition flex items-center gap-1.5 shadow"
                >
                  <ThumbsUp className="w-3.5 h-3.5 text-md-gold" />
                  <span>Upvote Existing</span>
                </button>
              </div>
            </div>
          )}

          {/* Category & Description Form */}
          <div className="p-6 rounded-3xl liquid-glass border border-white/50 dark:border-white/10 shadow-glass space-y-4">
            <div>
              <label className="block text-xs font-bold text-content-primary mb-2">Category</label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {CATEGORIES.map((cat) => (
                  <button
                    key={cat.id}
                    type="button"
                    onClick={() => setCategory(cat.id)}
                    className={`p-2.5 rounded-xl text-left text-xs font-semibold transition border ${
                      category === cat.id
                        ? 'bg-md-gold/20 border-md-gold/60 text-md-black dark:text-md-gold shadow-sm'
                        : 'liquid-glass-frosted border-content-secondary/15 text-content-secondary hover:text-content-primary'
                    }`}
                  >
                    {cat.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-content-primary mb-1">Additional Notes (Optional)</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe landmark or specific location details..."
                className="w-full px-4 py-2.5 rounded-xl bg-surface-canvas/60 border border-content-secondary/20 text-xs text-content-primary focus:outline-none focus:ring-2 focus:ring-md-gold/40 resize-none h-20"
              />
            </div>

            {/* Error Message */}
            {errorMessage && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-600 dark:text-red-400 text-xs font-medium flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Live Async Pipeline Progress Card */}
            {pipelineStatus && (
              <div className="p-4 rounded-2xl liquid-glass-frosted border border-white/40 dark:border-white/10 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-content-primary flex items-center gap-2">
                    {pipelineStatus === 'PENDING' && <Loader2 className="w-4 h-4 animate-spin text-md-gold" />}
                    {pipelineStatus === 'PROCESSING' && <RefreshCw className="w-4 h-4 animate-spin text-md-gold" />}
                    {pipelineStatus === 'DONE' && <CheckCircle2 className="w-4 h-4 text-emerald-500" />}
                    {pipelineStatus === 'FAILED' && <AlertCircle className="w-4 h-4 text-red-500" />}
                    Pipeline Status: <span className="font-extrabold">{pipelineStatus}</span>
                  </span>
                  {aiConfidence && (
                    <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">
                      AI Confidence: {aiConfidence}%
                    </span>
                  )}
                </div>

                {pipelineStatus === 'PROCESSING' && (
                  <p className="text-xs text-content-secondary animate-pulse">
                    Gemini Vision is classifying the image and running 100m spatial deduplication...
                  </p>
                )}

                {pipelineStatus === 'DONE' && (
                  <div className="flex items-center justify-between pt-1">
                    <span className="text-xs font-medium text-content-secondary">
                      Triage complete: {aiResultCategory || category}
                    </span>
                    <button
                      type="button"
                      onClick={() => router.push('/dashboard')}
                      className="px-3 py-1.5 rounded-xl bg-md-black text-white text-xs font-bold hover:bg-neutral-800 transition shadow"
                    >
                      View on Dashboard →
                    </button>
                  </div>
                )}

                {pipelineStatus === 'FAILED' && (
                  <div className="flex items-center justify-between pt-1">
                    <span className="text-xs text-red-500 font-medium">
                      Analysis encountered an issue.
                    </span>
                    <button
                      type="button"
                      onClick={handleSubmitReport}
                      className="px-3 py-1.5 rounded-xl bg-red-600 text-white text-xs font-bold hover:bg-red-700 transition shadow"
                    >
                      Retry Submission
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Submit Action Button */}
            {!pipelineStatus && (
              <button
                type="button"
                onClick={handleSubmitReport}
                disabled={submitting}
                className="w-full py-3.5 rounded-2xl bg-md-red text-white font-bold text-sm shadow-md hover:bg-md-red-dark transition flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Transmitting to Supabase Pipeline...</span>
                  </>
                ) : (
                  <>
                    <span>Submit Infrastructure Report</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
