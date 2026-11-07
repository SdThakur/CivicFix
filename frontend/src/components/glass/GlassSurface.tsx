'use client';

import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface GlassSurfaceProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'gold' | 'red';
  specular?: boolean;
  concentric?: boolean;
  children: React.ReactNode;
}

export default function GlassSurface({
  variant = 'default',
  specular = true,
  concentric = true,
  className,
  children,
  ...props
}: GlassSurfaceProps) {
  const variantClasses = {
    default: 'liquid-glass-surface text-content-primary',
    gold: 'liquid-glass-gold',
    red: 'liquid-glass-red',
  }[variant];

  return (
    <div
      className={twMerge(
        clsx(
          variantClasses,
          specular && 'specular-edge',
          concentric ? 'rounded-2xl' : 'rounded-xl',
          'transition-all duration-normal ease-liquid',
          className
        )
      )}
      {...props}
    >
      {children}
    </div>
  );
}

