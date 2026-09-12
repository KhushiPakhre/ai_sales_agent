import React from 'react'

const TIER_STYLES = {
  hot: 'bg-red-50 text-red-700 ring-1 ring-red-200',
  warm: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
  cold: 'bg-slate-100 text-slate-600',
}

const STATUS_STYLES = {
  confirmed: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200',
  proposed: 'bg-brand-50 text-brand-700 ring-1 ring-brand-200',
  reminded: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
  no_show: 'bg-red-50 text-red-700 ring-1 ring-red-200',
  completed: 'bg-slate-100 text-slate-600',
  cancelled: 'bg-slate-100 text-slate-500 line-through',
  booked: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200',
  tour_scheduled: 'bg-brand-50 text-brand-700 ring-1 ring-brand-200',
  awaiting_reply: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
  new: 'bg-slate-100 text-slate-600',
  active: 'bg-brand-50 text-brand-700 ring-1 ring-brand-200',
  pending: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
}

export function TierBadge({ tier }) {
  if (!tier) return <span className="badge bg-slate-100 text-slate-500">Unscored</span>
  const dots = { hot: 'bg-red-500', warm: 'bg-amber-500', cold: 'bg-slate-400' }
  return (
    <span className={`badge ${TIER_STYLES[tier] || 'bg-slate-100 text-slate-600'}`}>
      <span className={`inline-block h-1.5 w-1.5 rounded-full mr-1 ${dots[tier] || 'bg-slate-400'}`} />
      {tier.charAt(0).toUpperCase() + tier.slice(1)}
    </span>
  )
}

export function StatusBadge({ status }) {
  const label = (status || 'unknown').replace(/_/g, ' ')
  return (
    <span className={`badge ${STATUS_STYLES[status] || 'bg-slate-100 text-slate-600'}`}>
      {label.charAt(0).toUpperCase() + label.slice(1)}
    </span>
  )
}

export function EmptyState({ title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-16 px-6">
      <div className="h-12 w-12 rounded-full bg-slate-100 flex items-center justify-center mb-4">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-slate-400">
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" strokeLinecap="round" />
        </svg>
      </div>
      <p className="text-sm font-semibold text-slate-700">{title}</p>
      {description && <p className="text-sm text-slate-400 mt-1 max-w-xs">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-16 px-6">
      <div className="h-12 w-12 rounded-full bg-red-50 flex items-center justify-center mb-4">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-red-500">
          <path d="M12 9v4m0 4h.01M10.29 3.86l-8.18 14.18A2 2 0 004.18 21h15.64a2 2 0 001.87-2.96L13.71 3.86a2 2 0 00-3.42 0z" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <p className="text-sm font-semibold text-slate-700">Something went wrong</p>
      {message && <p className="text-sm text-slate-400 mt-1 max-w-xs">{message}</p>}
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary mt-5">
          Try again
        </button>
      )}
    </div>
  )
}

export function SkeletonRows({ rows = 5, cols = 4 }) {
  return (
    <div className="animate-pulse divide-y divide-slate-100">
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-4 px-5 py-4">
          {Array.from({ length: cols }).map((_, c) => (
            <div
              key={c}
              className="h-3 bg-slate-100 rounded-full flex-1"
              style={{ width: c === 0 ? '30%' : undefined }}
            />
          ))}
        </div>
      ))}
    </div>
  )
}

export function SkeletonCard({ lines = 2 }) {
  return (
    <div className="card p-4 animate-pulse">
      <div className="h-2.5 bg-slate-100 rounded-full w-24 mb-3" />
      <div className="h-7 bg-slate-100 rounded-lg w-16" />
      {lines > 2 && <div className="h-2 bg-slate-100 rounded-full w-32 mt-3" />}
    </div>
  )
}
