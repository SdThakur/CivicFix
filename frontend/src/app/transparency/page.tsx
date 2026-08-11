'use client';

import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  MapPin, 
  Download, 
  CheckCircle2, 
  AlertCircle,
  Clock,
  Activity,
  Loader2,
  Building2,
  TrendingUp
} from 'lucide-react';
import { apiClient } from '@/lib/api';

export default function TransparencyPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTransparency = async () => {
      try {
        const res = await apiClient.get('/transparency/summary');
        setData(res.data);
      } catch (err: any) {
        setError('Unable to load transparency data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    fetchTransparency();
  }, []);

  const handleDownload = () => {
    window.location.href = `${apiClient.defaults.baseURL}/transparency/export/issues.csv`;
  };

  const maxCount = data?.category_breakdown 
    ? Math.max(...data.category_breakdown.map((c: any) => c.count))
    : 100;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans p-6 md:p-12 space-y-12">
      {/* Hero Section */}
      <div className="max-w-5xl mx-auto space-y-4 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-2">
          <Building2 className="w-4 h-4" /> Public Data Portal
        </div>
        <h1 className="text-4xl md:text-6xl font-extrabold text-white tracking-tight">
          City Infrastructure Transparency
        </h1>
        <p className="text-slate-400 text-lg max-w-2xl mx-auto">
          Open data on municipal service requests, infrastructure repairs, and departmental performance metrics, updated in real-time.
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-24">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      ) : error ? (
        <div className="max-w-3xl mx-auto flex items-center gap-3 p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      ) : (
        <div className="max-w-6xl mx-auto space-y-12">
          {/* KPI Row */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="glass-panel p-5 rounded-2xl border border-slate-800 text-center">
              <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">Total Reports</div>
              <div className="text-2xl font-black text-white">{data?.total_reports || 0}</div>
            </div>
            <div className="glass-panel p-5 rounded-2xl border border-slate-800 text-center">
              <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">Resolved</div>
              <div className="text-2xl font-black text-emerald-400">{data?.resolved_reports || 0}</div>
            </div>
            <div className="glass-panel p-5 rounded-2xl border border-slate-800 text-center">
              <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">Resolution Rate</div>
              <div className="text-2xl font-black text-blue-400">{data?.resolution_rate_pct || 0}%</div>
            </div>
            <div className="glass-panel p-5 rounded-2xl border border-slate-800 text-center">
              <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">SLA Compliance</div>
              <div className="text-2xl font-black text-amber-400">{data?.sla_compliance_pct || 0}%</div>
            </div>
            <div className="glass-panel p-5 rounded-2xl border border-slate-800 text-center">
              <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">Avg Response</div>
              <div className="text-2xl font-black text-white">{data?.avg_response_hours || 0}h</div>
            </div>
            <div className="glass-panel p-5 rounded-2xl border border-slate-800 text-center">
              <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider mb-1">Avg Resolution</div>
              <div className="text-2xl font-black text-white">{data?.avg_resolution_days || 0}d</div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Pure CSS Bar Chart */}
            <div className="glass-panel p-6 rounded-3xl border border-slate-800">
              <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-6">
                <BarChart3 className="w-5 h-5 text-blue-400" /> Top Issue Categories
              </h3>
              <div className="space-y-4">
                {(data?.category_breakdown || []).map((cat: any) => (
                  <div key={cat.category} className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-300 font-medium">{cat.category}</span>
                      <span className="text-slate-400">{cat.count}</span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                      <div 
                        className="bg-blue-500 h-full rounded-full transition-all duration-1000"
                        style={{ width: `${Math.max(1, (cat.count / maxCount) * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Status Breakdown & Export */}
            <div className="space-y-8">
              <div className="glass-panel p-6 rounded-3xl border border-slate-800">
                <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-6">
                  <Activity className="w-5 h-5 text-emerald-400" /> Current Issue Status
                </h3>
                <div className="flex flex-wrap gap-4">
                  <div className="flex-1 min-w-[120px] bg-slate-800/50 p-4 rounded-2xl border border-slate-700/50 text-center">
                    <div className="text-3xl font-black text-rose-400">{data?.status_breakdown?.open || 0}</div>
                    <div className="text-xs text-slate-400 font-semibold uppercase mt-1">Open</div>
                  </div>
                  <div className="flex-1 min-w-[120px] bg-slate-800/50 p-4 rounded-2xl border border-slate-700/50 text-center">
                    <div className="text-3xl font-black text-amber-400">{data?.status_breakdown?.in_progress || 0}</div>
                    <div className="text-xs text-slate-400 font-semibold uppercase mt-1">In Progress</div>
                  </div>
                  <div className="flex-1 min-w-[120px] bg-slate-800/50 p-4 rounded-2xl border border-slate-700/50 text-center">
                    <div className="text-3xl font-black text-emerald-400">{data?.status_breakdown?.resolved || 0}</div>
                    <div className="text-xs text-slate-400 font-semibold uppercase mt-1">Resolved</div>
                  </div>
                </div>
              </div>

              <div className="glass-panel p-6 rounded-3xl border border-slate-800 text-center space-y-4">
                <Download className="w-8 h-8 text-blue-400 mx-auto" />
                <div>
                  <h4 className="text-white font-bold">Open Data Export</h4>
                  <p className="text-sm text-slate-400 mt-1">Download complete historical incident data in CSV format for independent analysis.</p>
                </div>
                <button 
                  onClick={handleDownload}
                  className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white py-3 rounded-xl font-semibold transition-colors"
                >
                  <Download className="w-4 h-4" /> Download Open Data
                </button>
              </div>
            </div>
          </div>

          {/* Map Placeholder */}
          <div className="glass-panel p-2 rounded-3xl border border-slate-800">
            <div className="bg-slate-900 rounded-[22px] h-96 flex flex-col items-center justify-center border border-slate-800/50 relative overflow-hidden">
              <div className="absolute inset-0 opacity-10 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-500 via-slate-900 to-slate-900"></div>
              <MapPin className="w-12 h-12 text-blue-500 mb-4 animate-bounce" />
              <h3 className="text-xl font-bold text-white relative z-10">Live Issue Map</h3>
              <p className="text-slate-400 relative z-10 mt-2">{data?.active_reports || 0} active reports across the city</p>
              <div className="mt-4 px-4 py-2 bg-slate-800/80 rounded-full border border-slate-700 text-sm text-slate-300 relative z-10">
                Map visualization requires API key
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="max-w-6xl mx-auto text-center pt-8 border-t border-slate-800/50 text-slate-500 text-sm">
        Data updated in real-time. No personally identifiable information is included.
      </footer>
    </div>
  );
}
