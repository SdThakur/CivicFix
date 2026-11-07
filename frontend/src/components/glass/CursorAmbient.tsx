'use client';

import React, { useEffect, useRef, useState } from 'react';

/**
 * CursorAmbient
 * Subtle, cursor-following ambient background layer.
 * 
 * Performance & Architecture:
 * - Fixed, pointer-events: none, aria-hidden="true" at z-index: -1.
 * - Zero React re-renders on mousemove: position stored in refs and written directly
 *   to compositor-only transform3d and opacity properties on a single DOM element.
 * - Smooth trailing via requestAnimationFrame lerp (~0.07 easing).
 * - RAF loop runs only while position/opacity are converging, then stops.
 * - Single 900px radial gradient box moving with translate3d (no blur filter, no backdrop-filter).
 * - Idle timer (~1.8s) settles to ~65% intensity; mouseleave fades to 0; tab hidden pauses loop.
 * - Static restrained gradient for coarse pointers (touch) and prefers-reduced-motion.
 */
export default function CursorAmbient() {
  const containerRef = useRef<HTMLDivElement>(null);
  const blobRef = useRef<HTMLDivElement>(null);
  const [isStatic, setIsStatic] = useState(false);

  // Position and opacity tracked strictly in refs — zero React state re-renders on pointer movement
  const posRef = useRef({
    targetX: 0,
    targetY: 0,
    currentX: 0,
    currentY: 0,
    targetOpacity: 0.65, // Idle initial intensity (~65%)
    currentOpacity: 0.65,
  });

  useEffect(() => {
    // Check for touch / coarse pointers or reduced motion preference
    const isCoarse = window.matchMedia('(pointer: coarse)').matches;
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (isCoarse || prefersReducedMotion) {
      setIsStatic(true);
      return;
    }

    const blob = blobRef.current;
    if (!blob) return;

    // Center coordinates
    const initialX = window.innerWidth * 0.5;
    const initialY = window.innerHeight * 0.35;

    const s = posRef.current;
    s.targetX = initialX;
    s.targetY = initialY;
    s.currentX = initialX;
    s.currentY = initialY;
    s.targetOpacity = 0.65;
    s.currentOpacity = 0.65;

    let isLooping = false;
    let rafId = 0;
    let idleTimer: ReturnType<typeof setTimeout> | null = null;

    // Apply initial position and CSS custom properties
    blob.style.setProperty('--cx', `${s.currentX.toFixed(1)}px`);
    blob.style.setProperty('--cy', `${s.currentY.toFixed(1)}px`);
    blob.style.setProperty('--co', s.currentOpacity.toFixed(3));
    blob.style.transform = `translate3d(${s.currentX - 450}px, ${s.currentY - 450}px, 0)`;
    blob.style.opacity = s.currentOpacity.toFixed(3);

    const tick = () => {
      const dx = s.targetX - s.currentX;
      const dy = s.targetY - s.currentY;
      const dOp = s.targetOpacity - s.currentOpacity;

      // Smooth trailing via lerp (~0.07 easing)
      s.currentX += dx * 0.07;
      s.currentY += dy * 0.07;
      s.currentOpacity += dOp * 0.07;

      if (blob) {
        blob.style.setProperty('--cx', `${s.currentX.toFixed(1)}px`);
        blob.style.setProperty('--cy', `${s.currentY.toFixed(1)}px`);
        blob.style.setProperty('--co', s.currentOpacity.toFixed(3));
        blob.style.transform = `translate3d(${s.currentX - 450}px, ${s.currentY - 450}px, 0)`;
        blob.style.opacity = s.currentOpacity.toFixed(3);
      }

      // Check convergence threshold: stop loop when position & opacity are settled
      if (Math.abs(dx) < 0.15 && Math.abs(dy) < 0.15 && Math.abs(dOp) < 0.005) {
        s.currentX = s.targetX;
        s.currentY = s.targetY;
        s.currentOpacity = s.targetOpacity;
        if (blob) {
          blob.style.setProperty('--cx', `${s.currentX.toFixed(1)}px`);
          blob.style.setProperty('--cy', `${s.currentY.toFixed(1)}px`);
          blob.style.setProperty('--co', s.currentOpacity.toFixed(3));
          blob.style.transform = `translate3d(${s.currentX - 450}px, ${s.currentY - 450}px, 0)`;
          blob.style.opacity = s.currentOpacity.toFixed(3);
        }
        isLooping = false;
        return; // Loop stops when converged
      }

      rafId = requestAnimationFrame(tick);
    };

    const startLoop = () => {
      if (!isLooping) {
        isLooping = true;
        rafId = requestAnimationFrame(tick);
      }
    };

    const stopLoop = () => {
      if (isLooping) {
        cancelAnimationFrame(rafId);
        isLooping = false;
      }
    };

    // Passive pointer movement handler
    const onPointerMove = (e: PointerEvent) => {
      s.targetX = e.clientX;
      s.targetY = e.clientY;
      s.targetOpacity = 1.0; // Full active intensity on pointer motion

      // Settle to ~65% intensity on idle (~1.8s of no movement)
      if (idleTimer) clearTimeout(idleTimer);
      idleTimer = setTimeout(() => {
        s.targetOpacity = 0.65;
        startLoop();
      }, 1800);

      startLoop();
    };

    // Fade to 0 when cursor leaves viewport
    const onMouseLeave = () => {
      if (idleTimer) clearTimeout(idleTimer);
      s.targetOpacity = 0.0;
      startLoop();
    };

    // Restore intensity when cursor returns
    const onMouseEnter = () => {
      s.targetOpacity = 0.65;
      startLoop();
    };

    // Pause RAF loop when tab is hidden to save CPU/GPU cycles
    const onVisibilityChange = () => {
      if (document.hidden) {
        stopLoop();
      } else {
        startLoop();
      }
    };

    window.addEventListener('pointermove', onPointerMove, { passive: true });
    document.documentElement.addEventListener('mouseleave', onMouseLeave);
    document.documentElement.addEventListener('mouseenter', onMouseEnter);
    document.addEventListener('visibilitychange', onVisibilityChange);

    return () => {
      stopLoop();
      if (idleTimer) clearTimeout(idleTimer);
      window.removeEventListener('pointermove', onPointerMove);
      document.documentElement.removeEventListener('mouseleave', onMouseLeave);
      document.documentElement.removeEventListener('mouseenter', onMouseEnter);
      document.removeEventListener('visibilitychange', onVisibilityChange);
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 pointer-events-none overflow-hidden select-none"
      style={{ zIndex: -1 }}
      aria-hidden="true"
    >
      {isStatic ? (
        /* Static restrained gradient for coarse pointers & prefers-reduced-motion (upper right) */
        <div
          className="absolute w-[800px] h-[800px] rounded-full opacity-60"
          style={{
            top: '-200px',
            right: '-150px',
            background:
              'radial-gradient(circle at 50% 50%, var(--cursor-ambient-gold, rgba(255, 199, 44, 0.09)) 0%, var(--cursor-ambient-red, rgba(224, 58, 62, 0.04)) 35%, rgba(255, 253, 247, 0) 70%)',
          }}
        />
      ) : (
        /* Dynamic single 900px box moved with transform3d (compositor only) */
        <div
          ref={blobRef}
          className="absolute top-0 left-0 w-[900px] h-[900px] rounded-full will-change-transform"
          style={{
            background:
              'radial-gradient(circle at 50% 50%, var(--cursor-ambient-gold, rgba(255, 199, 44, 0.10)) 0%, var(--cursor-ambient-red, rgba(224, 58, 62, 0.05)) 32%, rgba(255, 253, 247, 0) 70%)',
          }}
        />
      )}
    </div>
  );
}
