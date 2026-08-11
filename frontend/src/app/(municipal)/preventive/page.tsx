'use client';

import React, { useState, useEffect } from 'react';
import { AlertTriangle, ScanSearch, Check, X, Loader2, ShieldAlert } from 'lucide-react';
import { apiClient } from '@/lib/api';

export default function PreventiveMaintenancePage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);

  const fetchItems = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/preventive-maintenance/');
      setItems(res.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, []);

  const runScan = async () => {
    setScanning(true);
    try {
      await apiClient.post('/preventive-maintenance/scan');
      await fetchItems();
    } catch (err) {
      console.error(err);
    } finally {
      setScanning(false);
    }
  };

  const handleAction = async (id: string, action: 'approve' | 'reject') => {
    try {
      await apiClient.post(`/preventive-maintenance/${id}/${action}`);
      fetchItems();
    } catch (err) {
      console.error(err);
    }
  };

  const pendingCount = items.filter(i => i.status === 'PENDING').length;

  return (
    <div className="space-y-6 py-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Preventive Intelligence</h1>
          <p className="text-slate-400 text-sm mt-1">AI-driven predictive maintenance recommendations</p>
        </div>
        <button 
          onClick={runScan}
          disabled={scanning}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold transition-colors flex items-center gap-2 text-sm disabled:opacity-50"
        >
          {scanning ? <Loader2 className="w-4 h-4 animate-spin" /> : <ScanSearch className="w-4 h-4" />}
          Run AI Scan
        </button>
      </div>

      {pendingCount > 0 && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center gap-3 text-amber-400">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span className="font-semibold text-sm">{pendingCount} pending recommendations require review.</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-full p-12 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-blue-500" /></div>
        ) : items.length === 0 ? (
          <div className="col-span-full p-12 text-center text-slate-500 glass-panel border border-slate-800 rounded-2xl">
            No predictive recommendations available. Run a scan to generate insights.
          </div>
        ) : (
          items.map((item: any) => (
            <div key={item.id} className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col h-full">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <span className="px-2 py-1 text-[10px] font-bold rounded-full bg-slate-800 text-slate-300 uppercase tracking-wider">
                    {item.maintenance_type}
                  </span>
                  <h3 className="text-lg font-bold text-white mt-2 leading-tight">{item.target_name}</h3>
                </div>
                <div className="w-12 h-12 rounded-full border-4 border-amber-500/30 flex items-center justify-center relative">
                  <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 36 36">
                    <path
                      className="text-amber-500"
                      strokeDasharray={`${item.risk_score || 0}, 100`}
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                      fill="none" stroke="currentColor" strokeWidth="4"
                    />
                  </svg>
                  <span className="text-sm font-bold text-white">{item.risk_score || 0}</span>
                </div>
              </div>

              <div className="text-sm text-slate-400 bg-slate-900/50 p-3 rounded-xl border border-slate-800/50 mb-4 flex-grow">
                <ShieldAlert className="w-4 h-4 inline-block mr-1 text-slate-500" />
                {item.reasoning || 'Pattern identified based on historical failure rates and recent environmental factors.'}
              </div>

              <div className="text-xs text-slate-500 mb-4">
                Triggered by {item.incident_count || 3} related incidents in area.
              </div>

              {item.status === 'PENDING' ? (
                <div className="flex gap-3 mt-auto pt-4 border-t border-slate-800">
                  <button 
                    onClick={() => handleAction(item.id, 'reject')}
                    className="flex-1 py-2 rounded-xl border border-rose-500/30 text-rose-400 hover:bg-rose-500/10 font-semibold text-sm flex items-center justify-center gap-1 transition-colors"
                  >
                    <X className="w-4 h-4" /> Reject
                  </button>
                  <button 
                    onClick={() => handleAction(item.id, 'approve')}
                    className="flex-1 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm flex items-center justify-center gap-1 transition-colors"
                  >
                    <Check className="w-4 h-4" /> Approve WO
                  </button>
                </div>
              ) : (
                <div className="mt-auto pt-4 border-t border-slate-800 text-center">
                  <span className={`text-sm font-bold ${item.status === 'APPROVED' ? 'text-emerald-400' : 'text-slate-500'}`}>
                    {item.status}
                  </span>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
