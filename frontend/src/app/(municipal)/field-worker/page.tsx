'use client';

import React, { useState, useEffect } from 'react';
import { MapPin, Navigation, Camera, CheckCircle2, AlertTriangle, Loader2, Upload, X } from 'lucide-react';
import { apiClient, workOrderApi } from '@/lib/api';

export default function FieldWorkerPage() {
  const [workOrders, setWorkOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeStep, setActiveStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [beforePhoto, setBeforePhoto] = useState<string | null>(null);
  const [afterPhoto, setAfterPhoto] = useState<string | null>(null);
  const [isBlockedModalOpen, setIsBlockedModalOpen] = useState(false);
  const [blockedReason, setBlockedReason] = useState('Cannot access location');
  const [blockedNotes, setBlockedNotes] = useState('');

  useEffect(() => {
    const fetchWO = async () => {
      setLoading(true);
      try {
        const res = await apiClient.get('/work-orders/', { params: { assigned: 'me' } });
        setWorkOrders(res.data || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchWO();
  }, []);

  const activeJob = workOrders.length > 0 ? workOrders[0] : null;

  if (loading) {
    return <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4"><Loader2 className="w-8 h-8 animate-spin text-blue-500" /></div>;
  }

  if (!activeJob) {
    return (
      <div className="min-h-screen bg-slate-950 p-4 text-center flex flex-col items-center justify-center">
        <CheckCircle2 className="w-16 h-16 text-emerald-500 mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">You're all caught up!</h2>
        <p className="text-slate-400">No active jobs assigned to you right now.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 max-w-[480px] mx-auto pb-24">
      {/* Header */}
      <div className="mb-6 pt-2">
        <div className="text-slate-400 text-sm font-semibold uppercase tracking-wider mb-1">Current Job</div>
        <h1 className="text-2xl font-black text-white">{activeJob.title || `Work Order #${activeJob.id}`}</h1>
      </div>

      {/* Main Card */}
      <div className="glass-panel p-5 rounded-3xl border border-slate-800 space-y-6">
        <div className="flex items-start gap-3 p-3 bg-slate-900/80 rounded-2xl border border-slate-800/80">
          <MapPin className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" />
          <div>
            <div className="text-sm font-bold text-white mb-1">{activeJob.address || 'Address not specified'}</div>
            <a href={`https://maps.google.com/?q=${activeJob.latitude},${activeJob.longitude}`} target="_blank" rel="noreferrer" className="text-xs text-blue-400 font-semibold flex items-center gap-1">
              <Navigation className="w-3 h-3" /> Open in Maps
            </a>
          </div>
        </div>

        {/* Workflow Steps */}
        <div className="space-y-0 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-700 before:to-transparent">
          
          {/* Step 1 */}
          <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active pb-6">
            <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 bg-slate-900 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow shadow-slate-950 ${activeStep > 1 ? 'border-emerald-500 text-emerald-500' : activeStep === 1 ? 'border-blue-500 text-blue-500' : 'border-slate-700 text-slate-500'}`}>
              <Navigation className="w-4 h-4" />
            </div>
            <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-2xl border border-slate-800 bg-slate-900/50">
              <h3 className="font-bold text-white text-sm mb-2">Navigate to Location</h3>
              {activeStep === 1 ? (
                <button 
                  onClick={async () => {
                    setSubmitting(true);
                    try {
                      await workOrderApi.updateStatus(activeJob.id, 'IN_PROGRESS');
                      setActiveStep(2);
                    } catch(e) { console.error(e); }
                    setSubmitting(false);
                  }} 
                  disabled={submitting}
                  className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold"
                >
                  Start Work
                </button>
              ) : (
                <div className="text-xs text-slate-400">Work Started</div>
              )}
            </div>
          </div>

          {/* Step 2 */}
          <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group pb-6">
            <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 bg-slate-900 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow shadow-slate-950 ${activeStep > 2 ? 'border-emerald-500 text-emerald-500' : activeStep === 2 ? 'border-blue-500 text-blue-500' : 'border-slate-700 text-slate-500'}`}>
              <Camera className="w-4 h-4" />
            </div>
            <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-2xl border border-slate-800 bg-slate-900/50">
              <h3 className="font-bold text-white text-sm mb-2">Before Photo</h3>
              {activeStep === 2 ? (
                <div>
                  <label className="w-full py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white rounded-xl text-xs font-semibold flex items-center justify-center gap-2 cursor-pointer">
                    <Camera className="w-4 h-4" /> Upload Before Photo
                    <input type="file" accept="image/*" className="hidden" onChange={async (e) => {
                      if (e.target.files && e.target.files[0]) {
                        setSubmitting(true);
                        try {
                          await workOrderApi.uploadBeforePhoto(activeJob.id, e.target.files[0]);
                          setBeforePhoto(URL.createObjectURL(e.target.files[0]));
                          setActiveStep(3);
                        } catch(e) { console.error(e); }
                        setSubmitting(false);
                      }
                    }} />
                  </label>
                  {submitting && <div className="text-xs text-slate-400 mt-2 text-center">Uploading...</div>}
                </div>
              ) : beforePhoto ? (
                <img src={beforePhoto} className="w-full h-24 object-cover rounded-lg" alt="Before" />
              ) : (
                <div className="text-xs text-slate-500">Pending</div>
              )}
            </div>
          </div>

          {/* Step 3 */}
          <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group pb-6">
            <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 bg-slate-900 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow shadow-slate-950 ${activeStep > 3 ? 'border-emerald-500 text-emerald-500' : activeStep === 3 ? 'border-blue-500 text-blue-500' : 'border-slate-700 text-slate-500'}`}>
              <Camera className="w-4 h-4" />
            </div>
            <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-2xl border border-slate-800 bg-slate-900/50">
              <h3 className="font-bold text-white text-sm mb-2">After Photo</h3>
              {activeStep === 3 ? (
                <div>
                  <label className="w-full py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white rounded-xl text-xs font-semibold flex items-center justify-center gap-2 cursor-pointer">
                    <Camera className="w-4 h-4" /> Upload After Photo
                    <input type="file" accept="image/*" className="hidden" onChange={async (e) => {
                      if (e.target.files && e.target.files[0]) {
                        setSubmitting(true);
                        try {
                          await workOrderApi.uploadAfterPhoto(activeJob.id, e.target.files[0]);
                          setAfterPhoto(URL.createObjectURL(e.target.files[0]));
                          setActiveStep(4);
                        } catch(e) { console.error(e); }
                        setSubmitting(false);
                      }
                    }} />
                  </label>
                  {submitting && <div className="text-xs text-slate-400 mt-2 text-center">Uploading...</div>}
                </div>
              ) : afterPhoto ? (
                <img src={afterPhoto} className="w-full h-24 object-cover rounded-lg" alt="After" />
              ) : (
                <div className="text-xs text-slate-500">Pending</div>
              )}
            </div>
          </div>

          {/* Step 4 */}
          <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group">
            <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 bg-slate-900 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow shadow-slate-950 ${activeStep > 4 ? 'border-emerald-500 text-emerald-500' : activeStep === 4 ? 'border-blue-500 text-blue-500' : 'border-slate-700 text-slate-500'}`}>
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-2xl border border-slate-800 bg-slate-900/50">
              <h3 className="font-bold text-white text-sm mb-2">Complete Work</h3>
              {activeStep === 4 ? (
                <button 
                  onClick={async () => {
                    setSubmitting(true);
                    try {
                      await workOrderApi.updateStatus(activeJob.id, 'COMPLETED');
                      window.location.reload();
                    } catch(e) { console.error(e); }
                    setSubmitting(false);
                  }}
                  disabled={submitting} 
                  className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold"
                >
                  Complete Repair
                </button>
              ) : (
                <div className="text-xs text-slate-500">Pending</div>
              )}
            </div>
          </div>

        </div>

        <button 
          onClick={() => setIsBlockedModalOpen(true)}
          className="w-full py-3 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-400 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition-colors"
        >
          <AlertTriangle className="w-4 h-4" /> Report Blocked Work
        </button>
      </div>
      
      {/* Queue */}
      {workOrders.length > 1 && (
        <div className="mt-8">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 px-2">Up Next</h3>
          <div className="space-y-2">
            {workOrders.slice(1).map((wo: any) => (
              <div key={wo.id} className="p-3 rounded-xl bg-slate-900/50 border border-slate-800 flex justify-between items-center opacity-70">
                <div className="truncate pr-4 text-sm font-medium text-slate-300">{wo.title}</div>
                <div className="text-xs text-slate-500 flex-shrink-0">WO #{wo.id}</div>
              </div>
            ))}
          </div>
        </div>
      )}
      {/* Blocked Work Modal */}
      {isBlockedModalOpen && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-slate-950/80 p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl p-6 relative">
            <button onClick={() => setIsBlockedModalOpen(false)} className="absolute top-4 right-4 text-slate-400 hover:text-white">
              <X className="w-5 h-5" />
            </button>
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-rose-500" /> Report Blocked Work
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Reason</label>
                <select 
                  value={blockedReason}
                  onChange={e => setBlockedReason(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white text-sm outline-none focus:border-blue-500"
                >
                  <option>Cannot access location</option>
                  <option>Wrong issue description</option>
                  <option>Missing equipment/materials</option>
                  <option>Safety hazard</option>
                  <option>Adverse weather</option>
                  <option>Other</option>
                </select>
              </div>
              
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Notes</label>
                <textarea 
                  value={blockedNotes}
                  onChange={e => setBlockedNotes(e.target.value)}
                  rows={3} 
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white text-sm outline-none focus:border-blue-500"
                  placeholder="Describe the issue preventing work..."
                />
              </div>
              
              <button 
                disabled={submitting}
                onClick={async () => {
                  setSubmitting(true);
                  try {
                    await workOrderApi.reportBlocked(activeJob.id, blockedReason, blockedNotes);
                    window.location.reload();
                  } catch (e) {
                    console.error(e);
                  }
                  setSubmitting(false);
                }}
                className="w-full py-3 bg-rose-600 hover:bg-rose-500 text-white font-semibold rounded-xl mt-2 flex justify-center items-center gap-2"
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Submit Report'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
