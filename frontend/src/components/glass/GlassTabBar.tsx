'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, MapPin, PlusCircle, LayoutDashboard } from 'lucide-react';

export default function GlassTabBar() {
  const pathname = usePathname();

  const tabs = [
    { href: '/', label: 'Home', icon: Home },
    { href: '/map', label: 'Map', icon: MapPin },
    { href: '/report', label: 'Report', icon: PlusCircle, isCta: true },
    { href: '/dashboard', label: 'Activity', icon: LayoutDashboard },
  ];

  return (
    <div className="fixed bottom-4 left-0 right-0 z-40 px-4 flex justify-center md:hidden pointer-events-none">
      <nav 
        aria-label="Mobile Navigation" 
        className="liquid-glass-surface specular-edge shadow-floating rounded-full p-1.5 flex items-center gap-1 border border-surface-border pointer-events-auto max-w-sm w-full justify-around backdrop-blur-[24px]"
      >
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = pathname === tab.href;

          if (tab.isCta) {
            return (
              <Link
                key={tab.href}
                href={tab.href}
                className="min-h-[44px] px-4 rounded-full btn-md-red text-white flex items-center gap-1.5 text-xs font-bold shadow-md"
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </Link>
            );
          }

          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`min-h-[44px] px-3.5 rounded-full flex items-center gap-1 text-xs font-bold transition-all ${
                isActive
                  ? 'liquid-glass-gold shadow-sm'
                  : 'text-content-secondary hover:text-content-primary'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}

