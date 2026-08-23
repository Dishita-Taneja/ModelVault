import React from 'react';
import { Filter, User, Cpu, Calendar, RotateCcw, Search, CheckCircle2 } from 'lucide-react';

export default function FilterBar({
  users,
  models,
  selectedUser,
  setSelectedUser,
  selectedModel,
  setSelectedModel,
  timeRange,
  setTimeRange,
  customStartDate,
  setCustomStartDate,
  customEndDate,
  setCustomEndDate,
  searchQuery,
  setSearchQuery,
  reviewedFilter,
  setReviewedFilter,
  onResetFilters,
  totalResults,
}) {
  const hasActiveFilters =
    selectedUser !== 'ALL' ||
    selectedModel !== 'ALL' ||
    timeRange !== 'ALL' ||
    searchQuery !== '' ||
    reviewedFilter !== 'ALL' ||
    customStartDate !== '' ||
    customEndDate !== '';

  return (
    <div className="bg-panel border border-socBorder rounded-lg p-4 mb-4">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Search bar & quick filters */}
        <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          {/* 1. Search Query */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search model / reason..."
              className="w-full pl-9 pr-3 py-1.5 bg-surface border border-socBorder rounded text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/30 transition-all"
            />
          </div>

          {/* 2. User Filter */}
          <div className="relative">
            <User className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <select
              value={selectedUser}
              onChange={(e) => setSelectedUser(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-surface border border-socBorder rounded text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/30 transition-all appearance-none cursor-pointer"
            >
              <option value="ALL">All Owners / Users</option>
              {users.map((user) => (
                <option key={user} value={user}>
                  {user}
                </option>
              ))}
            </select>
          </div>

          {/* 3. Model Filter */}
          <div className="relative">
            <Cpu className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-surface border border-socBorder rounded text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/30 transition-all appearance-none cursor-pointer"
            >
              <option value="ALL">All ML Models</option>
              {models.map((mod) => (
                <option key={mod} value={mod}>
                  {mod}
                </option>
              ))}
            </select>
          </div>

          {/* 4. Time Range Filter */}
          <div className="relative">
            <Calendar className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-surface border border-socBorder rounded text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/30 transition-all appearance-none cursor-pointer"
            >
              <option value="ALL">Time: All Recorded</option>
              <option value="24H">Last 24 Hours</option>
              <option value="7D">Last 7 Days</option>
              <option value="30D">Last 30 Days</option>
              <option value="CUSTOM">Custom Date Range</option>
            </select>
          </div>
        </div>

        {/* Reviewed Status Tabs & Reset */}
        <div className="flex items-center gap-3 self-end lg:self-center">
          {/* Reviewed Filter buttons */}
          <div className="flex items-center bg-surface border border-socBorder rounded p-0.5 text-xs font-mono">
            <button
              onClick={() => setReviewedFilter('ALL')}
              className={`px-2.5 py-1 rounded transition-all ${
                reviewedFilter === 'ALL'
                  ? 'bg-panel text-slate-100 font-bold border border-socBorder'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setReviewedFilter('UNREVIEWED')}
              className={`px-2.5 py-1 rounded transition-all ${
                reviewedFilter === 'UNREVIEWED'
                  ? 'bg-red-950/60 text-red-400 font-bold border border-red-500/40'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Active
            </button>
            <button
              onClick={() => setReviewedFilter('REVIEWED')}
              className={`px-2.5 py-1 rounded transition-all ${
                reviewedFilter === 'REVIEWED'
                  ? 'bg-emerald-950/60 text-emerald-400 font-bold border border-emerald-500/40'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Reviewed
            </button>
          </div>

          {/* Reset button */}
          {hasActiveFilters && (
            <button
              onClick={onResetFilters}
              className="flex items-center gap-1 px-2.5 py-1 text-xs font-mono text-slate-400 hover:text-red-400 bg-surface hover:bg-surfaceHover border border-socBorder rounded transition-all"
              title="Reset all filters"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>

      {/* Custom Date Range Picker inputs when CUSTOM is selected */}
      {timeRange === 'CUSTOM' && (
        <div className="mt-3 pt-3 border-t border-socBorder/80 flex flex-wrap items-center gap-3 text-xs font-mono">
          <span className="text-slate-400">Date Range:</span>
          <input
            type="date"
            value={customStartDate}
            onChange={(e) => setCustomStartDate(e.target.value)}
            className="bg-surface border border-socBorder rounded px-2.5 py-1 text-slate-200 focus:outline-none focus:border-cyan-500/60"
          />
          <span className="text-slate-500">to</span>
          <input
            type="date"
            value={customEndDate}
            onChange={(e) => setCustomEndDate(e.target.value)}
            className="bg-surface border border-socBorder rounded px-2.5 py-1 text-slate-200 focus:outline-none focus:border-cyan-500/60"
          />
        </div>
      )}
    </div>
  );
}
