import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  X,
  ShieldAlert,
  Terminal,
  Clock,
  User,
  HardDrive,
  Network,
  Copy,
  Check,
  CheckCircle2,
  AlertTriangle,
  Radio,
  RefreshCw,
} from 'lucide-react';
import { api } from '../api/client';
import { getScoreDetails, formatBytes, formatTimestamp, formatRelativeTime } from '../utils/formatters';

export default function EvidenceDrawer({ model, onClose, onToggleReviewed }) {
  const [copiedId, setCopiedId] = useState(null);
  const [activeTab, setActiveTab] = useState('events'); // 'events' | 'raw_json'

  // On-demand evidence fetching via React Query
  const {
    data: evidenceList = [],
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['evidence', model?.model_id],
    queryFn: () => api.getModelEvidence(model.model_id),
    enabled: !!model?.model_id,
    staleTime: 60000,
  });

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!model) return null;

  const scoreInfo = getScoreDetails(model.anomaly_score);

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(typeof text === 'object' ? JSON.stringify(text, null, 2) : text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const fullPayload = {
    ...model,
    evidence: evidenceList,
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
      {/* Backdrop */}
      <div
        onClick={onClose}
        className="fixed inset-0 bg-black/80 backdrop-blur-sm transition-opacity animate-fadeIn"
      ></div>

      {/* Drawer Panel */}
      <div className="relative z-10 w-full max-w-2xl bg-charcoal border-l border-socBorder shadow-2xl h-full flex flex-col overflow-hidden text-slate-200 animate-slideLeft">
        {/* Drawer Header */}
        <div className="p-5 border-b border-socBorder bg-panel/90 flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded uppercase ${scoreInfo.badgeBg}`}>
                {scoreInfo.category} SEVERITY
              </span>
              <span className="text-xs font-mono text-slate-400">
                SCORE: <strong className="text-red-400">{(model.anomaly_score * 100).toFixed(1)}%</strong>
              </span>
            </div>
            <h2 className="text-lg font-bold font-mono text-slate-100 flex items-center gap-2">
              <Terminal className="w-5 h-5 text-red-500" />
              <span>{model.model_name}</span>
            </h2>
            <div className="text-[11px] font-mono text-slate-500 mt-0.5">
              MODEL_ID: {model.model_id}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => onToggleReviewed(model.model_id)}
              className={`px-3 py-1.5 rounded text-xs font-mono font-semibold flex items-center gap-1.5 transition-all ${
                model.reviewed
                  ? 'bg-emerald-950/70 text-emerald-400 border border-emerald-500/40 hover:bg-emerald-900/60'
                  : 'bg-red-950/70 text-red-400 border border-red-500/40 hover:bg-red-900/60'
              }`}
            >
              {model.reviewed ? <CheckCircle2 className="w-3.5 h-3.5" /> : <ShieldAlert className="w-3.5 h-3.5" />}
              <span>{model.reviewed ? 'Marked Reviewed' : 'Mark Reviewed'}</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-md text-slate-400 hover:text-slate-100 hover:bg-surface border border-transparent hover:border-socBorder transition-colors"
              title="Close drawer (Esc)"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Threat Summary Banner */}
        <div className="p-4 bg-red-950/20 border-b border-red-500/20">
          <div className="flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <div>
              <h4 className="text-xs font-mono font-bold text-red-300 uppercase tracking-wide">
                Anomaly Reason / Indicator
              </h4>
              <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                {model.reason}
              </p>
            </div>
          </div>
        </div>

        {/* Metadata Telemetry Bar */}
        <div className="grid grid-cols-3 gap-2 p-4 bg-surface/40 border-b border-socBorder text-xs font-mono">
          <div className="bg-panel p-2.5 rounded border border-socBorder">
            <span className="text-slate-500 block text-[10px] uppercase">Model Owner</span>
            <span className="text-slate-200 font-semibold truncate block">{model.owner}</span>
          </div>
          <div className="bg-panel p-2.5 rounded border border-socBorder">
            <span className="text-slate-500 block text-[10px] uppercase">Flagged Timestamp</span>
            <span className="text-slate-200 font-semibold truncate block">{formatRelativeTime(model.flagged_at)}</span>
          </div>
          <div className="bg-panel p-2.5 rounded border border-socBorder">
            <span className="text-slate-500 block text-[10px] uppercase">Evidence Events</span>
            <span className="text-cyan-400 font-semibold block">
              {isLoading ? 'Querying...' : `${evidenceList.length} Recorded`}
            </span>
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="px-5 pt-3 bg-panel border-b border-socBorder flex items-center justify-between">
          <div className="flex gap-4 text-xs font-mono">
            <button
              onClick={() => setActiveTab('events')}
              className={`pb-2.5 font-bold transition-colors border-b-2 ${
                activeTab === 'events'
                  ? 'border-cyan-400 text-cyan-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Reconciled Access Events ({isLoading ? '...' : evidenceList.length})
            </button>
            <button
              onClick={() => setActiveTab('raw_json')}
              className={`pb-2.5 font-bold transition-colors border-b-2 ${
                activeTab === 'raw_json'
                  ? 'border-cyan-400 text-cyan-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Raw JSON Payload
            </button>
          </div>

          <button
            onClick={() => copyToClipboard(fullPayload, 'full-model')}
            className="flex items-center gap-1 text-[11px] font-mono text-slate-400 hover:text-slate-200 pb-2 transition-colors"
          >
            {copiedId === 'full-model' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copiedId === 'full-model' ? 'Copied' : 'Copy All'}</span>
          </button>
        </div>

        {/* Scrollable Evidence Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 font-mono text-xs">
          {isLoading ? (
            /* Loading Shimmer State */
            <div className="space-y-4">
              {[1, 2].map((i) => (
                <div key={i} className="bg-panel border border-socBorder rounded-lg p-4 space-y-3">
                  <div className="h-4 w-40 skeleton-shimmer rounded"></div>
                  <div className="h-3 w-full skeleton-shimmer rounded"></div>
                  <div className="h-20 w-full skeleton-shimmer rounded"></div>
                </div>
              ))}
            </div>
          ) : isError ? (
            /* Error State */
            <div className="p-8 text-center bg-red-950/20 border border-red-500/30 rounded-lg">
              <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-2" />
              <h4 className="font-bold text-red-300">Failed to load evidence telemetry</h4>
              <p className="text-xs text-slate-400 mt-1">{error?.message || 'Network request failed'}</p>
              <button
                onClick={() => refetch()}
                className="mt-3 px-3 py-1.5 rounded bg-surface hover:bg-surfaceHover border border-socBorder text-xs text-slate-200 inline-flex items-center gap-1.5"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Retry Query</span>
              </button>
            </div>
          ) : activeTab === 'events' ? (
            <div className="space-y-4">
              {evidenceList.length > 0 ? (
                evidenceList.map((evt, idx) => (
                  <div
                    key={evt.event_id || idx}
                    className="bg-panel border border-socBorder rounded-lg p-4 transition-all hover:border-socBorderLight relative"
                  >
                    {/* Event Header */}
                    <div className="flex items-center justify-between border-b border-socBorder/60 pb-2 mb-3">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-500/40 text-cyan-400 font-bold text-[10px]">
                          {evt.source}
                        </span>
                        <span className="font-bold text-slate-100">{evt.event_name}</span>
                      </div>
                      <span className="text-[11px] text-slate-400">
                        {formatTimestamp(evt.event_time_reconciled)}
                      </span>
                    </div>

                    {/* Telemetry Row */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] text-slate-300 mb-3">
                      <div className="flex items-center gap-1.5">
                        <Network className="w-3.5 h-3.5 text-slate-500" />
                        <span className="text-slate-400">IP Origin:</span>
                        <span className="text-slate-100 font-semibold bg-surface px-1.5 py-0.5 rounded border border-socBorder">
                          {evt.ip_address}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-slate-500" />
                        <span className="text-slate-400">Event ID:</span>
                        <span className="text-slate-400 truncate">{evt.event_id}</span>
                      </div>
                    </div>

                    {/* Extra Telemetry JSON Metadata */}
                    {evt.extra && (
                      <div className="bg-void/90 p-3 rounded border border-socBorder/80 text-[11px]">
                        <div className="flex justify-between items-center text-slate-500 mb-2 border-b border-socBorder/40 pb-1">
                          <span className="uppercase text-[10px] font-bold tracking-wider">
                            Payload Telemetry & Flags
                          </span>
                          <button
                            onClick={() => copyToClipboard(evt.extra, evt.event_id)}
                            className="hover:text-slate-300 text-[10px] flex items-center gap-1"
                          >
                            {copiedId === evt.event_id ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                            <span>{copiedId === evt.event_id ? 'Copied' : 'Copy'}</span>
                          </button>
                        </div>
                        <pre className="text-slate-300 overflow-x-auto whitespace-pre-wrap leading-relaxed text-[11px]">
                          {JSON.stringify(evt.extra, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-slate-500">
                  No individual access events attached to this record.
                </div>
              )}
            </div>
          ) : (
            /* Full Raw JSON Tab */
            <div className="bg-void p-4 rounded-lg border border-socBorder">
              <pre className="text-cyan-300 overflow-x-auto text-[11px] leading-relaxed">
                {JSON.stringify(fullPayload, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Drawer Footer */}
        <div className="p-4 bg-panel border-t border-socBorder flex items-center justify-between text-xs font-mono">
          <div className="text-slate-400">
            INCIDENT STATUS:{' '}
            <span className={model.reviewed ? 'text-emerald-400 font-bold' : 'text-red-400 font-bold'}>
              {model.reviewed ? 'TRIAGED / ACKNOWLEDGED' : 'ACTION REQUIRED'}
            </span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded bg-surface hover:bg-surfaceHover border border-socBorder text-slate-200 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
