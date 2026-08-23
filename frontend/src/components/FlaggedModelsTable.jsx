import React from 'react';
import { ShieldAlert, CheckCircle2, AlertCircle, ChevronRight, User, Terminal, ExternalLink } from 'lucide-react';
import { getScoreDetails, formatRelativeTime, formatTimestamp } from '../utils/formatters';

export default function FlaggedModelsTable({
  models,
  onSelectModel,
  onToggleReviewed,
  selectedModelId,
}) {
  if (!models || models.length === 0) {
    return (
      <div className="bg-panel border border-socBorder rounded-lg p-12 text-center">
        <AlertCircle className="w-8 h-8 text-slate-500 mx-auto mb-3" />
        <h3 className="text-sm font-mono font-bold text-slate-300 uppercase">
          No Security Incidents Matched
        </h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
          Try adjusting your search keywords, owner filter, or time range selection.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-panel border border-socBorder rounded-lg overflow-hidden shadow-card-subtle">
      {/* Table header bar */}
      <div className="px-5 py-3.5 border-b border-socBorder bg-surface/80 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-cyberCyan" />
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-200">
            Tracked ML Model Access Audit Log ({models.length})
          </h3>
        </div>
        <span className="text-[11px] font-mono text-slate-400">
          Click any row to inspect forensic evidence
        </span>
      </div>

      {/* Responsive Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-socBorder bg-void/50 text-[11px] font-mono uppercase tracking-wider text-slate-400">
              <th className="py-3 px-4 font-semibold">Model Identifier</th>
              <th className="py-3 px-4 font-semibold">Owner / Identity</th>
              <th className="py-3 px-4 font-semibold">Anomaly Score</th>
              <th className="py-3 px-4 font-semibold hidden md:table-cell">Primary Reason</th>
              <th className="py-3 px-4 font-semibold">Last Flagged</th>
              <th className="py-3 px-4 font-semibold text-center">Triage Status</th>
              <th className="py-3 px-4 font-semibold text-right">Forensics</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-socBorder/60 text-xs font-mono">
            {models.map((item) => {
              const scoreInfo = getScoreDetails(item.anomaly_score);
              const isSelected = selectedModelId === item.model_id;

              return (
                <tr
                  key={item.model_id}
                  onClick={() => onSelectModel(item)}
                  className={`cursor-pointer transition-colors group ${
                    isSelected
                      ? 'bg-surfaceHover border-l-2 border-l-cyan-400'
                      : 'hover:bg-surface/70 hover:border-l-2 hover:border-l-red-500/80'
                  }`}
                >
                  {/* 1. Model Name */}
                  <td className="py-3.5 px-4 font-mono">
                    <div className="font-semibold text-slate-100 group-hover:text-cyan-300 transition-colors flex items-center gap-2">
                      <span>{item.model_name}</span>
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono truncate max-w-[200px]">
                      {item.model_id}
                    </div>
                  </td>

                  {/* 2. Owner */}
                  <td className="py-3.5 px-4 text-slate-300">
                    <div className="flex items-center gap-1.5">
                      <User className="w-3.5 h-3.5 text-slate-500" />
                      <span>{item.owner}</span>
                    </div>
                  </td>

                  {/* 3. Anomaly Score with Visual Tag */}
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-2.5">
                      <span
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded border text-[11px] font-bold ${scoreInfo.badgeBg}`}
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                        {item.anomaly_score.toFixed(2)}
                      </span>
                      {/* Mini bar gauge */}
                      <div className="w-12 bg-slate-800 rounded-full h-1.5 overflow-hidden hidden sm:block">
                        <div
                          className={`h-full ${scoreInfo.barColor}`}
                          style={{ width: `${Math.min(item.anomaly_score * 100, 100)}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>

                  {/* 4. Primary Reason */}
                  <td className="py-3.5 px-4 text-slate-400 font-sans text-xs max-w-xs truncate hidden md:table-cell" title={item.reason}>
                    {item.reason}
                  </td>

                  {/* 5. Last Flagged Time */}
                  <td className="py-3.5 px-4 text-slate-300 whitespace-nowrap" title={formatTimestamp(item.flagged_at)}>
                    <div className="text-slate-200">{formatRelativeTime(item.flagged_at)}</div>
                    <div className="text-[10px] text-slate-500">{new Date(item.flagged_at).toISOString().substring(11, 19)} UTC</div>
                  </td>

                  {/* 6. Reviewed Status Toggle */}
                  <td className="py-3.5 px-4 text-center" onClick={(e) => e.stopPropagation()}>
                    <button
                      type="button"
                      onClick={() => onToggleReviewed(item.model_id)}
                      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-mono font-medium transition-all ${
                        item.reviewed
                          ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-500/40 hover:bg-emerald-900/60'
                          : 'bg-red-950/60 text-red-400 border border-red-500/40 hover:bg-red-900/60 animate-pulse-slow'
                      }`}
                      title="Click to toggle triage status"
                    >
                      {item.reviewed ? (
                        <>
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Reviewed</span>
                        </>
                      ) : (
                        <>
                          <ShieldAlert className="w-3 h-3 text-red-400" />
                          <span>Unreviewed</span>
                        </>
                      )}
                    </button>
                  </td>

                  {/* 7. Action / Forensics button */}
                  <td className="py-3.5 px-4 text-right">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectModel(item);
                      }}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-surface hover:bg-surfaceHover border border-socBorder text-slate-300 hover:text-cyan-300 text-xs transition-all"
                    >
                      <span>Evidence</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
