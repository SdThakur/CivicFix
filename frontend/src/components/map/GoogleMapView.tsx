'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Crosshair, Loader2, Navigation, Search, MapPin, ZoomIn } from 'lucide-react';
import { loadGoogleMaps, isGoogleMapsConfigured } from '@/lib/googleMaps';
import type { Issue } from '@/types';

declare const google: any;

interface GoogleMapViewProps {
  issues: Issue[];
  selectedIssue: Issue | null;
  onSelectIssue: (issue: Issue | null) => void;
  onBoundsChange?: (bounds: { minLat: number; maxLat: number; minLng: number; maxLng: number }) => void;
  initialCenter?: { lat: number; lng: number } | null;
  compact?: boolean;
  className?: string;
}

// Maryland Light Civic Map Styles (Clean, daylight readability, minimal POIs)
const LIGHT_MAP_STYLES: any[] = [
  { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#e8edf5' }] },
  { featureType: 'landscape', elementType: 'geometry', stylers: [{ color: '#f8fafc' }] },
  { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#ffffff' }] },
  { featureType: 'road.arterial', elementType: 'geometry', stylers: [{ color: '#ffffff' }, { weight: 1.5 }] },
  { featureType: 'road.highway', elementType: 'geometry', stylers: [{ color: '#fff3c4' }, { weight: 2 }] },
  { featureType: 'poi', stylers: [{ visibility: 'off' }] }, // minimal POI labels to avoid clutter
  { featureType: 'poi.park', elementType: 'geometry', stylers: [{ color: '#edf5ee' }, { visibility: 'simplified' }] },
  { featureType: 'transit', stylers: [{ visibility: 'simplified' }] },
  { featureType: 'administrative', elementType: 'labels.text.fill', stylers: [{ color: '#0b0b0c' }] },
  { featureType: 'administrative.neighborhood', stylers: [{ visibility: 'simplified' }] },
];

// Maryland Dark Civic Map Styles (Deep night contrast, minimal POIs)
const DARK_MAP_STYLES: any[] = [
  { elementType: 'geometry', stylers: [{ color: '#0b0b0c' }] },
  { elementType: 'labels.text.stroke', stylers: [{ color: '#0b0b0c' }] },
  { elementType: 'labels.text.fill', stylers: [{ color: '#e2e8f0' }] },
  { featureType: 'administrative.locality', elementType: 'labels.text.fill', stylers: [{ color: '#f8fafc' }] },
  { featureType: 'poi', stylers: [{ visibility: 'off' }] },
  { featureType: 'poi.park', elementType: 'geometry', stylers: [{ color: '#131a14' }, { visibility: 'simplified' }] },
  { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#1e1e24' }] },
  { featureType: 'road', elementType: 'geometry.stroke', stylers: [{ color: '#2b2b32' }] },
  { featureType: 'road.highway', elementType: 'geometry', stylers: [{ color: '#3d3014' }] },
  { featureType: 'road.highway', elementType: 'geometry.stroke', stylers: [{ color: '#ffc72c' }, { weight: 0.5 }] },
  { featureType: 'transit', elementType: 'geometry', stylers: [{ color: '#18181b' }] },
  { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#10141a' }] },
  { featureType: 'water', elementType: 'labels.text.fill', stylers: [{ color: '#94a3b8' }] },
];

export default function GoogleMapView({
  issues,
  selectedIssue,
  onSelectIssue,
  onBoundsChange,
  initialCenter,
  compact = false,
  className,
}: GoogleMapViewProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const mapRef = useRef<any>(null);
  const markersRef = useRef<Map<string | number, any>>(new Map());
  const clusterMarkersRef = useRef<any[]>([]);
  const circlesRef = useRef<any[]>([]);
  const infoWindowRef = useRef<any>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [locating, setLocating] = useState(false);
  const [zoomLevel, setZoomLevel] = useState<number>(compact ? 12 : 13);
  const [useFallback, setUseFallback] = useState(false);

  // Initialize Map
  useEffect(() => {
    let isMounted = true;

    if (!isGoogleMapsConfigured()) {
      setUseFallback(true);
      setLoading(false);
      return;
    }

    loadGoogleMaps()
      .then((googleInstance) => {
        if (!isMounted || !mapContainerRef.current) return;

        const isDarkMode = typeof window !== 'undefined' && (
          document.documentElement.classList.contains('dark') ||
          window.matchMedia('(prefers-color-scheme: dark)').matches
        );

        const defaultCenter = initialCenter || { lat: 39.0458, lng: -76.6413 }; // Maryland / Annapolis default
        const initZoom = compact ? 12 : 13;

        const map = new googleInstance.maps.Map(mapContainerRef.current, {
          center: defaultCenter,
          zoom: initZoom,
          styles: isDarkMode ? DARK_MAP_STYLES : LIGHT_MAP_STYLES,
          disableDefaultUI: compact,
          gestureHandling: 'greedy', // Captures scrollwheel/gestures on the map without scrolling the parent page
          zoomControl: !compact,
          zoomControlOptions: {
            position: googleInstance.maps.ControlPosition.RIGHT_BOTTOM,
          },
          streetViewControl: false,
          mapTypeControl: false,
          fullscreenControl: !compact,
          fullscreenControlOptions: {
            position: googleInstance.maps.ControlPosition.RIGHT_TOP,
          },
        });

        mapRef.current = map;
        infoWindowRef.current = new googleInstance.maps.InfoWindow();

        // Listen for zoom changes to drive marker clustering vs individual pins
        map.addListener('zoom_changed', () => {
          const currentZoom = map.getZoom();
          if (typeof currentZoom === 'number') {
            setZoomLevel(currentZoom);
          }
        });

        // Listen for viewport idle to trigger debounced bounded RPC fetching
        map.addListener('idle', () => {
          const b = map.getBounds();
          if (b && onBoundsChange) {
            const ne = b.getNorthEast();
            const sw = b.getSouthWest();
            onBoundsChange({
              minLat: sw.lat(),
              maxLat: ne.lat(),
              minLng: sw.lng(),
              maxLng: ne.lng(),
            });
          }
        });

        // Initialize Places Autocomplete if search input exists
        if (searchInputRef.current && googleInstance.maps.places) {
          const autocomplete = new googleInstance.maps.places.Autocomplete(searchInputRef.current, {
            fields: ['geometry', 'name', 'formatted_address'],
          });
          autocomplete.bindTo('bounds', map);
          autocomplete.addListener('place_changed', () => {
            const place = autocomplete.getPlace();
            if (!place.geometry || !place.geometry.location) return;

            map.panTo(place.geometry.location);
            map.setZoom(16);
          });
        }

        setLoading(false);
      })
      .catch(() => {
        setUseFallback(true);
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [initialCenter, compact]);

  // Recenter GPS
  const handleRecenter = useCallback(() => {
    if (!navigator.geolocation || !mapRef.current) return;
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const coords = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        mapRef.current?.panTo(coords);
        mapRef.current?.setZoom(16);
        setLocating(false);
      },
      () => setLocating(false),
      { enableHighAccuracy: true, timeout: 8000 }
    );
  }, []);

  // Render Markers and Clusters
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !(window as any).google?.maps) return;

    // Clear individual markers
    markersRef.current.forEach((marker) => marker.setMap(null));
    markersRef.current.clear();

    // Clear cluster markers
    clusterMarkersRef.current.forEach((marker) => marker.setMap(null));
    clusterMarkersRef.current = [];

    // Clear hotspot circles
    circlesRef.current.forEach((circle) => circle.setMap(null));
    circlesRef.current = [];

    const bounds = new (window as any).google.maps.LatLngBounds();
    let hasCoords = false;

    // Filter valid coordinate issues
    const validIssues = issues.filter(
      (i) => i.location?.latitude != null && i.location?.longitude != null
    );

    // Zoom-based Clustering Threshold:
    // If zoom < 14 and more than 6 issues, cluster close items
    const shouldCluster = zoomLevel < 14 && validIssues.length > 5;

    if (shouldCluster) {
      // Distance-based clustering algorithm
      const clusters: { center: { lat: number; lng: number }; items: Issue[] }[] = [];
      const clusterRadius = 0.007; // ~700 meters

      validIssues.forEach((issue) => {
        const lat = issue.location!.latitude;
        const lng = issue.location!.longitude;
        bounds.extend({ lat, lng });
        hasCoords = true;

        let added = false;
        for (const c of clusters) {
          const dLat = Math.abs(c.center.lat - lat);
          const dLng = Math.abs(c.center.lng - lng);
          if (dLat < clusterRadius && dLng < clusterRadius) {
            c.items.push(issue);
            // Re-average center
            c.center.lat = (c.center.lat * (c.items.length - 1) + lat) / c.items.length;
            c.center.lng = (c.center.lng * (c.items.length - 1) + lng) / c.items.length;
            added = true;
            break;
          }
        }

        if (!added) {
          clusters.push({ center: { lat, lng }, items: [issue] });
        }
      });

      clusters.forEach((cluster) => {
        if (cluster.items.length > 1) {
          // Render Cluster Badge Marker
          const count = cluster.items.length;
          const clusterMarker = new (window as any).google.maps.Marker({
            position: cluster.center,
            map: map,
            title: `Cluster: ${count} Incidents`,
            icon: {
              path: (window as any).google.maps.SymbolPath.CIRCLE,
              scale: Math.min(16 + count * 2, 28),
              fillColor: '#FFC72C', // Maryland Gold
              fillOpacity: 0.95,
              strokeColor: '#0B0B0C', // Maryland Black
              strokeWeight: 2.5,
            },
            label: {
              text: String(count),
              color: '#0B0B0C',
              fontSize: '12px',
              fontWeight: '800',
            },
            zIndex: 80,
          });

          clusterMarker.addListener('click', () => {
            map.setZoom(Math.min(map.getZoom() + 2, 16));
            map.panTo(cluster.center);
          });

          clusterMarkersRef.current.push(clusterMarker);

          // Hotspot density circle around cluster
          const clusterCircle = new (window as any).google.maps.Circle({
            strokeColor: '#FFC72C',
            strokeOpacity: 0.6,
            strokeWeight: 1.5,
            fillColor: '#FFC72C',
            fillOpacity: 0.12,
            map: map,
            center: cluster.center,
            radius: 80, // 80m cluster aura
          });
          circlesRef.current.push(clusterCircle);
        } else {
          // Single issue in cluster: render standard individual pin
          renderSingleIssuePin(cluster.items[0], map);
        }
      });

    } else {
      // Zoom >= 14 or small number of issues: Render all individual pins
      validIssues.forEach((issue) => {
        const lat = issue.location!.latitude;
        const lng = issue.location!.longitude;
        bounds.extend({ lat, lng });
        hasCoords = true;
        renderSingleIssuePin(issue, map);
      });
    }

    // Function to render standard geometric individual pin
    function renderSingleIssuePin(issue: Issue, targetMap: any) {
      const lat = issue.location!.latitude;
      const lng = issue.location!.longitude;
      const isSelected = selectedIssue?.id === issue.id;
      const pos = { lat, lng };

      const isResolved = issue.status === 'RESOLVED';
      const isUrgent = (issue.severity === 'CRITICAL' || issue.severity === 'HIGH') && !isResolved;
      const isMedium = (issue.severity === 'MEDIUM' || issue.status === 'IN_PROGRESS') && !isResolved;

      let svgPath = '';
      let fillColor = '#ffffff';
      let strokeColor = '#0b0b0c';
      let anchorPoint = new (window as any).google.maps.Point(12, 12);

      if (isResolved) {
        // Hexagonal Resolved Badge with Black fill (NEVER Red)
        svgPath = 'M 6 0 L 18 0 L 24 10 L 18 20 L 6 20 L 0 10 Z';
        fillColor = '#0b0b0c';
        strokeColor = '#ffffff';
      } else if (isUrgent) {
        // Rotated Diamond Shape for Urgent/Critical Hazards
        svgPath = 'M 12 0 L 24 12 L 12 24 L 0 12 Z';
        fillColor = '#E03A3E';
        strokeColor = '#0b0b0c';
      } else if (isMedium) {
        // Teardrop Shape for Medium / In Progress Hazards
        svgPath = 'M 12 0 C 7.03 0 3 4.03 3 9 C 3 15.25 12 24 12 24 C 12 24 21 15.25 21 9 C 21 4.03 16.97 0 12 0 Z';
        fillColor = '#FFC72C';
        strokeColor = '#0b0b0c';
        anchorPoint = new (window as any).google.maps.Point(12, 24);
      } else {
        // Outlined Circle for Low / Submitted
        svgPath = 'M 12 2 A 10 10 0 1 0 12 22 A 10 10 0 1 0 12 2 Z';
        fillColor = '#ffffff';
        strokeColor = '#0b0b0c';
      }

      const svgPin = {
        path: svgPath,
        fillColor: fillColor,
        fillOpacity: 1,
        strokeColor: strokeColor,
        strokeWeight: 1.5,
        scale: isSelected ? 1.5 : 1.15,
        anchor: anchorPoint,
      };

      const marker = new (window as any).google.maps.Marker({
        position: pos,
        map: targetMap,
        title: `${issue.title} (${isResolved ? 'Resolved' : isUrgent ? 'Critical' : 'Active'})`,
        icon: svgPin,
        zIndex: isSelected ? 100 : isUrgent ? 50 : 10,
        animation: isSelected ? (window as any).google.maps.Animation.BOUNCE : undefined,
      });

      marker.addListener('click', () => {
        onSelectIssue(issue);

        const statusBadgeHtml = isResolved
          ? '<span style="font-size: 10px; font-weight: 800; background: #0b0b0c; color: #ffffff; padding: 2px 8px; border-radius: 9999px;">✓ RESOLVED</span>'
          : isUrgent
          ? '<span style="font-size: 10px; font-weight: 800; background: #e03a3e; color: #ffffff; padding: 2px 8px; border-radius: 9999px;">▲ CRITICAL</span>'
          : '<span style="font-size: 10px; font-weight: 800; background: #ffc72c; color: #0b0b0c; padding: 2px 8px; border-radius: 9999px;">◑ IN PROGRESS</span>';

        const contentString = `
          <div style="font-family: 'Public Sans', sans-serif; padding: 8px; max-width: 260px; color: #0b0b0c;">
            <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 6px;">
              ${statusBadgeHtml}
              <span style="font-size: 11px; font-weight: 800; color: #0b0b0c;">
                Score: ${Math.round(issue.priority_score || 50)}/100
              </span>
            </div>
            <h4 style="font-size: 13px; font-weight: 800; margin: 0 0 4px 0; line-height: 1.3;">${issue.title}</h4>
            <p style="font-size: 11px; color: #475569; margin: 0 0 6px 0;">${issue.location?.address || 'Street Location'}</p>
            <div style="font-size: 10px; font-weight: 700; color: #e03a3e; text-transform: uppercase;">
              ${issue.category || 'General'}
            </div>
          </div>
        `;

        if (infoWindowRef.current) {
          infoWindowRef.current.setContent(contentString);
          infoWindowRef.current.open(targetMap, marker);
        }
      });

      markersRef.current.set(issue.id, marker);

      // Keep spatial hotspot circle for multi-report or urgent incidents
      if ((issue.report_count && issue.report_count > 1) || isUrgent) {
        const circle = new (window as any).google.maps.Circle({
          strokeColor: fillColor,
          strokeOpacity: 0.5,
          strokeWeight: 1,
          fillColor: fillColor,
          fillOpacity: 0.12,
          map: targetMap,
          center: pos,
          radius: 45, // 45 meters
        });
        circlesRef.current.push(circle);
      }
    }

    // Pan to selected issue or fit bounds
    if (selectedIssue?.location?.latitude && selectedIssue?.location?.longitude) {
      map.panTo({
        lat: selectedIssue.location.latitude,
        lng: selectedIssue.location.longitude,
      });
      map.setZoom(16);
    } else if (hasCoords && !initialCenter && !compact) {
      map.fitBounds(bounds, 50);
    }
  }, [issues, selectedIssue, onSelectIssue, initialCenter, compact, zoomLevel]);

  const rootClasses = className
    ? `relative overflow-hidden ${className}`
    : `relative w-full h-full min-h-[500px] rounded-3xl overflow-hidden border border-surface-border shadow-card bg-surface-canvas`;

  return (
    <div className={rootClasses}>
      
      {/* Floating Places Search Bar in Liquid Glass (Full Mode Only, non-animated blur) */}
      {!compact && (
        <div className="absolute top-4 left-4 z-20 max-w-sm w-full">
          <div className="liquid-glass-surface specular-edge shadow-floating rounded-2xl p-1.5 flex items-center gap-2 border border-surface-border">
            <Search className="w-4 h-4 text-content-muted ml-2.5 flex-shrink-0" />
            <input
              ref={searchInputRef}
              type="text"
              placeholder="Search address or neighborhood..."
              className="w-full bg-transparent text-xs font-semibold text-content-primary placeholder:text-content-muted focus:outline-none py-1.5 pr-2"
              aria-label="Search map location"
            />
          </div>
        </div>
      )}

      {/* Floating GPS Recenter Button (Non-animated blur) */}
      <div className={`absolute ${compact ? 'top-3 right-3' : 'top-4 right-14'} z-20`}>
        <button
          onClick={handleRecenter}
          disabled={locating}
          title="Recenter to my location"
          className="min-h-[40px] min-w-[40px] p-2 rounded-xl liquid-glass-surface specular-edge shadow-floating text-content-primary hover:bg-white/80 active:scale-95 transition-transform flex items-center justify-center border border-surface-border"
          aria-label="My Location"
        >
          {locating ? (
            <Loader2 className="w-4 h-4 text-md-red animate-spin" />
          ) : (
            <Crosshair className="w-4 h-4 text-content-primary" />
          )}
        </button>
      </div>

      {/* Interactive Fallback Geospatial Radar Layer (When Google Maps Key is offline or unverified) */}
      {useFallback ? (
        <div className="w-full h-full relative overflow-hidden bg-[#fbf9f3] dark:bg-[#141416] p-4 flex flex-col justify-between select-none">
          {/* Subtle Geospatial Coordinate Grid */}
          <div 
            className="absolute inset-0 opacity-20 pointer-events-none"
            style={{
              backgroundImage: 'linear-gradient(to right, #0b0b0c 1px, transparent 1px), linear-gradient(to bottom, #0b0b0c 1px, transparent 1px)',
              backgroundSize: '40px 40px',
            }}
          />

          {/* Radar Header Pill */}
          <div className="relative z-10 flex items-center justify-between pointer-events-none">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/90 dark:bg-black/80 backdrop-blur-md border border-black/[0.08] text-[11px] font-bold text-content-primary shadow-xs pointer-events-auto">
              <span className="w-2 h-2 rounded-full bg-[#10b981] animate-ping" />
              <span>Civic Radar Mode</span>
              <span className="text-content-muted tabular-nums">({issues.length} active)</span>
            </div>
          </div>

          {/* Interactive Incident Pins Canvas */}
          <div className="absolute inset-4 z-10">
            {issues.map((issue, idx) => {
              const lat = issue.location?.latitude || (38.97 + (idx * 0.015));
              const lng = issue.location?.longitude || (-76.55 + (idx * 0.02));
              
              // Normalize lat/lng to percentage bounds
              const minLat = 38.90, maxLat = 39.05, minLng = -76.65, maxLng = -76.40;
              const xPct = Math.max(10, Math.min(90, ((lng - minLng) / (maxLng - minLng)) * 100));
              const yPct = Math.max(10, Math.min(90, (1 - (lat - minLat) / (maxLat - minLat)) * 100));

              const isSelected = selectedIssue?.id === issue.id;
              const isUrgent = issue.severity === 'CRITICAL' || (issue.priority_score && issue.priority_score > 75);

              return (
                <button
                  key={issue.id}
                  type="button"
                  onClick={() => onSelectIssue(isSelected ? null : issue)}
                  style={{ left: `${xPct}%`, top: `${yPct}%` }}
                  title={`${issue.title} - ${issue.location?.address || 'Reported Hazard'}`}
                  className={`absolute -translate-x-1/2 -translate-y-1/2 group transition-all duration-300 focus:outline-none ${
                    isSelected ? 'scale-125 z-30' : 'hover:scale-110 z-20'
                  }`}
                  aria-label={`View ${issue.title}`}
                >
                  <div className={`p-2 rounded-full shadow-lg border transition-all ${
                    isSelected
                      ? 'bg-[#ffc72c] text-[#1b1c19] border-black ring-4 ring-[#ffc72c]/40'
                      : isUrgent
                      ? 'bg-[#b61825] text-white border-white/80'
                      : 'bg-white text-content-primary border-black/10'
                  }`}>
                    <MapPin className="w-4 h-4" />
                  </div>
                  {isSelected && (
                    <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 whitespace-nowrap bg-black/90 text-white text-[10px] font-bold px-2 py-0.5 rounded shadow pointer-events-none">
                      {issue.title}
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          {/* Radar Bottom Footer */}
          <div className="relative z-10 flex items-center justify-between text-[11px] text-content-muted font-mono pointer-events-none">
            <span>Annapolis Metropolitan Zone</span>
            <span>WGS84 38.9784° N, 76.4922° W</span>
          </div>
        </div>
      ) : (
        /* Google Maps Container */
        <div ref={mapContainerRef} className={`w-full h-full ${compact ? 'min-h-[300px]' : 'min-h-[500px]'}`} />
      )}

      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 z-30 flex items-center justify-center bg-white/70 backdrop-blur-sm">
          <div className="flex flex-col items-center gap-3 p-6 rounded-3xl liquid-glass-surface shadow-floating text-center">
            <Loader2 className="w-8 h-8 text-md-red animate-spin" />
            <span className="text-sm font-bold text-content-primary">Connecting Google Maps Engine...</span>
          </div>
        </div>
      )}

      {/* Error Overlay */}
      {error && (
        <div className="absolute inset-0 z-30 flex items-center justify-center bg-white/80 p-6">
          <div className="p-6 rounded-3xl surface-card-solid max-w-md text-center space-y-3">
            <MapPin className="w-8 h-8 text-md-red mx-auto" />
            <h4 className="font-bold text-sm text-content-primary">Map Engine Notice</h4>
            <p className="text-xs text-content-secondary">{error}</p>
          </div>
        </div>
      )}
    </div>
  );
}
