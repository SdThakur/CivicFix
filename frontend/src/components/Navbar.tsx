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
  Bell,
  ClipboardList,
  HardHat,
  Wrench,
  Shield,
  Database,
  Eye,
  Hammer,
  Users
} from 'lucide-react';

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
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
    { href: '/', label: 'Home' },
    { href: '/map', label: 'Public Map', icon: MapPin },
    { href: '/report', label: 'Report Problem', icon: PlusCircle, highlight: true },
  ];

  if (currentUser) {
    if (currentUser.role === 'CITIZEN') {
      navLinks.push({ href: '/dashboard', label: 'My Reports', icon: LayoutDashboard });
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
  // Public transparency always available
  navLinks.push({ href: '/transparency', label: 'Transparency', icon: Eye });

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 group-hover:scale-105 transition-transform">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-xl tracking-tight text-white flex items-center gap-1">
                Civic<span className="text-blue-500">Fix</span>
              </span>
              <span className="text-[10px] text-slate-400 font-medium tracking-wider uppercase">
                AI Infrastructure Ops
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;

              if (link.highlight) {
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className="ml-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm flex items-center gap-2 shadow-lg shadow-blue-600/20 transition-all hover:shadow-blue-600/30 hover:-translate-y-0.5"
                  >
                    {Icon && <Icon className="w-4 h-4" />}
                    {link.label}
                  </Link>
                );
              }

              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5 ${
                    isActive
                      ? 'bg-slate-800 text-blue-400 border border-slate-700'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
                  }`}
                >
                  {Icon && <Icon className="w-4 h-4 text-slate-400" />}
                  {link.label}
                </Link>
              );
            })}
          </nav>

          {/* Right Action Items */}
          <div className="hidden md:flex items-center gap-3">
            {currentUser ? (
              <div className="flex items-center gap-3 border-l border-slate-800 pl-3">
                <div className="flex flex-col text-right">
                  <span className="text-sm font-medium text-slate-200">{currentUser.full_name || currentUser.email}</span>
                  <span className="text-[11px] text-blue-400 font-semibold tracking-wider uppercase">
                    {currentUser.role}
                  </span>
                </div>
                <button
                  onClick={handleLogout}
                  title="Logout"
                  className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/login"
                  className="px-3.5 py-2 text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800/60 rounded-lg transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  className="px-3.5 py-2 text-sm font-medium bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 rounded-lg transition-colors"
                >
                  Register
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden items-center gap-2">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-300 hover:bg-slate-800 transition-colors"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-slate-800 bg-[#0f172a] px-4 pt-2 pb-4 space-y-2">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 rounded-lg text-base font-medium text-slate-200 hover:bg-slate-800"
            >
              {link.label}
            </Link>
          ))}
          {currentUser ? (
            <button
              onClick={handleLogout}
              className="w-full text-left px-3 py-2 rounded-lg text-base font-medium text-rose-400 hover:bg-rose-500/10"
            >
              Logout
            </button>
          ) : (
            <div className="pt-2 border-t border-slate-800 flex flex-col gap-2">
              <Link
                href="/login"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full text-center px-3 py-2 rounded-lg text-slate-200 bg-slate-800"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                onClick={() => setMobileMenuOpen(false)}
                className="w-full text-center px-3 py-2 rounded-lg text-white bg-blue-600"
              >
                Register
              </Link>
            </div>
          )}
        </div>
      )}
    </header>
  );
}
