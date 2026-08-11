'use client';

import React, { useState, useEffect } from 'react';
import { 
  Search,
  Filter,
  CheckCircle,
  Clock,
  AlertTriangle,
  Camera,
  ClipboardCheck,
  ChevronRight,
  X,
  Loader2
} from 'lucide-react';
import { apiClient } from '@/lib/api';

export default function InspectionsPage() {
  const [inspections, setInspections] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedInspection, setSelectedInspection] = useState<any | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    confirmed_severity: 'LOW',
    safety_risk: 'LOW',
    lanes_affected: 0,
    estimated_area_sqm: 0,
    road_condition_rating: 5,
    recommended_repair: 'PATCH',
    estimated_repair_hours: 1,
    estimated_material_cost: 0,
    is_emergency: false,
    inspection_notes: ''
  });

  const fetchInspections = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get('/inspections/', {
        params: statusFilter !== 'ALL' ? { status: statusFilter } : {}
      });
      setInspections(res.data || []);
    } catch (err) {
      console.error(err);
      setError('Failed to fetch inspections.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInspections();
  }, [statusFilter]);

  const handleComplete = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInspection) return;
    setSubmitting(true);
    try {
      await apiClient.post(`/inspections/${selectedInspection.id}/complete`, formData);
      setSelectedInspection(null);
      fetchInspections();
    } catch (err) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'SCHEDULED': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'IN_PROGRESS': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'COMPLETED': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      default: return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
    }
  };

  return (
    <div className="space-y-6 py-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Infrastructure Inspections</h1>
          <p className="text-slate-400 text-sm mt-1">Manage physical verification of reported issues</p>
        </div>
        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-semibold transition-colors flex items-center gap-2 text-sm">
          <ClipboardCheck className="w-4 h-4" /> + Schedule Inspection
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-4">
        {['ALL', 'SCHEDULED', 'IN_PROGRESS', 'COMPLETED'].map(status => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={`px-4 py-1.5 rounded-full text-xs font-semibold border ${
              statusFilter === status 
                ? 'bg-blue-600 text-white border-blue-500' 
                : 'bg-slate-800 text-slate-400 border-slate-700 hover:bg-slate-700'
            }`}
          >
            {status.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="glass-panel border border-slate-800 rounded-2xl overflow-hidden">
        {error && (
          <div className="flex items-center justify-between p-4 bg-rose-500/10 border-b border-rose-500/30 text-rose-400 text-sm">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
            <button 
              onClick={fetchInspections} 
              className="px-3 py-1.5 text-xs font-semibold bg-rose-500/20 hover:bg-rose-500/30 rounded-lg transition-colors"
            >
              Try Again
            </button>
          </div>
        )}
        {loading ? (
          <div className="p-12 flex justify-center"><Loader2 className="w-6 h-6 animate-spin text-blue-500" /></div>
        ) : inspections.length === 0 ? (
          <div className="p-12 text-center text-slate-500">No inspections found matching criteria.</div>
        ) : (
          <>
            <div className="hidden md:block">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-900/50 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="p-4 font-semibold">Inspection No.</th>
                    <th className="p-4 font-semibold">Issue Title</th>
                    <th className="p-4 font-semibold">Inspector</th>
                    <th className="p-4 font-semibold">Status</th>
                    <th className="p-4 font-semibold">Scheduled</th>
                    <th className="p-4 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {inspections.map((ins: any) => (
                    <tr key={ins.id} className="hover:bg-slate-800/20 transition-colors">
                      <td className="p-4 text-white font-medium">{ins.inspection_number}</td>
                      <td className="p-4 text-slate-300">Issue #{ins.issue_id}</td>
                      <td className="p-4 text-slate-400">{ins.inspector_name || 'Unassigned'}</td>
                      <td className="p-4">
                        <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold border uppercase tracking-wider ${getStatusColor(ins.status)}`}>
                          {ins.status}
                        </span>
                      </td>
                      <td className="p-4 text-slate-400">
                        {ins.scheduled_date ? new Date(ins.scheduled_date).toLocaleDateString() : 'N/A'}
                      </td>
                      <td className="p-4 text-right">
                        <button 
                          onClick={() => {
                            setSelectedInspection(ins);
                            setFormData(prev => ({ ...prev, inspection_notes: ins.notes || '' }));
                          }}
                          className="text-blue-400 hover:text-blue-300 font-semibold flex items-center justify-end gap-1 w-full"
                        >
                          View <ChevronRight className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile Stacked Cards */}
            <div className="block md:hidden space-y-3 p-4 bg-slate-950">
              {inspections.map((ins: any) => (
                <div key={ins.id} className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                  <div className="flex justify-between items-start gap-2">
                    <div>
                      <div className="text-xs font-bold text-slate-400 mb-1">{ins.inspection_number}</div>
                      <h3 className="text-sm font-semibold text-white">Issue #{ins.issue_id}</h3>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${getStatusColor(ins.status)}`}>
                      {ins.status}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="flex flex-col gap-1">
                      <span className="text-slate-500 font-medium">Inspector</span>
                      <span className="text-slate-300">{ins.inspector_name || 'Unassigned'}</span>
                    </div>
                    <div className="flex flex-col gap-1">
                      <span className="text-slate-500 font-medium">Scheduled</span>
                      <span className="text-slate-300">
                        {ins.scheduled_date ? new Date(ins.scheduled_date).toLocaleDateString() : 'N/A'}
                      </span>
                    </div>
                  </div>

                  <button 
                    onClick={() => {
                      setSelectedInspection(ins);
                      setFormData(prev => ({ ...prev, inspection_notes: ins.notes || '' }));
                    }}
                    className="w-full mt-2 py-2 text-center text-blue-400 hover:text-blue-300 text-sm font-semibold border border-slate-800 rounded-lg bg-slate-800/50"
                  >
                    View Details
                  </button>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Detail Modal */}
      {selectedInspection && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/80 backdrop-blur-sm">
          <div className="w-full md:max-w-2xl bg-slate-900 border-l border-slate-800 h-full overflow-y-auto p-6 shadow-2xl animate-in slide-in-from-right">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">Complete Inspection</h2>
              <button onClick={() => setSelectedInspection(null)} className="p-2 text-slate-400 hover:text-white rounded-full hover:bg-slate-800">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row gap-4">
                {/* AI Recommendation */}
                <div className="flex-1 p-4 rounded-xl bg-blue-900/10 border border-blue-500/20 space-y-2">
                  <div className="text-xs font-bold text-blue-400 uppercase tracking-wider flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5" /> AI Recommendation
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="text-slate-400">Category: <span className="text-white">Pothole</span></div>
                    <div className="text-slate-400">Severity: <span className="text-amber-400">MEDIUM</span></div>
                    <div className="text-slate-400 col-span-2">Priority Score: <span className="text-white">72/100</span></div>
                  </div>
                </div>
              </div>

              {/* Form */}
              <form onSubmit={handleComplete} className="space-y-4">
                <div className="text-xs font-bold text-slate-400 uppercase tracking-wider border-b border-slate-800 pb-2">
                  Inspector's Official Finding
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1">Confirmed Severity</label>
                    <select 
                      value={formData.confirmed_severity} 
                      onChange={(e) => setFormData({...formData, confirmed_severity: e.target.value})}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-white text-sm"
                    >
                      <option value="LOW">LOW</option>
                      <option value="MEDIUM">MEDIUM</option>
                      <option value="HIGH">HIGH</option>
                      <option value="CRITICAL">CRITICAL</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1">Safety Risk</label>
                    <select 
                      value={formData.safety_risk} 
                      onChange={(e) => setFormData({...formData, safety_risk: e.target.value})}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-white text-sm"
                    >
                      <option value="LOW">LOW</option>
                      <option value="MODERATE">MODERATE</option>
                      <option value="HIGH">HIGH</option>
                      <option value="IMMINENT">IMMINENT</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1">Lanes Affected</label>
                    <input 
                      type="number" min="0" 
                      value={formData.lanes_affected} 
                      onChange={(e) => setFormData({...formData, lanes_affected: parseInt(e.target.value)})}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-white text-sm" 
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1">Est Area (sqm)</label>
                    <input 
                      type="number" min="0" step="0.1" 
                      value={formData.estimated_area_sqm} 
                      onChange={(e) => setFormData({...formData, estimated_area_sqm: parseFloat(e.target.value)})}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-white text-sm" 
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Road Condition Rating (1-10)</label>
                  <input 
                    type="range" min="1" max="10" 
                    value={formData.road_condition_rating} 
                    onChange={(e) => setFormData({...formData, road_condition_rating: parseInt(e.target.value)})}
                    className="w-full accent-blue-500" 
                  />
                  <div className="text-right text-xs text-slate-400 mt-1">{formData.road_condition_rating}/10</div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1">Recommended Repair</label>
                    <select 
                      value={formData.recommended_repair} 
                      onChange={(e) => setFormData({...formData, recommended_repair: e.target.value})}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-white text-sm"
                    >
                      <option value="PATCH">COLD PATCH</option>
                      <option value="MILL_AND_FILL">MILL AND FILL</option>
                      <option value="FULL_DEPTH">FULL DEPTH REPAIR</option>
                      <option value="REPLACE">REPLACE</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1">Est Hours</label>
                    <input 
                      type="number" min="0" 
                      value={formData.estimated_repair_hours} 
                      onChange={(e) => setFormData({...formData, estimated_repair_hours: parseInt(e.target.value)})}
                      className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-white text-sm" 
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2 mt-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20">
                  <input 
                    type="checkbox" id="emergency"
                    checked={formData.is_emergency}
                    onChange={(e) => setFormData({...formData, is_emergency: e.target.checked})}
                    className="w-4 h-4 rounded bg-slate-800 border-slate-600 text-rose-500 focus:ring-rose-500 focus:ring-offset-slate-900" 
                  />
                  <label htmlFor="emergency" className="text-sm font-bold text-rose-400">Mark as Emergency Hazard</label>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Inspection Notes</label>
                  <textarea 
                    rows={4}
                    value={formData.inspection_notes}
                    onChange={(e) => setFormData({...formData, inspection_notes: e.target.value})}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-white text-sm resize-none"
                    placeholder="Enter detailed findings..."
                  />
                </div>

                <div className="pt-4 flex justify-end gap-3 border-t border-slate-800">
                  <button type="button" onClick={() => setSelectedInspection(null)} className="px-4 py-2 text-sm font-semibold text-slate-300 hover:text-white">
                    Cancel
                  </button>
                  <button type="submit" disabled={submitting} className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold rounded-xl transition-colors flex items-center gap-2">
                    {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                    Mark Complete
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
