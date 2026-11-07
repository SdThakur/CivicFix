'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { 
  ShieldAlert, 
  MapPin, 
  PlusCircle, 
  LayoutDashboard, 
  BarChart3, 
  Bot, 
  User, 
  LogOut, 
  Menu, 
  X,
  ClipboardList,
  HardHat,
  Wrench,
  Shield,
  Database,
  Eye,
  Users
} from 'lucide-react';
import TranslucencyPicker from '@/components/glass/TranslucencyPicker';
import LanguagePicker from '@/components/ui/LanguagePicker';
import { useI18n } from '@/lib/i18n';

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { t } = useI18n();
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const userJson = localStorage.getItem('civicfix_user');
    if (userJson) {
      try {
        setCurrentUser(JSON.parse(userJson));
      } catch (e) {
        console.error(e);
      }
    }
  }, [pathname]);

  const handleLogout = () => {
    localStorage.removeItem('civicfix_token');
    localStorage.removeItem('civicfix_user');
    setCurrentUser(null);
    router.push('/login');
  };

  const navLinks = [
    { href: '/', label: t('nav.home') },
    { href: '/map', label: t('nav.map'), icon: MapPin },
    { href: '/report', label: t('nav.report'), icon: PlusCircle, isCta: true },
  ];

  if (currentUser) {
    if (currentUser.role === 'CITIZEN') {
      navLinks.push({ href: '/dashboard', label: t('nav.dashboard'), icon: LayoutDashboard });
    } else if (currentUser.role === 'FIELD_WORKER') {
      navLinks.push({ href: '/field-worker', label: 'My Jobs', icon: HardHat });
    } else if (currentUser.role === 'INSPECTOR') {
      navLinks.push({ href: '/employee', label: 'Queue', icon: LayoutDashboard });
      navLinks.push({ href: '/inspections', label: 'Inspections', icon: ClipboardList });
    } else {
      navLinks.push({ href: '/employee', label: 'Operations Queue', icon: LayoutDashboard });
      navLinks.push({ href: '/service-requests', label: '311 Dispatch', icon: Shield });
      navLinks.push({ href: '/inspections', label: 'Inspections', icon: ClipboardList });
      navLinks.push({ href: '/crews', label: 'Crews', icon: Users });
      navLinks.push({ href: '/assets', label: 'Assets', icon: Database });
      navLinks.push({ href: '/preventive', label: 'Preventive', icon: Wrench });
      navLinks.push({ href: '/admin', label: 'Analytics', icon: BarChart3 });
      navLinks.push({ href: '/assistant', label: 'AI Assistant', icon: Bot });
    }
  }

  navLinks.push({ href: '/transparency', label: t('nav.transparency'), icon: Eye });

  return (
    <header className="sticky top-0 z-50 liquid-glass-surface specular-edge border-b border-surface-border backdrop-blur-[24px]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-20">
          
          {/* Logo with Maryland Heraldic Accent */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-md-red text-white flex items-center justify-center shadow-md group-hover:scale-105 transition-transform">
              <ShieldAlert className="w-5 h-5 text-white" />
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-1">
                <span className="font-extrabold text-xl tracking-tight text-content-primary font-display">
                  Civic<span className="text-md-red">Fix</span>
                </span>
                <span className="w-2 h-2 rounded-full bg-md-gold inline-block" />
              </div>
              <span className="text-[10px] text-content-secondary font-semibold tracking-wider uppercase">
                Public Infrastructure
              </span>
            </div>
          </Link>

          {/* Desktop Grouped Glass Navigation Bar */}
          <nav className="hidden md:flex items-center gap-1.5 p-1 rounded-2xl bg-neutral-black-03 border border-surface-border">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;

              if (link.isCta) {
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className="min-h-[44px] ml-1 px-4 py-2 rounded-xl btn-md-red text-xs font-bold flex items-center gap-2 shadow-sm"
                  >
                    {Icon && <Icon className="w-4 h-4 text-white" />}
                    <span>{link.label}</span>
                  </Link>
                );
              }

              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`min-h-[44px] px-3.5 py-2 rounded-xl text-xs font-semibold transition-all flex items-center gap-1.5 ${
                    isActive
                      ? 'liquid-glass-gold shadow-sm font-bold'
                      : 'text-content-secondary hover:text-content-primary hover:bg-neutral-black-06'
                  }`}
                >
                  {Icon && <Icon className="w-3.5 h-3.5 text-content-primary" />}
                  <span>{link.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Right Action Items & Preferences */}
          <div className="hidden md:flex items-center gap-2.5">
            <LanguagePicker />
            <TranslucencyPicker />

            {currentUser ? (
              <div className="flex items-center gap-3 border-l border-surface-border pl-3">
                <div className="flex flex-col text-right">
                  <span className="text-xs font-bold text-content-primary">{currentUser.full_name || currentUser.email}</span>
                  <span className="text-[10px] text-md-red font-bold tracking-wider uppercase">
                    {currentUser.role}
                  </span>
                </div>
                <button
                  onClick={handleLogout}
                  title="Logout"
                  className="min-h-[44px] min-w-[44px] p-2.5 rounded-xl text-content-secondary hover:text-md-red hover:bg-neutral-black-06 transition-colors flex items-center justify-center"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/login"
                  className="min-h-[44px] px-4 py-2 rounded-xl text-xs font-bold text-content-primary hover:bg-neutral-black-06 transition-colors flex items-center justify-center"
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  className="min-h-[44px] px-4 py-2 rounded-xl btn-md-gold text-xs font-bold flex items-center justify-center shadow-sm"
                >
                  Register
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Menu & Settings Button */}
          <div className="flex md:hidden items-center gap-2">
            <TranslucencyPicker />
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="min-h-[44px] min-w-[44px] p-2.5 rounded-xl text-content-primary hover:bg-neutral-black-06 active:scale-95 transition-all flex items-center justify-center"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer Sheet */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-surface-border bg-surface-card px-4 pt-3 pb-6 space-y-3 animate-in slide-in-from-top-4 duration-fast">
          <nav className="flex flex-col gap-1.5">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;

              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`min-h-[44px] px-4 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2.5 ${
                    link.isCta
                      ? 'btn-md-red text-white'
                      : isActive
                      ? 'liquid-glass-gold font-bold'
                      : 'text-content-secondary hover:text-content-primary hover:bg-neutral-black-06'
                  }`}
                >
                  {Icon && <Icon className="w-4 h-4" />}
                  <span>{link.label}</span>
                </Link>
              );
            })}
          </nav>

          <div className="pt-3 border-t border-surface-border space-y-3">
            <div className="flex items-center justify-between px-1">
              <span className="text-xs font-bold text-content-secondary">Language:</span>
              <LanguagePicker />
            </div>

            {currentUser ? (
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-bold text-content-primary">{currentUser.full_name}</div>
                  <div className="text-xs text-md-red font-semibold">{currentUser.role}</div>
                </div>
                <button
                  onClick={handleLogout}
                  className="min-h-[44px] px-4 py-2 rounded-xl text-xs font-bold text-md-red hover:bg-neutral-black-06"
                >
                  Log Out
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                <Link
                  href="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="min-h-[44px] py-2 rounded-xl text-center text-xs font-bold text-content-primary bg-neutral-black-06 flex items-center justify-center"
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  onClick={() => setMobileMenuOpen(false)}
                  className="min-h-[44px] py-2 rounded-xl text-center text-xs font-bold btn-md-gold flex items-center justify-center shadow-sm"
                >
                  Register
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
