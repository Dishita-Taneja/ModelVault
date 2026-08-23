import React, { useEffect } from 'react';
import { ShieldAlert, CheckCircle2, AlertTriangle, Info, X } from 'lucide-react';

function ToastItem({ toast, onRemove }) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onRemove(toast.id);
    }, toast.duration || 5000);
    return () => clearTimeout(timer);
  }, [toast, onRemove]);

  const typeConfig = {
    error: {
      border: 'border-red-500/70 shadow-glow-red bg-charcoal/95',
      icon: <ShieldAlert className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />,
      titleColor: 'text-red-300',
      barColor: 'bg-red-500',
      tag: 'SEC_ERROR',
    },
    success: {
      border: 'border-emerald-500/70 shadow-glow-emerald bg-charcoal/95',
      icon: <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />,
      titleColor: 'text-emerald-300',
      barColor: 'bg-emerald-500',
      tag: 'SYSTEM_OK',
    },
    warning: {
      border: 'border-amber-500/70 shadow-glow-amber bg-charcoal/95',
      icon: <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />,
      titleColor: 'text-amber-300',
      barColor: 'bg-amber-500',
      tag: 'THREAT_WARN',
    },
    info: {
      border: 'border-cyan-500/70 shadow-glow-cyan bg-charcoal/95',
      icon: <Info className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />,
      titleColor: 'text-cyan-300',
      barColor: 'bg-cyan-500',
      tag: 'TELEMETRY',
    },
  }[toast.type || 'error'];

  return (
    <div
      className={`relative w-96 max-w-[calc(100vw-2rem)] border rounded-lg p-4 font-mono shadow-2xl backdrop-blur-md transition-all animate-slideDown overflow-hidden ${typeConfig.border}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          {typeConfig.icon}
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-surface border border-socBorder text-slate-400">
                {typeConfig.tag}
              </span>
              <h4 className={`text-xs font-bold ${typeConfig.titleColor}`}>
                {toast.title || 'System Notification'}
              </h4>
            </div>
            <p className="text-xs text-slate-300 mt-1 font-sans leading-relaxed">
              {toast.message}
            </p>
          </div>
        </div>
        <button
          onClick={() => onRemove(toast.id)}
          className="text-slate-400 hover:text-slate-100 p-1 rounded hover:bg-surface transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Progress countdown bar */}
      <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-slate-800">
        <div
          className={`h-full ${typeConfig.barColor} animate-progress`}
          style={{ animationDuration: `${toast.duration || 5000}ms` }}
        ></div>
      </div>
    </div>
  );
}

export default function ToastContainer({ toasts, onRemove }) {
  if (!toasts || toasts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-3 pointer-events-auto">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  );
}
