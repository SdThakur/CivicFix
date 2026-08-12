'use client';

import React, { useEffect, useMemo, useState, useCallback, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Crosshair, Loader2, Navigation, MapPin } from 'lucide-react';
import type { Issue } from '@/types';

// Fix Leaflet's default icon loading bug in Next.js/Webpack
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: '',
  iconUrl: '',
  shadowUrl: '',
});

// Safe flyTo helper that avoids _leaflet_pos undefined errors on initial render
function safeFlyTo(map: L.Map, lat: number, lng: number, zoom: number = 16, duration: number = 1.2) {
  if (!map) return;
  try {
    map.whenReady(() => {
      try {
        const container = map.getContainer();
        if (container && (map as any)._mapPane) {
          map.flyTo([lat, lng], zoom, { animate: true, duration });
        } else {
          map.setView([lat, lng], zoom);
        }
      } catch {
        try {
          map.setView([lat, lng], zoom);
        } catch {}
      }
    });
  } catch {
    try {
      map.setView([lat, lng], zoom);
    } catch {}
  }
}

// Safe fitBounds helper
function safeFitBounds(map: L.Map, bounds: L.LatLngBounds) {
  if (!map) return;
  try {
    map.whenReady(() => {
      try {
        map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
      } catch {}
    });
  } catch {}
}

// Custom pin for issue markers
function createCustomPin(severity: string, isSelected: boolean) {
  let color = '#3b82f6'; // blue
  let glow = 'rgba(59, 130, 246, 0.4)';

  if (severity === 'CRITICAL') {
    color = '#f43f5e'; // rose-500
    glow = 'rgba(244, 63, 94, 0.5)';
  } else if (severity === 'HIGH') {
    color = '#f97316'; // orange-500
    glow = 'rgba(249, 115, 22, 0.4)';
  } else if (severity === 'MEDIUM') {
    color = '#eab308'; // yellow-500
    glow = 'rgba(234, 179, 8, 0.4)';
  } else if (severity === 'LOW') {
    color = '#10b981'; // emerald-500
    glow = 'rgba(16, 185, 129, 0.4)';
  }

  const size = isSelected ? 36 : 28;
  const pulse = severity === 'CRITICAL' || isSelected;

  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: `
      <div style="position: relative; width: ${size}px; height: ${size}px; display: flex; align-items: center; justify-content: center;">
        ${pulse ? `<div style="position: absolute; inset: -4px; border-radius: 9999px; background: ${glow}; animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>` : ''}
        <div style="
          width: ${size}px;
          height: ${size}px;
          background: ${color};
          border-radius: 50% 50% 50% 0;
          transform: rotate(-45deg);
          box-shadow: 0 4px 12px ${glow}, 0 0 0 2px #0f172a;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: transform 0.2s ease;
        ">
          <div style="
            width: ${size * 0.4}px;
            height: ${size * 0.4}px;
            background: #ffffff;
            border-radius: 50%;
            transform: rotate(45deg);
          "></div>
        </div>
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size],
    popupAnchor: [0, -size],
  });
}

// Custom pulsing blue beacon for user's precise GPS location
const userLocationIcon = L.divIcon({
  className: 'user-location-marker',
  html: `
    <div style="position: relative; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;">
      <div style="position: absolute; inset: -10px; border-radius: 9999px; background: rgba(14, 165, 233, 0.35); animation: ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
      <div style="position: absolute; inset: -4px; border-radius: 9999px; background: rgba(56, 189, 248, 0.5); border: 2px solid #ffffff;"></div>
      <div style="width: 14px; height: 14px; background: #0284c7; border-radius: 9999px; box-shadow: 0 0 14px #38bdf8; z-index: 10;"></div>
    </div>
  `,
  iconSize: [28, 28],
  iconAnchor: [14, 14],
  popupAnchor: [0, -16],
});

// Map controller handling auto-geolocation on initial load and issue pan/zoom
function MapController({
  selectedIssue,
  issues,
  initialCenter,
  userPos,
  setUserPos,
  setLocating,
  setLocError,
}: {
  selectedIssue: Issue | null;
  issues: Issue[];
  initialCenter?: { lat: number; lng: number } | null;
  userPos: { lat: number; lng: number; accuracy: number } | null;
  setUserPos: (pos: { lat: number; lng: number; accuracy: number } | null) => void;
  setLocating: (val: boolean) => void;
  setLocError: (err: string | null) => void;
}) {
  const map = useMap();
  const hasAutoLocated = useRef(false);

  // Initial center flyTo if target location is provided
  useEffect(() => {
    if (initialCenter?.lat && initialCenter?.lng) {
      safeFlyTo(map, initialCenter.lat, initialCenter.lng, 16, 1.2);
    }
  }, [map, initialCenter]);

  // Auto-locate user GPS without overriding initial target location
  useEffect(() => {
    if (!hasAutoLocated.current && typeof navigator !== 'undefined' && navigator.geolocation) {
      hasAutoLocated.current = true;
      setLocating(true);

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude, accuracy } = position.coords;
          setUserPos({ lat: latitude, lng: longitude, accuracy });
          setLocating(false);

          // Only fly to user location if no specific target location/initialCenter was provided
          if (!initialCenter && !selectedIssue) {
            safeFlyTo(map, latitude, longitude, 16, 1.5);
          }
        },
        (error) => {
          setLocating(false);
          if (!initialCenter && issues.length > 0) {
            const validPoints = issues
              .filter((i) => i.location?.latitude && i.location?.longitude)
              .map((i) => [i.location!.latitude, i.location!.longitude] as [number, number]);

            if (validPoints.length > 0) {
              const bounds = L.latLngBounds(validPoints);
              safeFitBounds(map, bounds);
            }
          }
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0,
        }
      );
    }
  }, [map, setUserPos, setLocating, issues, initialCenter, selectedIssue]);

  // Handle clicking an issue from the list
  useEffect(() => {
    if (selectedIssue?.location?.latitude && selectedIssue?.location?.longitude) {
      safeFlyTo(
        map,
        selectedIssue.location.latitude,
        selectedIssue.location.longitude,
        16,
        1.2
      );
    }
  }, [selectedIssue, map]);

  return null;
}

// Precise GPS Geolocation button controller
function GeolocationButton({
  setUserPos,
  locating,
  setLocating,
  setLocError,
}: {
  setUserPos: (pos: { lat: number; lng: number; accuracy: number } | null) => void;
  locating: boolean;
  setLocating: (val: boolean) => void;
  setLocError?: (err: string | null) => void;
}) {
  const map = useMap();

  const handleLocateMe = useCallback(() => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      alert('Geolocation is not supported by your browser.');
      return;
    }

    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude, accuracy } = position.coords;
        setUserPos({ lat: latitude, lng: longitude, accuracy });
        setLocating(false);
        safeFlyTo(map, latitude, longitude, 17, 1.2);
      },
      (error) => {
        setLocating(false);
        alert('Could not acquire your GPS position. Please check location permissions.');
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  }, [map, setUserPos, setLocating]);

  return (
    <div className="leaflet-top leaflet-right" style={{ pointerEvents: 'auto', marginTop: '12px', marginRight: '12px' }}>
      <button
        onClick={handleLocateMe}
        disabled={locating}
        title="Re-center to precise GPS location"
        className="flex items-center gap-2 px-3.5 py-2.5 rounded-xl bg-slate-900/90 hover:bg-slate-800 text-slate-100 border border-slate-700 shadow-2xl backdrop-blur-md transition-all hover:scale-105 active:scale-95 disabled:opacity-60 text-xs font-semibold group cursor-pointer"
      >
        {locating ? (
          <Loader2 className="w-4 h-4 text-sky-400 animate-spin" />
        ) : (
          <Crosshair className="w-4 h-4 text-sky-400 group-hover:rotate-45 transition-transform" />
        )}
        <span>
          {locating ? 'Acquiring GPS...' : 'Precise Location'}
        </span>
      </button>
    </div>
  );
}

interface IssueMapInnerProps {
  issues: Issue[];
  selectedIssue: Issue | null;
  onSelectIssue: (issue: Issue | null) => void;
  initialCenter?: { lat: number; lng: number } | null;
}

export default function IssueMapInner({
  issues,
  selectedIssue,
  onSelectIssue,
  initialCenter,
}: IssueMapInnerProps) {
  // Neutral center fallback while auto-locating
  const fallbackCenter: [number, number] = initialCenter?.lat && initialCenter?.lng
    ? [initialCenter.lat, initialCenter.lng]
    : [37.7749, -122.4194];

  // User GPS position state
  const [userPos, setUserPos] = useState<{ lat: number; lng: number; accuracy: number } | null>(null);
  const [locating, setLocating] = useState(false);
  const [locError, setLocError] = useState<string | null>(null);

  // Memoize markers
  const markers = useMemo(() => {
    return issues
      .filter((i) => i.location?.latitude && i.location?.longitude)
      .map((issue) => {
        const lat = issue.location!.latitude;
        const lng = issue.location!.longitude;
        const isSelected = selectedIssue?.id === issue.id;
        const customIcon = createCustomPin(issue.severity || 'MEDIUM', isSelected);

        return (
          <Marker
            key={issue.id}
            position={[lat, lng]}
            icon={customIcon}
            eventHandlers={{
              click: () => onSelectIssue(issue),
            }}
          >
            <Popup className="custom-popup" closeButton={false}>
              <div className="p-3 bg-slate-900 text-slate-100 rounded-xl border border-slate-800 shadow-2xl min-w-[220px] max-w-[280px]">
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800">
                    {issue.id}
                  </span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      issue.severity === 'CRITICAL'
                        ? 'bg-rose-500/20 text-rose-400'
                        : issue.severity === 'HIGH'
                        ? 'bg-amber-500/20 text-amber-400'
                        : 'bg-blue-500/20 text-blue-400'
                    }`}
                  >
                    {issue.severity}
                  </span>
                </div>

                <h4 className="font-bold text-white text-sm leading-tight mb-1">{issue.title}</h4>

                {issue.location?.address && (
                  <p className="text-[11px] text-slate-400 mb-2 truncate">
                    📍 {issue.location.address}
                  </p>
                )}

                <div className="flex items-center justify-between text-[10px] pt-2 border-t border-slate-800 text-slate-400">
                  <span>👥 {issue.report_count ?? 1} Citizen Reports</span>
                  <span className="font-semibold text-blue-400">
                    {issue.status?.replace('_', ' ')}
                  </span>
                </div>
              </div>
            </Popup>
          </Marker>
        );
      });
  }, [issues, selectedIssue, onSelectIssue]);

  return (
    <div className="w-full h-full relative">
      {/* Geolocation error notification */}
      {locError && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] px-4 py-2 rounded-xl bg-rose-500/90 text-white text-xs font-medium shadow-xl border border-rose-400 flex items-center gap-2">
          <span>{locError}</span>
          <button onClick={() => setLocError(null)} className="ml-1 underline font-bold">Dismiss</button>
        </div>
      )}

      <MapContainer
        center={fallbackCenter}
        zoom={14}
        scrollWheelZoom={true}
        className="w-full h-full z-0"
        style={{ background: '#0b0f19' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          maxZoom={19}
        />
        
        {/* Handles auto-locating on initial mount */}
        <MapController
          selectedIssue={selectedIssue}
          issues={issues}
          userPos={userPos}
          setUserPos={setUserPos}
          setLocating={setLocating}
          setLocError={setLocError}
        />

        {/* Floating Precise Location Button */}
        <GeolocationButton
          setUserPos={setUserPos}
          locating={locating}
          setLocating={setLocating}
          setLocError={setLocError}
        />

        {/* Precise User GPS Marker with Accuracy Ring */}
        {userPos && (
          <>
            <Circle
              center={[userPos.lat, userPos.lng]}
              radius={Math.max(userPos.accuracy, 15)}
              pathOptions={{
                color: '#38bdf8',
                fillColor: '#38bdf8',
                fillOpacity: 0.15,
                weight: 1.5,
              }}
            />
            <Marker position={[userPos.lat, userPos.lng]} icon={userLocationIcon}>
              <Popup className="custom-popup" closeButton={false}>
                <div className="p-3 bg-slate-900 text-slate-100 rounded-xl border border-sky-500/40 shadow-2xl min-w-[180px]">
                  <div className="flex items-center gap-2 mb-1">
                    <Navigation className="w-4 h-4 text-sky-400" />
                    <span className="text-xs font-bold text-white">Your Precise Location</span>
                  </div>
                  <p className="text-[10px] text-slate-400 font-mono">
                    {userPos.lat.toFixed(5)}, {userPos.lng.toFixed(5)}
                  </p>
                  <p className="text-[10px] text-sky-400 mt-1">
                    GPS Accuracy: ±{Math.round(userPos.accuracy)}m
                  </p>
                </div>
              </Popup>
            </Marker>
          </>
        )}

        {markers}
      </MapContainer>
    </div>
  );
}
