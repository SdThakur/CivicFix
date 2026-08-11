'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

export default function MunicipalLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    const userJson = localStorage.getItem('civicfix_user');
    const token = localStorage.getItem('civicfix_token');

    if (!userJson || !token) {
      router.push('/login');
      return;
    }

    try {
      const user = JSON.parse(userJson);
      // Ensure user is staff
      if (!user || user.role === 'CITIZEN') {
        router.push('/login');
      } else {
        setAuthorized(true);
      }
    } catch (e) {
      router.push('/login');
    }
  }, [router]);

  if (!authorized) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
      {children}
    </div>
  );
}
