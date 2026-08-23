/**
 * Utility functions for formatting cybersecurity SOC metrics, timestamps, and scores.
 */

export function getScoreDetails(score) {
  if (score >= 0.7) {
    return {
      category: 'CRITICAL',
      colorClass: 'text-red-400 bg-red-950/50 border-red-500/40',
      badgeBg: 'bg-red-500/10 text-red-400 border-red-500/30',
      barColor: 'bg-gradient-to-r from-red-500 to-rose-600',
      glowClass: 'shadow-glow-red border-red-500/50',
      textAccent: 'text-red-400',
      label: 'High Severity',
    };
  }
  if (score >= 0.3) {
    return {
      category: 'ELEVATED',
      colorClass: 'text-amber-400 bg-amber-950/50 border-amber-500/40',
      badgeBg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
      barColor: 'bg-gradient-to-r from-amber-400 to-orange-500',
      glowClass: 'shadow-glow-amber border-amber-500/50',
      textAccent: 'text-amber-400',
      label: 'Medium Severity',
    };
  }
  return {
    category: 'LOW',
    colorClass: 'text-emerald-400 bg-emerald-950/50 border-emerald-500/40',
    badgeBg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    barColor: 'bg-gradient-to-r from-emerald-400 to-teal-500',
    glowClass: 'border-emerald-500/30',
    textAccent: 'text-emerald-400',
    label: 'Low / Normal',
  };
}

export function formatBytes(bytes, decimals = 2) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

export function formatTimestamp(isoString) {
  if (!isoString) return '--';
  try {
    const d = new Date(isoString);
    return d.toISOString().replace('T', ' ').replace('Z', ' UTC');
  } catch {
    return isoString;
  }
}

export function formatRelativeTime(isoString) {
  if (!isoString) return '--';
  try {
    const d = new Date(isoString);
    const now = new Date();
    const diffSec = Math.floor((now - d) / 1000);

    if (diffSec < 60) return `${diffSec}s ago`;
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
    return `${Math.floor(diffSec / 86400)}d ago`;
  } catch {
    return isoString;
  }
}
