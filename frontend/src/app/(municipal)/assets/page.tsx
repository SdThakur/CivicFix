'use client';

import React, { useState, useEffect } from 'react';
import { Search, Plus, MapPin, Activity, Loader2, Calendar } from 'lucide-react';
import { apiClient } from '@/lib/api';

const ASSET_ICONS: Record<string, string> = {
  'ROAD': '🛣️',
  'TRAFFIC_SIGNAL': '🚦',
  'STREETLIGHT': '💡',
  'SIGN': '🛑',
  'BRIDGE': '🌉',
  'OTHER': '🏗️'
};

const CONDITION_COLORS: Record<string, string> = {
  'EXCELLENT': 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  'GOOD': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  'FAIR': 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  'POOR': 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  'CRITICAL': 'bg-rose-500/20 text-rose-400 border-rose-500/30'
};

export default function AssetsPage() {
  const [assets, setAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState('ALL');

  const fetchAssets = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get('/assets/infrastructure', {
        params: filter !== 'ALL' ? { asset_type: filter } : {}
      });
      setAssets(res.data || []);
    } catch (err) {
      console.error(err);
      setError('Failed to fetch assets.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets();
  }, [filter]);

  return (
    <div className="space-y-6 py-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Infrastructure Asset Registry</h1>
          <p className="text-slate-400 text-sm mt-1">Geospatial inventory and condition tracking</p>
        </div>
        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold transition-colors flex items-center gap-2 text-sm">
          <Plus className="w-4 h-4" /> Register Asset
        </button>
      </div>

      {/* Error state */}
      {error && (
        <div className="flex items-center justify-between p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
          <div className="flex items-center gap-3">
            <span className="flex-shrink-0">⚠️</span>
            <span>{error}</span>
          </div>
          <button 
            onClick={fetchAssets} 
            className="px-3 py-1.5 text-xs font-semibold bg-rose-500/20 hover:bg-rose-500/30 rounded-lg transition-colors"
          >
            Try Again
          </button>
        </div>
      )}

      <div className="flex items-center gap-2 overflow-x-auto pb-2 no-scrollbar flex-nowrap">
        {['ALL', 'ROAD', 'TRAFFIC_SIGNAL', 'STREETLIGHT', 'SIGN', 'BRIDGE'].map(type => (
          <button
            key={type}
            onClick={() => setFilter(type)}
            className={`px-4 py-1.5 rounded-full text-xs font-semibold border whitespace-nowrap ${
              filter === type 
                ? 'bg-blue-600 text-white border-blue-500' 
                : 'bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700'
            }`}
          >
            {type === 'ALL' ? 'All Assets' : type.replace('_', ' ')}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {loading ? (
          <div className="col-span-full p-12 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-blue-500" /></div>
        ) : assets.length === 0 ? (
          <div className="col-span-full p-12 text-center text-slate-500 glass-panel border border-slate-800 rounded-2xl">
            No assets found for this category.
          </div>
        ) : (
          assets.map((asset: any) => (
            <div key={asset.id} className="glass-panel p-5 rounded-2xl border border-slate-800 hover:border-slate-700 transition-colors group cursor-pointer">
              <div className="flex justify-between items-start mb-3">
                <div className="text-3xl">{ASSET_ICONS[asset.type] || ASSET_ICONS['OTHER']}</div>
                <span className={`px-2 py-1 text-[10px] font-bold rounded-full border ${CONDITION_COLORS[asset.condition || 'FAIR']}`}>
                  {asset.condition || 'FAIR'}
                </span>
              </div>
              
              <h3 className="font-bold text-white text-base truncate">{asset.name}</h3>
              <div className="text-xs text-slate-400 font-mono mt-1 mb-4">{asset.asset_code}</div>

              <div className="space-y-2 text-xs text-slate-400">
                <div className="flex items-center gap-2">
                  <MapPin className="w-3.5 h-3.5" />
                  <span className="truncate">{asset.address || 'Geo-coordinates only'}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="w-3.5 h-3.5" />
                  <span>Inspected: {asset.last_inspected ? new Date(asset.last_inspected).toLocaleDateString() : 'Never'}</span>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-slate-800/50">
                <div className="flex justify-between text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
                  <span>Risk Profile</span>
                  <span>{asset.risk_score || 0}/100</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                  <div 
                    className={`h-full rounded-full ${((asset.risk_score || 0) > 75) ? 'bg-rose-500' : ((asset.risk_score || 0) > 50) ? 'bg-amber-500' : 'bg-emerald-500'}`}
                    style={{ width: `${Math.min(100, asset.risk_score || 0)}%` }}
                  />
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
