import React from 'react';
import { Layers, ShieldAlert, Zap, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function StatsStrip({ stats }) {
  if (!stats) return null;

  return (
    <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
      {/* 1. Total Models Monitored */}
      <div className="bg-panel/90 border border-socBorder rounded-lg p-5 relative overflow-hidden transition-all hover:border-socBorderLight group">
        <div className="absolute top-0 right-0 w-24 h-24 bg-cyan-500/5 rounded-full blur-xl pointer-events-none group-hover:bg-cyan-500/10 transition-all"></div>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 text-slate-400 text-xs font-mono tracking-wider uppercase mb-1">
              <span>Total Models Monitored</span>
            </div>
            <div className="text-3xl font-bold font-mono text-slate-100 tracking-tight">
              {stats.total_models}
            </div>
            <div className="flex items-center gap-1.5 mt-2.5 text-xs text-slate-400">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>100% telemetry coverage</span>
            </div>
          </div>
          <div className="p-3 rounded-lg bg-surface border border-socBorder text-cyberCyan group-hover:border-cyan-500/40 transition-colors">
            <Layers className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* 2. Flagged Models */}
      <div className="bg-panel/90 border border-socBorder rounded-lg p-5 relative overflow-hidden transition-all hover:border-red-500/40 group">
        <div className="absolute top-0 right-0 w-24 h-24 bg-red-500/5 rounded-full blur-xl pointer-events-none group-hover:bg-red-500/15 transition-all"></div>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 text-red-400 text-xs font-mono tracking-wider uppercase mb-1">
              <span>Flagged Models</span>
            </div>
            <div className="text-3xl font-bold font-mono text-red-400 tracking-tight flex items-baseline gap-2">
              {stats.flagged_count}
              <span className="text-xs font-normal text-slate-400 font-sans">
                ({Math.round((stats.flagged_count / stats.total_models) * 100)}% of fleet)
              </span>
            </div>
            <div className="flex items-center gap-1.5 mt-2.5 text-xs text-red-400/90 font-mono">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Breach threshold triggers</span>
            </div>
          </div>
          <div className="p-3 rounded-lg bg-red-950/40 border border-red-500/40 text-red-400 group-hover:shadow-glow-red transition-all">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* 3. Active Anomalies */}
      <div className="bg-panel/90 border border-socBorder rounded-lg p-5 relative overflow-hidden transition-all hover:border-amber-500/40 sm:col-span-2 lg:col-span-1 group">
        <div className="absolute top-0 right-0 w-24 h-24 bg-amber-500/5 rounded-full blur-xl pointer-events-none group-hover:bg-amber-500/15 transition-all"></div>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 text-amber-400 text-xs font-mono tracking-wider uppercase mb-1">
              <span>Active Anomalies</span>
            </div>
            <div className="text-3xl font-bold font-mono text-amber-400 tracking-tight">
              {stats.active_anomalies}
            </div>
            <div className="flex items-center gap-1.5 mt-2.5 text-xs text-amber-400/90 font-mono">
              <Zap className="w-3.5 h-3.5 animate-pulse" />
              <span>Pending SOC triage</span>
            </div>
          </div>
          <div className="p-3 rounded-lg bg-amber-950/40 border border-amber-500/40 text-amber-400 group-hover:shadow-glow-amber transition-all">
            <Zap className="w-5 h-5" />
          </div>
        </div>
      </div>
    </section>
  );
}
