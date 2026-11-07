'use client';

import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface GlassButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'accent' | 'glass' | 'glass-gold' | 'glass-red';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  children: React.ReactNode;
}

export default function GlassButton({
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  className,
  disabled,
  children,
  ...props
}: GlassButtonProps) {
  const variantStyles = {
    // Red Solid CTA with White Text (4.92:1 AA)
    primary: 'btn-md-red border border-transparent font-bold',
    // Gold Solid Action with Black Text (12.4:1 AAA)
    accent: 'btn-md-gold border border-transparent font-bold',
    // Liquid Glass on White with Black Text (19.8:1 AAA)
    glass: 'liquid-glass-surface text-content-primary hover:bg-white/80 active:bg-white/90 border-surface-border font-semibold shadow-glass-sm',
    // Gold Tint Glass with Black Text (16.5:1 AAA)
    'glass-gold': 'liquid-glass-gold font-bold',
    // Red Tint Glass for Urgency
    'glass-red': 'liquid-glass-red font-bold',
  }[variant];

  const sizeStyles = {
    sm: 'min-h-[44px] min-w-[44px] px-3.5 py-2 text-xs rounded-lg gap-1.5',
    md: 'min-h-[44px] min-w-[44px] px-5 py-2.5 text-sm rounded-xl gap-2',
    lg: 'min-h-[48px] min-w-[48px] px-7 py-3.5 text-base rounded-2xl gap-2.5',
  }[size];

  return (
    <button
      className={twMerge(
        clsx(
          'liquid-glass-button relative inline-flex items-center justify-center tracking-tight transition-all duration-fast ease-spring focus-visible:ring-2 focus-visible:ring-md-red/40',
          variantStyles,
          sizeStyles,
          fullWidth && 'w-full',
          disabled && 'opacity-50 cursor-not-allowed transform-none pointer-events-none',
          className
        )
      )}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}

