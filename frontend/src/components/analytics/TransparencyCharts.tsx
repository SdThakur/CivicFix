'use client';

import React from 'react';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ReferenceLine 
} from 'recharts';
import { TrendingUp, MapPin, Clock } from 'lucide-react';

interface TransparencyChartsProps {
  trendData: Array<{ week: string; reported: number; resolved: number }>;
  neighborhoodData: Array<{ neighborhood: string; total: number; resolved: number }>;
  slaData: Array<{ category: string; avgHours: number; target: number }>;
}

export default function TransparencyCharts({
  trendData,
  neighborhoodData,
  slaData,
}: TransparencyChartsProps) {
  return (
    <div className="space-y-8">
      {/* 1. Historical Trend Line Chart */}
      <div className="surface-card-solid p-6 sm:p-8 rounded-3xl space-y-4 border border-surface-border">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-surface-border pb-3">
          <div>
            <h3 className="text-lg font-black text-content-primary flex items-center gap-2 font-display">
              <TrendingUp className="w-5 h-5 text-md-red" />
              <span>Reported vs. Resolved Incidents Trend</span>
            </h3>
            <p className="text-xs text-content-secondary mt-0.5">
              Weekly citywide hazard intake velocity compared against verified crew repair completions.
            </p>
          </div>

          <div className="flex items-center gap-4 text-xs font-bold text-content-secondary">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-0.5 bg-md-red inline-block" />
              <span>Reported (Solid)</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-0.5 border-t-2 border-dashed border-md-black inline-block" />
              <span>Resolved (Dashed)</span>
            </span>
          </div>
        </div>

        <div className="h-72 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trendData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
              <XAxis dataKey="week" stroke="#0B0B0C" fontSize={12} tickLine={false} />
              <YAxis stroke="#0B0B0C" fontSize={12} tickLine={false} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#FFFFFF', 
                  borderColor: '#E5E7EB', 
                  borderRadius: '16px',
                  fontSize: '12px',
                  boxShadow: '0 8px 30px rgba(0,0,0,0.08)'
                }} 
              />
              <Line 
                type="monotone" 
                dataKey="reported" 
                name="Reported Incidents"
                stroke="#E03A3E" 
                strokeWidth={3} 
                dot={{ r: 5, fill: '#E03A3E' }}
                activeDot={{ r: 7 }}
              />
              <Line 
                type="monotone" 
                dataKey="resolved" 
                name="Resolved Tickets"
                stroke="#0B0B0C" 
                strokeWidth={3} 
                strokeDasharray="5 5"
                dot={{ r: 5, fill: '#0B0B0C' }}
                activeDot={{ r: 7 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 2. Neighborhood & SLA Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Neighborhood Breakdown Chart */}
        <div className="surface-card-solid p-6 sm:p-8 rounded-3xl space-y-4 border border-surface-border">
          <div className="border-b border-surface-border pb-3">
            <h3 className="text-lg font-black text-content-primary flex items-center gap-2 font-display">
              <MapPin className="w-5 h-5 text-md-gold" />
              <span>Neighborhood Volume Breakdown</span>
            </h3>
            <p className="text-xs text-content-secondary mt-0.5">
              Submissions and resolved tickets by Maryland municipal corridor.
            </p>
          </div>

          <div className="h-72 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={neighborhoodData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                <XAxis dataKey="neighborhood" stroke="#0B0B0C" fontSize={10} tickLine={false} interval={0} />
                <YAxis stroke="#0B0B0C" fontSize={12} tickLine={false} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#FFFFFF', 
                    borderColor: '#E5E7EB', 
                    borderRadius: '16px',
                    fontSize: '12px' 
                  }} 
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Bar dataKey="total" name="Total Submissions" fill="#FFC72C" radius={[6, 6, 0, 0]} />
                <Bar dataKey="resolved" name="Resolved Tickets" fill="#0B0B0C" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* SLA Performance vs Benchmark */}
        <div className="surface-card-solid p-6 sm:p-8 rounded-3xl space-y-4 border border-surface-border">
          <div className="border-b border-surface-border pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-lg font-black text-content-primary flex items-center gap-2 font-display">
                <Clock className="w-5 h-5 text-md-black" />
                <span>Average Resolution Hours by Category</span>
              </h3>
              <p className="text-xs text-content-secondary mt-0.5">
                Compared against the 48-Hour Municipal Resolution Standard.
              </p>
            </div>
          </div>

          <div className="h-72 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={slaData} margin={{ top: 15, right: 15, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                <XAxis dataKey="category" stroke="#0B0B0C" fontSize={10} tickLine={false} interval={0} />
                <YAxis stroke="#0B0B0C" fontSize={12} tickLine={false} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#FFFFFF', 
                    borderColor: '#E5E7EB', 
                    borderRadius: '16px',
                    fontSize: '12px' 
                  }} 
                />
                <ReferenceLine 
                  y={48} 
                  stroke="#E03A3E" 
                  strokeWidth={2} 
                  strokeDasharray="4 4" 
                  label={{ value: '48h Target SLA', fill: '#E03A3E', fontSize: 11, position: 'top' }} 
                />
                <Bar dataKey="avgHours" name="Avg Resolution (Hours)" fill="#0B0B0C" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

