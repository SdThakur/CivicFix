'use client';

import React, { useState, useEffect } from 'react';
import { Users, Plus, HardHat, AlertTriangle, Loader2 } from 'lucide-react';
import { apiClient } from '@/lib/api';

export default function CrewsPage() {
  const [crews, setCrews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchCrews = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/crews/');
      setCrews(res.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCrews();
  }, []);

  return (
    <div className="space-y-6 py-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Crew & Resource Management</h1>
          <p className="text-slate-400 text-sm mt-1">Manage field teams, equipment, and workloads</p>
        </div>
        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold transition-colors flex items-center gap-2 text-sm">
          <Plus className="w-4 h-4" /> Add Crew
        </button>
      </div>

      {loading ? (
        <div className="p-12 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-blue-500" /></div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {crews.map(crew => (
            <div key={crew.id} className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4">
                <span className={`px-2 py-1 text-[10px] font-bold rounded-full uppercase tracking-wider ${crew.status === 'ACTIVE' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700/50 text-slate-400'}`}>
                  {crew.status}
                </span>
              </div>
              
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <HardHat className="w-5 h-5 text-blue-400" />
                  <h3 className="text-lg font-bold text-white">{crew.name}</h3>
                </div>
                <div className="text-xs font-mono text-slate-500">{crew.crew_code} • {crew.department_name}</div>
              </div>

              <div className="space-y-3 pt-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Supervisor</span>
                  <span className="text-slate-200">{crew.supervisor_name || 'N/A'}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Base</span>
                  <span className="text-slate-200">{crew.home_base_address || 'Unassigned'}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-slate-400">Members</span>
                  <div className="flex -space-x-2">
                    {Array.from({length: Math.min(crew.member_count || 0, 4)}).map((_, i) => (
                      <div key={i} className="w-7 h-7 rounded-full bg-slate-700 border-2 border-slate-900 flex items-center justify-center text-[10px] font-bold text-white">
                        U
                      </div>
                    ))}
                    {(crew.member_count || 0) > 4 && (
                      <div className="w-7 h-7 rounded-full bg-slate-800 border-2 border-slate-900 flex items-center justify-center text-[10px] font-bold text-slate-400">
                        +{(crew.member_count || 0) - 4}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-800">
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Job Utilization</span>
                  <span className="text-white font-medium">{crew.active_jobs} / {crew.max_concurrent_jobs}</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                  <div 
                    className={`h-full rounded-full ${crew.active_jobs >= crew.max_concurrent_jobs ? 'bg-rose-500' : 'bg-blue-500'}`}
                    style={{ width: `${Math.min(100, ((crew.active_jobs || 0) / (crew.max_concurrent_jobs || 1)) * 100)}%` }}
                  />
                </div>
              </div>

              <button className="w-full py-2 bg-slate-800/50 hover:bg-slate-700 border border-slate-700 rounded-xl text-sm font-semibold text-white transition-colors mt-2">
                View Details
              </button>
            </div>
          ))}
          {crews.length === 0 && (
            <div className="col-span-full p-12 text-center text-slate-500 border border-dashed border-slate-700 rounded-2xl">
              No crews defined. Create your first crew to start assigning work orders.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
