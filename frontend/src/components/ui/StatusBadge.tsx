'use client';

import React from 'react';
import { Circle, CircleDot, CheckCircle2, AlertTriangle } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export type CivicStatus = 'SUBMITTED' | 'UNDER_REVIEW' | 'IN_PROGRESS' | 'ASSIGNED' | 'VERIFICATION' | 'RESOLVED' | 'CRITICAL';

interface StatusBadgeProps {
  status: CivicStatus | string;
  size?: 'sm' | 'md';
  className?: string;
}

export default function StatusBadge({ status, size = 'md', className }: StatusBadgeProps) {
  const norm = (status || '').toUpperCase().replace(/\s+/g, '_');

  // Unified Status System: Every status has a unique Shape + Icon + Label + Contrast pairing
  if (norm === 'CRITICAL' || norm === 'HIGH') {
    return (
      <span
        className={twMerge(
          clsx(
            'inline-flex items-center gap-1.5 font-black uppercase tracking-wider rounded-full bg-md-red text-white shadow-xs',
            size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs',
            className
          )
        )}
      >
        <AlertTriangle className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
        <span>Critical</span>
      </span>
    );
  }

  if (norm === 'RESOLVED') {
    return (
      <span
        className={twMerge(
          clsx(
            'inline-flex items-center gap-1.5 font-bold uppercase tracking-wider rounded-full bg-md-black text-white shadow-xs',
            size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs',
            className
          )
        )}
      >
        <CheckCircle2 className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
        <span>Resolved</span>
      </span>
    );
  }

  if (norm === 'IN_PROGRESS' || norm === 'ASSIGNED' || norm === 'VERIFICATION') {
    return (
      <span
        className={twMerge(
          clsx(
            'inline-flex items-center gap-1.5 font-bold uppercase tracking-wider rounded-full bg-md-gold text-md-black shadow-xs',
            size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs',
            className
          )
        )}
      >
        <CircleDot className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
        <span>In Progress</span>
      </span>
    );
  }

  // Default: Submitted / Open (Outlined ring, neutral background)
  return (
    <span
      className={twMerge(
        clsx(
          'inline-flex items-center gap-1.5 font-bold uppercase tracking-wider rounded-full bg-neutral-black-06 text-content-primary border border-surface-border',
          size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs',
          className
        )
      )}
    >
      <Circle className={size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
      <span>Submitted</span>
    </span>
  );
}

