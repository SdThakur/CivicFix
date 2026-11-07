'use client';

import React from 'react';
import Link from 'next/link';
import { LucideIcon, MapPin, RefreshCw, AlertCircle } from 'lucide-react';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
  isError?: boolean;
}

export default function EmptyState({
  icon: Icon = MapPin,
  title,
  description,
  actionLabel,
  actionHref,
  onAction,
  isError = false,
}: EmptyStateProps) {
  return (
    <div className="surface-card-solid p-10 sm:p-14 rounded-3xl text-center relative overflow-hidden border border-surface-border shadow-card space-y-4">
      {/* Faint Heraldic Maryland Motif Watermark (< 6% opacity) */}
      <div 
        className="absolute inset-0 pointer-events-none opacity-[0.04] bg-repeat z-0"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%230b0b0c' fill-rule='evenodd'%3E%3Cpath d='M0 0h30v30H0zM30 30h30v30H30z'/%3E%3Cpath d='M30 0h30v30H30zM0 30h30v30H0z' fill='%23e03a3e'/%3E%3C/g%3E%3C/svg%3E")`,
          backgroundSize: '40px 40px',
        }}
        aria-hidden="true"
      />

      {/* Content */}
      <div className="relative z-10 space-y-3 max-w-md mx-auto">
        <div className={`w-14 h-14 rounded-2xl flex items-center justify-center mx-auto shadow-sm ${
          isError ? 'bg-md-red-subtle border border-md-red/30 text-md-red' : 'bg-md-gold-subtle border border-md-gold/30 text-md-black'
        }`}>
          {isError ? <AlertCircle className="w-7 h-7 text-md-red" /> : <Icon className="w-7 h-7 text-md-black" />}
        </div>

        <h3 className="text-lg sm:text-xl font-black text-content-primary font-display">
          {title}
        </h3>
        
        <p className="text-xs sm:text-sm text-content-secondary leading-relaxed">
          {description}
        </p>

        {actionLabel && (
          <div className="pt-2">
            {actionHref ? (
              <Link
                href={actionHref}
                className="inline-flex items-center justify-center min-h-[44px] px-6 py-2.5 rounded-xl btn-md-red text-white text-xs font-bold shadow-sm hover:scale-105 active:scale-95 transition-all"
              >
                {actionLabel}
              </Link>
            ) : onAction ? (
              <button
                type="button"
                onClick={onAction}
                className="inline-flex items-center justify-center gap-2 min-h-[44px] px-6 py-2.5 rounded-xl btn-md-gold text-md-black text-xs font-bold shadow-sm hover:scale-105 active:scale-95 transition-all"
              >
                <RefreshCw className="w-3.5 h-3.5 text-md-black" />
                <span>{actionLabel}</span>
              </button>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}

