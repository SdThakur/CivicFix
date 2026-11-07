'use client';

import React from 'react';
import { Circle, CircleDot, CheckCircle2, AlertTriangle, Zap, ShieldAlert, Clock } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export type CivicStatus =
  | 'SUBMITTED'
  | 'UNDER_REVIEW'
  | 'IN_PROGRESS'
  | 'ASSIGNED'
  | 'VERIFICATION'
  | 'RESOLVED'
  | 'CLOSED'
  | 'CANCELLED';

export type CivicPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

interface StatusBadgeProps {
  status?: CivicStatus | string;
  priority?: CivicPriority | string;
  size?: 'sm' | 'md';
  className?: string;
}

export default function StatusBadge({ status, priority, size = 'md', className }: StatusBadgeProps) {
  // If priority is explicitly passed or status looks like priority:
  const isPriority = Boolean(priority) || ['LOW', 'MEDIUM', 'HIGH', 'URGENT', 'CRITICAL'].includes((status || '').toUpperCase());
  const token = (priority || status || 'SUBMITTED').toUpperCase().replace(/\s+/g, '_');

  const basePadding = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs';
  const iconSize = size === 'sm' ? 'w-3 h-3' : 'w-3.5 h-3.5';

  if (isPriority) {
    if (token === 'URGENT' || token === 'CRITICAL') {
      return (
        <span
          className={twMerge(
            clsx(
              'inline-flex items-center gap-1.5 font-extrabold uppercase tracking-wider rounded-md bg-md-red text-white shadow-xs',
              basePadding,
              className
            )
          )}
        >
          <ShieldAlert className={iconSize} />
          <span>Urgent</span>
        </span>
      );
    }

    if (token === 'HIGH') {
      return (
        <span
          className={twMerge(
            clsx(
              'inline-flex items-center gap-1.5 font-bold uppercase tracking-wider rounded-lg bg-md-gold text-md-black shadow-xs',
              basePadding,
              className
            )
          )}
        >
          <Zap className={iconSize} />
          <span>High Priority</span>
        </span>
      );
    }

    if (token === 'MEDIUM') {
      return (
        <span
          className={twMerge(
            clsx(
              'inline-flex items-center gap-1.5 font-semibold uppercase tracking-wider rounded-full bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-300 dark:border-slate-700',
              basePadding,
              className
            )
          )}
        >
          <Clock className={iconSize} />
          <span>Medium</span>
        </span>
      );
    }

    return (
      <span
        className={twMerge(
          clsx(
            'inline-flex items-center gap-1.5 font-medium uppercase tracking-wider rounded-full bg-neutral-100 dark:bg-neutral-900 text-content-secondary border border-content-secondary/20',
            basePadding,
            className
          )
        )}
      >
        <Circle className={iconSize} />
        <span>Low</span>
      </span>
    );
  }

  // Status mapping
  if (token === 'RESOLVED') {
    return (
      <span
        className={twMerge(
          clsx(
            'inline-flex items-center gap-1.5 font-bold uppercase tracking-wider rounded-full bg-md-black text-white shadow-xs',
            basePadding,
            className
          )
        )}
      >
        <CheckCircle2 className={iconSize} />
        <span>Resolved</span>
      </span>
    );
  }

  if (token === 'IN_PROGRESS' || token === 'ASSIGNED' || token === 'VERIFICATION') {
    return (
      <span
        className={twMerge(
          clsx(
            'inline-flex items-center gap-1.5 font-bold uppercase tracking-wider rounded-full bg-md-gold text-md-black shadow-xs',
            basePadding,
            className
          )
        )}
      >
        <CircleDot className={iconSize} />
        <span>In Progress</span>
      </span>
    );
  }

  // Default: Submitted / Open
  return (
    <span
      className={twMerge(
        clsx(
          'inline-flex items-center gap-1.5 font-bold uppercase tracking-wider rounded-full bg-neutral-black-06 text-content-primary border border-surface-border',
          basePadding,
          className
        )
      )}
    >
      <Circle className={iconSize} />
      <span>Submitted</span>
    </span>
  );
}
