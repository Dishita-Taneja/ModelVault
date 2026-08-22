import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import TopBar from '../components/TopBar';
import StatsStrip from '../components/StatsStrip';
import TopSuspiciousPanel from '../components/TopSuspiciousPanel';
import FilterBar from '../components/FilterBar';
import FlaggedModelsTable from '../components/FlaggedModelsTable';
import EvidenceDrawer from '../components/EvidenceDrawer';
import { StatsSkeleton, TopSuspiciousSkeleton, TableSkeleton } from '../components/Skeletons';
import { api } from '../api/client';
import { useDebounce } from '../hooks/useDebounce';
import { useToast } from '../context/ToastContext';
import { AlertCircle, RefreshCw } from 'lucide-react';

export default function Dashboard() {
  const queryClient = useQueryClient();
  const { addToast } = useToast();

  const [selectedModelForDrawer, setSelectedModelForDrawer] = useState(null);

  // Raw Filter States
  const [selectedUser, setSelectedUser] = useState('ALL');
  const [selectedModel, setSelectedModel] = useState('ALL');
  const [timeRange, setTimeRange] = useState('ALL');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [reviewedFilter, setReviewedFilter] = useState('ALL');

  // Debounced filters (300ms) per requirement #3
  const debouncedSearch = useDebounce(searchQuery, 300);
  const debouncedStartDate = useDebounce(customStartDate, 300);
  const debouncedEndDate = useDebounce(customEndDate, 300);

  // 1. Fetch Users for Filter Dropdown
  const { data: usersList = [] } = useQuery({
    queryKey: ['users'],
    queryFn: api.getUsers,
    staleTime: 5 * 60 * 1000,
  });

  const uniqueUsers = useMemo(() => {
    return usersList.map((u) => u.username || u.name || u).filter(Boolean);
  }, [usersList]);

  // 2. Fetch Models for Filter Dropdown
  const { data: modelsList = [] } = useQuery({
    queryKey: ['models'],
    queryFn: api.getModels,
    staleTime: 5 * 60 * 1000,
  });

  const uniqueModels = useMemo(() => {
    return modelsList.map((m) => m.name || m.model_name || m).filter(Boolean);
  }, [modelsList]);

  // 3. Fetch Telemetry Stats
  const {
    data: stats,
    isLoading: isStatsLoading,
    isRefetching: isStatsRefetching,
    error: statsError,
  } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: api.getStats,
    staleTime: 30 * 1000,
  });

  // 4. Fetch Top 3 Suspicious Incidents
  const {
    data: topSuspicious = [],
    isLoading: isTopLoading,
    isRefetching: isTopRefetching,
    error: topError,
  } = useQuery({
    queryKey: ['dashboard', 'top-suspicious'],
    queryFn: api.getTopSuspicious,
    staleTime: 30 * 1000,
  });

  // 5. Fetch Flagged Models with dynamic queryKey for auto-refetching
  const flaggedModelsQueryKey = useMemo(() => [
    'dashboard',
    'flagged-models',
    {
      user: selectedUser,
      model: selectedModel,
      reviewed: reviewedFilter,
      timeRange,
      search: debouncedSearch,
      startDate: debouncedStartDate,
      endDate: debouncedEndDate,
    },
  ], [
    selectedUser,
    selectedModel,
    reviewedFilter,
    timeRange,
    debouncedSearch,
    debouncedStartDate,
    debouncedEndDate,
  ]);

  const {
    data: rawFlaggedModels = [],
    isLoading: isFlaggedLoading,
    isRefetching: isFlaggedRefetching,
    isError: isFlaggedError,
    error: flaggedError,
    refetch: refetchFlagged,
  } = useQuery({
    queryKey: flaggedModelsQueryKey,
    queryFn: () =>
      api.getFlaggedModels({
        user_id: selectedUser !== 'ALL' ? selectedUser : undefined,
        model_id: selectedModel !== 'ALL' ? selectedModel : undefined,
        reviewed: reviewedFilter,
        search: debouncedSearch || undefined,
        start_time: timeRange === 'CUSTOM' ? debouncedStartDate : undefined,
        end_time: timeRange === 'CUSTOM' ? debouncedEndDate : undefined,
      }),
    staleTime: 30 * 1000,
  });

  // Client-side supplementary filter for instantaneous text response and local fields
  const filteredModels = useMemo(() => {
    return rawFlaggedModels.filter((item) => {
      // 1. Search Query filter (name, reason, id)
      if (debouncedSearch.trim() !== '') {
        const query = debouncedSearch.toLowerCase();
        const matchesName = item.model_name?.toLowerCase().includes(query);
        const matchesReason = item.reason?.toLowerCase().includes(query);
        const matchesOwner = item.owner?.toLowerCase().includes(query);
        const matchesId = item.model_id?.toLowerCase().includes(query);
        if (!matchesName && !matchesReason && !matchesOwner && !matchesId) return false;
      }

      // 2. User Filter
      if (selectedUser !== 'ALL' && item.owner !== selectedUser) {
        return false;
      }

      // 3. Model Filter
      if (selectedModel !== 'ALL' && item.model_name !== selectedModel) {
        return false;
      }

      // 4. Reviewed Filter
      if (reviewedFilter === 'REVIEWED' && !item.reviewed) return false;
      if (reviewedFilter === 'UNREVIEWED' && item.reviewed) return false;

      // 5. Time Range Filter (24H, 7D, 30D)
      if (timeRange !== 'ALL' && item.flagged_at) {
        const itemTime = new Date(item.flagged_at).getTime();
        const now = Date.now();

        if (timeRange === '24H' && now - itemTime > 24 * 60 * 60 * 1000) return false;
        if (timeRange === '7D' && now - itemTime > 7 * 24 * 60 * 60 * 1000) return false;
        if (timeRange === '30D' && now - itemTime > 30 * 24 * 60 * 60 * 1000) return false;
        if (timeRange === 'CUSTOM') {
          if (debouncedStartDate && itemTime < new Date(debouncedStartDate).getTime()) return false;
          if (debouncedEndDate && itemTime > new Date(debouncedEndDate).getTime() + 86400000) return false;
        }
      }

      return true;
    });
  }, [
    rawFlaggedModels,
    debouncedSearch,
    selectedUser,
    selectedModel,
    reviewedFilter,
    timeRange,
    debouncedStartDate,
    debouncedEndDate,
  ]);

  // 6. Optimistic Reviewed Status Mutation (Requirement #5)
  const reviewMutation = useMutation({
    mutationFn: ({ modelId, newReviewed }) => api.reviewFlaggedModel(modelId, newReviewed),
    onMutate: async ({ modelId, newReviewed }) => {
      // Cancel outgoing refetches so they don't overwrite our optimistic update
      await queryClient.cancelQueries({ queryKey: ['dashboard'] });

      // Snapshot previous values
      const previousFlagged = queryClient.getQueryData(flaggedModelsQueryKey);
      const previousTop = queryClient.getQueryData(['dashboard', 'top-suspicious']);
      const previousStats = queryClient.getQueryData(['dashboard', 'stats']);

      // Optimistically update Flagged Models list
      queryClient.setQueryData(flaggedModelsQueryKey, (old) => {
        if (!old) return [];
        return old.map((m) => (m.model_id === modelId ? { ...m, reviewed: newReviewed } : m));
      });

      // Optimistically update Top 3 Suspicious
      queryClient.setQueryData(['dashboard', 'top-suspicious'], (old) => {
        if (!old) return [];
        return old.map((m) => (m.model_id === modelId ? { ...m, reviewed: newReviewed } : m));
      });

      // Update selected drawer model if active
      setSelectedModelForDrawer((prev) =>
        prev && prev.model_id === modelId ? { ...prev, reviewed: newReviewed } : prev
      );

      return { previousFlagged, previousTop, previousStats };
    },
    onError: (err, variables, context) => {
      // Rollback to previous state on failure
      if (context?.previousFlagged) {
        queryClient.setQueryData(flaggedModelsQueryKey, context.previousFlagged);
      }
      if (context?.previousTop) {
        queryClient.setQueryData(['dashboard', 'top-suspicious'], context.previousTop);
      }
      if (context?.previousStats) {
        queryClient.setQueryData(['dashboard', 'stats'], context.previousStats);
      }

      setSelectedModelForDrawer((prev) =>
        prev && prev.model_id === variables.modelId ? { ...prev, reviewed: !variables.newReviewed } : prev
      );

      // Show visible error toast per requirement #5
      addToast({
        title: 'Triage Update Failed',
        message: `Could not sync triage status for model ${variables.modelId}. Reverting changes. (${err.message})`,
        type: 'error',
      });
    },
    onSuccess: (data, variables) => {
      addToast({
        title: variables.newReviewed ? 'Incident Marked Reviewed' : 'Incident Re-Opened',
        message: `Triage record for model ${variables.modelId} updated in immutable audit log.`,
        type: 'success',
      });
      // Invalidate queries to sync authoritative server state
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });

  const handleToggleReviewed = (modelId) => {
    // Find current review state
    const target = rawFlaggedModels.find((m) => m.model_id === modelId) ||
      topSuspicious.find((m) => m.model_id === modelId) ||
      selectedModelForDrawer;
    const currentReviewed = target?.reviewed || false;
    reviewMutation.mutate({ modelId, newReviewed: !currentReviewed });
  };

  // Trigger manual refresh for all dashboard queries
  const isRefreshing = isStatsRefetching || isTopRefetching || isFlaggedRefetching;
  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    addToast({
      title: 'Telemetry Synced',
      message: 'Refreshed active threat vectors and SOC metrics.',
      type: 'info',
      duration: 2500,
    });
  };

  const handleResetFilters = () => {
    setSelectedUser('ALL');
    setSelectedModel('ALL');
    setTimeRange('ALL');
    setCustomStartDate('');
    setCustomEndDate('');
    setSearchQuery('');
    setReviewedFilter('ALL');
  };

  return (
    <div className="min-h-screen bg-void flex flex-col font-sans">
      {/* Top Bar */}
      <TopBar onRefresh={handleRefresh} isRefreshing={isRefreshing} />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Section 1: Stats Strip */}
        {isStatsLoading ? (
          <StatsSkeleton />
        ) : (
          <StatsStrip stats={stats} />
        )}

        {/* Section 2: Top 3 Suspicious Events Panel */}
        {isTopLoading ? (
          <TopSuspiciousSkeleton />
        ) : (
          <TopSuspiciousPanel
            topSuspicious={topSuspicious}
            onSelectModel={setSelectedModelForDrawer}
          />
        )}

        {/* Section 3: Filter Bar & Main Flagged Models Table */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-mono font-bold uppercase tracking-wider text-slate-100 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
              <span>All Flagged Model Incidents</span>
            </h2>
            <span className="text-xs font-mono text-slate-400">
              Showing {filteredModels.length} of {rawFlaggedModels.length} models
            </span>
          </div>

          <FilterBar
            users={uniqueUsers}
            models={uniqueModels}
            selectedUser={selectedUser}
            setSelectedUser={setSelectedUser}
            selectedModel={selectedModel}
            setSelectedModel={setSelectedModel}
            timeRange={timeRange}
            setTimeRange={setTimeRange}
            customStartDate={customStartDate}
            setCustomStartDate={setCustomStartDate}
            customEndDate={customEndDate}
            setCustomEndDate={setCustomEndDate}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            reviewedFilter={reviewedFilter}
            setReviewedFilter={setReviewedFilter}
            onResetFilters={handleResetFilters}
            totalResults={filteredModels.length}
          />

          {isFlaggedLoading ? (
            <TableSkeleton />
          ) : isFlaggedError ? (
            <div className="bg-panel border border-red-500/40 rounded-lg p-10 text-center">
              <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
              <h3 className="text-sm font-mono font-bold text-red-300">
                Failed to Retrieve Threat Audit Stream
              </h3>
              <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                {flaggedError?.message || 'The server returned an error while fetching flagged models.'}
              </p>
              <button
                onClick={() => refetchFlagged()}
                className="mt-4 px-3.5 py-1.5 rounded bg-surface hover:bg-surfaceHover border border-socBorder text-xs font-mono text-slate-200 inline-flex items-center gap-1.5"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Retry Stream Query</span>
              </button>
            </div>
          ) : (
            <FlaggedModelsTable
              models={filteredModels}
              onSelectModel={setSelectedModelForDrawer}
              onToggleReviewed={handleToggleReviewed}
              selectedModelId={selectedModelForDrawer?.model_id}
            />
          )}
        </section>
      </main>

      {/* Evidence Side Drawer Modal (Lazily queries evidence on demand) */}
      <EvidenceDrawer
        model={selectedModelForDrawer}
        onClose={() => setSelectedModelForDrawer(null)}
        onToggleReviewed={handleToggleReviewed}
      />

      {/* Security Footer */}
      <footer className="mt-16 border-t border-socBorder/60 bg-charcoal/40 py-6 px-4 text-center text-xs font-mono text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            <span>MODELVAULT THREAT INTELLIGENCE &bull; CONTINUOUS AUDIT ENGINE</span>
          </div>
          <div className="text-slate-400 text-[11px]">
            CLASSIFIED // INTERNAL SEC-OPS ACCESS ONLY
          </div>
        </div>
      </footer>
    </div>
  );
}
