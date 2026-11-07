'use client';

import React from 'react';
import { usePathname } from 'next/navigation';

export default function MainContentWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isMap = pathname === '/map';

  return (
    <main
      className={`flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 relative z-10 transition-all ${
        isMap
          ? 'py-2 sm:py-4 pb-20 md:pb-4 flex flex-col min-h-0'
          : 'py-6 pb-24 md:pb-12'
      }`}
    >
      {children}
    </main>
  );
}

