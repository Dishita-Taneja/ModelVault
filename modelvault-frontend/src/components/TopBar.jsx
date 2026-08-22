import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, RefreshCw, Radio, UserPlus, Server } from 'lucide-react';

export default function TopBar({ onRefresh, isRefreshing }) {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatUtcTime = (date) => {
    return date.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
  };

  return (
    <header className="sticky top-0 z-30 bg-charcoal/95 backdrop-blur-md border-b border-socBorder px-4 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
      {/* Brand & Wordmark */}
      <div className="flex items-center gap-3">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="relative flex items-center justify-center w-9 h-9 rounded-md bg-red-950/70 border border-red-500/50 shadow-glow-red group-hover:border-red-400 transition-colors">
            <ShieldAlert className="w-5 h-5 text-red-400" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-red-500 animate-ping"></span>
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-red-500"></span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-wider text-slate-100 uppercase font-mono flex items-center gap-1.5 group-hover:text-red-300 transition-colors">
                MODEL<span className="text-red-500">VAULT</span>
              </h1>
              <span className="text-[10px] font-mono tracking-widest px-1.5 py-0.5 rounded bg-surface border border-socBorder text-slate-400">
                SOC THREAT INTEL v2.4
              </span>
            </div>
            <p className="text-xs text-slate-400 tracking-tight hidden sm:block">
              Autonomous ML Model Access Anomaly Detection & Incident Response
            </p>
          </div>
        </Link>
      </div>

      {/* Right controls: Live Threat Dot, UTC Clock, Sign Up, Refresh */}
      <div className="flex items-center gap-3 sm:gap-4">
        {/* Live Status Indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-surface border border-socBorder text-xs font-mono">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-emerald-400 font-semibold uppercase tracking-wider text-[11px]">
            TELEMETRY ONLINE
          </span>
          <span className="text-slate-500">|</span>
          <span className="text-slate-400 text-[11px] hidden md:inline">
            CLUSTER SOC-18
          </span>
        </div>

        {/* Real-time UTC Clock */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-md bg-panel border border-socBorder text-slate-300 font-mono text-xs">
          <Radio className="w-3.5 h-3.5 text-cyberCyan animate-pulse-slow" />
          <span className="text-slate-400">SYS_TIME:</span>
          <span className="text-slate-100 font-medium">{formatUtcTime(currentTime)}</span>
        </div>

        {/* Sign Up / Enroll Link */}
        <Link
          to="/signup"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-red-950/40 hover:bg-red-900/50 border border-red-500/30 hover:border-red-500/60 text-red-300 hover:text-red-200 text-xs font-mono transition-all"
        >
          <UserPlus className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Enroll Operator</span>
        </Link>

        {/* Refresh Action */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-surface hover:bg-surfaceHover border border-socBorder active:scale-95 transition-all text-xs font-mono text-slate-300 hover:text-slate-100"
          title="Refresh Threat Telemetry"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-cyberCyan' : 'text-slate-400'}`} />
          <span className="hidden sm:inline">SYNC</span>
        </button>
      </div>
    </header>
  );
}
