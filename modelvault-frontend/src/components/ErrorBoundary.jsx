import React from 'react';
import { ShieldAlert, RefreshCw, AlertTriangle, Terminal } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an unhandled exception:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-void flex items-center justify-center p-6 text-slate-200 font-mono">
          <div className="max-w-xl w-full bg-charcoal border border-red-500/60 shadow-glow-red rounded-lg p-8 relative overflow-hidden">
            {/* Top red danger strip */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-red-500"></div>

            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 bg-red-950/80 border border-red-500/40 rounded-lg text-red-400">
                <ShieldAlert className="w-8 h-8" />
              </div>
              <div>
                <span className="text-[11px] px-2 py-0.5 rounded bg-red-500/10 border border-red-500/30 text-red-400 font-bold uppercase">
                  CRITICAL_SYSTEM_FAULT
                </span>
                <h1 className="text-xl font-bold text-slate-100 mt-1">
                  Security Console Interrupted
                </h1>
              </div>
            </div>

            <p className="text-xs text-slate-300 font-sans leading-relaxed mb-6">
              A runtime exception interrupted the ModelVault SOC Telemetry pipeline. The incident has been logged for forensic evaluation.
            </p>

            {/* Error detail box */}
            <div className="bg-void p-4 rounded border border-socBorder text-xs mb-6 overflow-x-auto text-red-300">
              <div className="text-slate-500 text-[10px] mb-1 flex items-center gap-1">
                <Terminal className="w-3 h-3" />
                <span>EXCEPTION_TRACE</span>
              </div>
              <p className="font-mono">{this.state.error?.toString() || 'Unknown Runtime Error'}</p>
            </div>

            <div className="flex items-center justify-between gap-4">
              <span className="text-[11px] text-slate-500">
                MODELVAULT RECOVERY AGENT // v2.4
              </span>
              <button
                onClick={this.handleReset}
                className="px-4 py-2 rounded bg-red-500/20 hover:bg-red-500/30 border border-red-500/50 text-red-300 hover:text-red-200 text-xs font-bold flex items-center gap-2 transition-all active:scale-95"
              >
                <RefreshCw className="w-4 h-4" />
                <span>REINITIALIZE DASHBOARD</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
