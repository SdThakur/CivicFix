'use client';

import React from 'react';
import { usePathname } from 'next/navigation';

export default function Footer() {
  const pathname = usePathname();

  // Full-bleed interactive maps should never render a website footer
  if (pathname === '/map') {
    return null;
  }

  return (
    <footer className="border-t border-surface-border bg-surface-card-subtle py-8 text-center text-xs text-content-muted relative z-10">
      <div className="max-w-7xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="font-bold text-content-primary tracking-tight">CivicFix Platform</span>
          <span className="text-content-muted">— Municipal Operations Engine</span>
        </div>
        <p className="text-content-secondary">
          © 2026 CivicFix. Powered by Computer Vision, PostGIS & Machine Intelligence.
        </p>
      </div>
    </footer>
  );
}

