'use client';

import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'rectangular' | 'circular' | 'card';
}

export default function Skeleton({ className, variant = 'rectangular' }: SkeletonProps) {
  const baseClasses = 'animate-pulse bg-neutral-200 dark:bg-neutral-800/60 rounded-xl';

  if (variant === 'circular') {
    return <div className={twMerge(clsx(baseClasses, 'rounded-full', className))} />;
  }

  if (variant === 'text') {
    return <div className={twMerge(clsx(baseClasses, 'h-4 w-3/4 rounded-md', className))} />;
  }

  if (variant === 'card') {
    return (
      <div className={twMerge(clsx('surface-card-solid p-6 rounded-3xl border border-surface-border space-y-4 animate-pulse', className))}>
        <div className="flex items-center justify-between">
          <div className="h-6 w-28 bg-neutral-200 dark:bg-neutral-800 rounded-lg" />
          <div className="h-6 w-20 bg-neutral-200 dark:bg-neutral-800 rounded-full" />
        </div>
        <div className="h-5 w-3/4 bg-neutral-200 dark:bg-neutral-800 rounded-md" />
        <div className="h-16 w-full bg-neutral-100 dark:bg-neutral-900 rounded-xl" />
        <div className="flex items-center justify-between pt-2">
          <div className="h-4 w-32 bg-neutral-200 dark:bg-neutral-800 rounded-md" />
          <div className="h-8 w-24 bg-neutral-200 dark:bg-neutral-800 rounded-xl" />
        </div>
      </div>
    );
  }

  return <div className={twMerge(clsx(baseClasses, className))} />;
}

export function FeedSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-4" role="status" aria-label="Loading reports feed">
      {Array.from({ length: count }).map((_, idx) => (
        <Skeleton key={idx} variant="card" />
      ))}
      <span className="sr-only">Loading content...</span>
    </div>
  );
}

