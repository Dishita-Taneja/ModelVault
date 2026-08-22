import React, { useState } from 'react';
import { Flame, ChevronRight, Eye, ShieldAlert, Clock, User, HardDrive, Terminal } from 'lucide-react';
import { getScoreDetails, formatRelativeTime, formatBytes } from '../utils/formatters';

export default function TopSuspiciousPanel({ topSuspicious, onSelectModel }) {
  const [expandedCard, setExpandedCard] = useState(null);

  if (!topSuspicious || topSuspicious.length === 0) return null;

  const toggleExpand = (modelId, e) => {
    e.stopPropagation();
    setExpandedCard(expandedCard === modelId ? null : modelId);
  };

  return (
    <section className="mb-10">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="flex items-center justify-center w-6 h-6 rounded bg-red-950/80 border border-red-500/50 text-red-400">
            <Flame className="w-3.5 h-3.5 animate-pulse" />
          </div>
          <h2 className="text-sm font-mono font-bold tracking-wider uppercase text-slate-100">
            Top 3 High-Threat Suspicious Incidents
          </h2>
        </div>
        <span className="text-xs font-mono text-red-400/80 uppercase tracking-widest hidden sm:inline">
          PRIORITY 1 ESCALATIONS
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {topSuspicious.map((item, index) => {
          const scoreInfo = getScoreDetails(item.anomaly_score);
          const isExpanded = expandedCard === item.model_id;
          const primaryEvidence = item.evidence?.[0];

          return (
            <div
              key={item.model_id}
              onClick={() => onSelectModel(item)}
              className="bg-panel border border-red-500/30 hover:border-red-500/70 rounded-lg p-5 shadow-card-subtle hover:shadow-glow-red transition-all cursor-pointer flex flex-col justify-between group relative overflow-hidden"
            >
              {/* Subtle top red glow bar */}
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-red-500/20 via-red-500 to-red-500/20"></div>

              <div>
                {/* Header: Rank + Model Name + Severity Badge */}
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex items-center gap-2">
                    <span className="flex items-center justify-center w-5 h-5 rounded bg-red-500/20 border border-red-500/40 text-[11px] font-mono font-bold text-red-400">
                      #{index + 1}
                    </span>
                    <h3 className="font-mono text-sm font-semibold text-slate-100 truncate group-hover:text-red-300 transition-colors" title={item.model_name}>
                      {item.model_name}
                    </h3>
                  </div>
                  <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded uppercase tracking-wider ${scoreInfo.badgeBg} shrink-0`}>
                    {scoreInfo.category}
                  </span>
                </div>

                {/* Threat Gauge & Anomaly Score Bar */}
                <div className="mb-4 bg-void/80 p-3 rounded-md border border-socBorder">
                  <div className="flex justify-between items-center text-xs font-mono mb-1.5">
                    <span className="text-slate-400 flex items-center gap-1">
                      <ShieldAlert className="w-3.5 h-3.5 text-red-400" />
                      ANOMALY_SCORE
                    </span>
                    <span className="text-red-400 font-bold text-sm">
                      {(item.anomaly_score * 100).toFixed(1)}%
                      <span className="text-slate-500 text-xs ml-1">({item.anomaly_score.toFixed(2)})</span>
                    </span>
                  </div>
                  {/* Gauge Bar */}
                  <div className="w-full bg-slate-800/80 rounded-full h-2 overflow-hidden p-[1px]">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${scoreInfo.barColor}`}
                      style={{ width: `${Math.min(item.anomaly_score * 100, 100)}%` }}
                    ></div>
                  </div>
                </div>

                {/* Reason */}
                <p className="text-xs text-slate-300 leading-relaxed mb-4 line-clamp-2">
                  {item.reason}
                </p>

                {/* Metadata tags */}
                <div className="grid grid-cols-2 gap-2 text-[11px] font-mono text-slate-400 mb-4 bg-surface/50 p-2.5 rounded border border-socBorder/60">
                  <div className="flex items-center gap-1.5 truncate">
                    <User className="w-3 h-3 text-slate-500 shrink-0" />
                    <span className="truncate">{item.owner}</span>
                  </div>
                  <div className="flex items-center gap-1.5 justify-end">
                    <Clock className="w-3 h-3 text-slate-500 shrink-0" />
                    <span>{formatRelativeTime(item.flagged_at)}</span>
                  </div>
                </div>
              </div>

              {/* Expandable Evidence Snippet */}
              <div>
                <div className="flex items-center justify-between pt-2 border-t border-socBorder/80">
                  <button
                    type="button"
                    onClick={(e) => toggleExpand(item.model_id, e)}
                    className="text-xs font-mono text-slate-400 hover:text-slate-200 flex items-center gap-1 transition-colors"
                  >
                    <span>{isExpanded ? 'Hide' : 'Quick Evidence'}</span>
                    <ChevronRight className={`w-3.5 h-3.5 transition-transform ${isExpanded ? 'rotate-90 text-red-400' : ''}`} />
                  </button>

                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectModel(item);
                    }}
                    className="px-2.5 py-1 rounded bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 hover:text-red-300 text-xs font-mono flex items-center gap-1.5 transition-all"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>View Evidence</span>
                  </button>
                </div>

                {/* Inline Expanded Log Card */}
                {isExpanded && primaryEvidence && (
                  <div className="mt-3 p-3 bg-void border border-socBorder rounded font-mono text-[11px] space-y-1.5 text-slate-300 animate-fadeIn">
                    <div className="text-red-400 font-bold flex items-center gap-1">
                      <Terminal className="w-3 h-3" />
                      <span>{primaryEvidence.source} // {primaryEvidence.event_name}</span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>IP: <span className="text-slate-200">{primaryEvidence.ip_address}</span></span>
                      <span>{formatRelativeTime(primaryEvidence.event_time_reconciled)}</span>
                    </div>
                    {primaryEvidence.extra?.bytes_transferred && (
                      <div className="text-amber-400/90 flex items-center gap-1">
                        <HardDrive className="w-3 h-3" />
                        <span>Transferred: {formatBytes(primaryEvidence.extra.bytes_transferred)}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
