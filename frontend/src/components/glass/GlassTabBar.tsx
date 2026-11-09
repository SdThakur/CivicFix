'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Home, 
  MapPin, 
  Camera, 
  Building2, 
  User
} from 'lucide-react';

export default function GlassTabBar() {
  const pathname = usePathname();

  const dockItems = [
    { href: '/', label: 'Feed', icon: Home },
    { href: '/map', label: 'Map', icon: MapPin },
    { href: '/report', label: 'Instant Report', icon: Camera, isCta: true },
    { href: '/transparency', label: 'Directory', icon: Building2 },
    { href: '/dashboard', label: 'Profile', icon: User },
  ];

  return (
    <nav 
      aria-label="Civic Navigation Island"
      className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 pointer-events-auto"
    >
      <div className="civic-dock-island specular-edge px-3 py-2 flex items-center gap-1.5 sm:gap-2 shadow-2xl border border-black/[0.08] dark:border-white/[0.12]">
        {dockItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;

          if (item.isCta) {
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-label={item.label}
                aria-current={isActive ? 'page' : undefined}
                className="group relative flex items-center justify-center mx-1"
              >
                <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-[#b61825] to-[#e03a3e] text-white flex items-center justify-center shadow-[0_4px_18px_rgba(182,24,37,0.45)] hover:shadow-[0_6px_24px_rgba(182,24,37,0.6)] group-hover:scale-105 active:scale-95 transition-all">
                  <Icon className="w-5 h-5 text-white" />
                  <span className="absolute -top-1 -right-1 flex h-3 w-3">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#ffc72c] opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-3 w-3 bg-[#ffc72c]"></span>
                  </span>
                </div>
                <span className="sr-only">{item.label}</span>
              </Link>
            );
          }

          return (
            <Link
              key={item.href}
              href={item.href}
              aria-label={item.label}
              aria-current={isActive ? 'page' : undefined}
              className={`relative px-3 sm:px-4 py-2 rounded-full flex flex-col sm:flex-row items-center gap-1 sm:gap-1.5 text-xs font-bold transition-all duration-200 ${
                isActive
                  ? 'bg-[#ffc72c]/20 text-[#1b1c19] shadow-xs'
                  : 'text-[#5b403e] hover:text-[#1b1c19] hover:bg-black/[0.04]'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-[#b61825]' : 'text-[#767475]'}`} />
              <span className="text-[11px] font-semibold tracking-tight hidden sm:inline">{item.label}</span>
              {isActive && (
                <span className="absolute bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-[#b61825] sm:hidden" />
              )}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
