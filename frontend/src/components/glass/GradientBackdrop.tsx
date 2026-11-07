'use client';

import React from 'react';

interface GradientBackdropProps {
  showWatermark?: boolean;
}

export default function GradientBackdrop({ showWatermark = true }: GradientBackdropProps) {
  return (
    <div className="md-mesh-backdrop" aria-hidden="true">
      {/* Drifting Gold Mesh Blob (Top-Right, 8-14% opacity) */}
      <div 
        className="md-mesh-backdrop-gold animate-mesh-drift" 
        style={{ animationDuration: '68s' }} 
      />

      {/* Drifting Red Mesh Blob (Bottom-Left, 8-12% opacity) */}
      <div 
        className="md-mesh-backdrop-red animate-mesh-drift" 
        style={{ animationDuration: '78s', animationDirection: 'alternate-reverse' }} 
      />

      {/* Subtle Maryland Flag Heritage Quartered Pattern (< 4% opacity) */}
      {showWatermark && <div className="md-flag-watermark" />}
    </div>
  );
}

