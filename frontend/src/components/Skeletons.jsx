import React from 'react';

export function StatsSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="bg-panel border border-socBorder/60 rounded-lg p-5 flex items-center justify-between"
        >
          <div className="space-y-2 w-full">
            <div className="h-3.5 w-28 skeleton-shimmer rounded"></div>
            <div className="h-8 w-16 skeleton-shimmer rounded"></div>
            <div className="h-2.5 w-36 skeleton-shimmer rounded"></div>
          </div>
          <div className="h-10 w-10 rounded-lg skeleton-shimmer"></div>
        </div>
      ))}
    </div>
  );
}

export function TopSuspiciousSkeleton() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-8">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="bg-panel border border-socBorder/80 rounded-lg p-5 flex flex-col justify-between space-y-4"
        >
          <div className="flex items-center justify-between">
            <div className="h-4 w-36 skeleton-shimmer rounded"></div>
            <div className="h-6 w-16 skeleton-shimmer rounded-full"></div>
          </div>
          <div className="space-y-2">
            <div className="h-3 w-full skeleton-shimmer rounded"></div>
            <div className="h-3 w-4/5 skeleton-shimmer rounded"></div>
          </div>
          <div className="h-2 w-full skeleton-shimmer rounded-full"></div>
          <div className="h-8 w-full skeleton-shimmer rounded"></div>
        </div>
      ))}
    </div>
  );
}

export function TableSkeleton() {
  return (
    <div className="bg-panel border border-socBorder rounded-lg overflow-hidden">
      <div className="p-4 border-b border-socBorder/80 flex justify-between items-center">
        <div className="h-4 w-40 skeleton-shimmer rounded"></div>
        <div className="h-4 w-24 skeleton-shimmer rounded"></div>
      </div>
      <div className="divide-y divide-socBorder/40">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="p-4 flex items-center justify-between gap-4">
            <div className="h-4 w-48 skeleton-shimmer rounded"></div>
            <div className="h-4 w-28 skeleton-shimmer rounded"></div>
            <div className="h-4 w-20 skeleton-shimmer rounded"></div>
            <div className="h-4 w-32 skeleton-shimmer rounded"></div>
            <div className="h-6 w-20 skeleton-shimmer rounded-full"></div>
          </div>
        ))}
      </div>
    </div>
  );
}
