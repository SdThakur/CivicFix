'use client';

import React, { useEffect, useState } from 'react';

interface GradientBackdropProps {
  showWatermark?: boolean;
}

export default function GradientBackdrop({ showWatermark = true }: GradientBackdropProps) {
  const [isPaused, setIsPaused] = useState(false);

  // Pause ambient background animation when the document is hidden to conserve GPU/battery
  useEffect(() => {
    const handleVisibilityChange = () => {
      setIsPaused(document.hidden);
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  const animationStyle = isPaused ? { animationPlayState: 'paused' } : undefined;

  return (
    <div className="md-mesh-backdrop" aria-hidden="true">
      {/* 1. Primary Coral-Red Radiant Top-Right Aura (Sunset warmth) */}
      <div 
        className="md-mesh-backdrop-red-top animate-mesh-drift" 
        style={{ animationDuration: '72s', ...animationStyle }} 
      />

      {/* 2. Luminous Golden-Amber Sunlight Blob (Top-Right Core) */}
      <div 
        className="md-mesh-backdrop-gold-top animate-mesh-drift" 
        style={{ animationDuration: '84s', animationDirection: 'alternate-reverse', ...animationStyle }} 
      />

      {/* 3. Soft Ambient Bottom-Left Reflection (Muted balance) */}
      <div 
        className="md-mesh-backdrop-bottom animate-mesh-drift" 
        style={{ animationDuration: '92s', ...animationStyle }} 
      />

      {/* 4. Maryland Flag Calvert Heritage Quartered Motif (Left-flank watermark) */}
      {showWatermark && <div className="md-flag-watermark" />}
    </div>
  );
}
