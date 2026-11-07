'use client';

import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface GlassContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export default function GlassContainer({
  className,
  children,
  ...props
}: GlassContainerProps) {
  return (
    <div
      className={twMerge(
        clsx(
          'liquid-glass-container p-1.5 flex items-center gap-1 specular-edge backdrop-blur-[24px]',
          className
        )
      )}
      {...props}
    >
      {children}
    </div>
  );
}

