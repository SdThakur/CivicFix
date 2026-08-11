'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ShieldAlert, Mail, Lock, LogIn, ArrowRight } from 'lucide-react';
import { authApi } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const tokenRes = await authApi.login(email, password);
      localStorage.setItem('civicfix_token', tokenRes.access_token);
      
      const userRes = await authApi.me();
      localStorage.setItem('civicfix_user', JSON.stringify(userRes));

      if (userRes.role === 'CITIZEN') {
        router.push('/dashboard');
      } else {
        router.push('/employee');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid email or password. Try citizen@civicfix.gov / password');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (demoRole: string) => {
    if (demoRole === 'citizen') {
      setEmail('citizen@civicfix.gov');
      setPassword('password123');
    } else if (demoRole === 'employee') {
      setEmail('employee@civicfix.gov');
      setPassword('password123');
    } else if (demoRole === 'admin') {
      setEmail('admin@civicfix.gov');
      setPassword('password123');
    }
  };

  return (
    <div className="max-w-md mx-auto py-12 space-y-6">
      <div className="text-center space-y-2">
        <div className="w-12 h-12 rounded-2xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 mx-auto">
          <ShieldAlert className="w-7 h-7" />
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Sign in to CivicFix</h1>
        <p className="text-slate-400 text-sm">Access your citizen dashboard or municipal portal</p>
      </div>

      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-800 space-y-6">
        {error && (
          <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="citizen@civicfix.gov"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900/80 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 text-sm"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900/80 border border-slate-800 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 text-sm"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
          >
            {loading ? 'Authenticating...' : 'Sign In'}
            <LogIn className="w-4 h-4" />
          </button>
        </form>

        {/* Demo Fast Login Pills */}
        <div className="pt-4 border-t border-slate-800/80 space-y-2">
          <span className="text-xs text-slate-400 font-medium block">Quick Demo Login:</span>
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => handleQuickLogin('citizen')}
              className="py-1.5 px-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-[11px] font-medium text-slate-300"
            >
              👤 Citizen
            </button>
            <button
              onClick={() => handleQuickLogin('employee')}
              className="py-1.5 px-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-[11px] font-medium text-slate-300"
            >
              👷 Employee
            </button>
            <button
              onClick={() => handleQuickLogin('admin')}
              className="py-1.5 px-2 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-[11px] font-medium text-slate-300"
            >
              👑 Admin
            </button>
          </div>
        </div>
      </div>

      <p className="text-center text-xs text-slate-400">
        Don&apos;t have an account?{' '}
        <Link href="/register" className="text-blue-400 font-semibold hover:underline">
          Register as Citizen
        </Link>
      </p>
    </div>
  );
}
