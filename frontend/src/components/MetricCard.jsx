import React from 'react'

const TONE_STYLES = {
  default: {
    value: 'text-slate-900',
    accent: 'bg-brand-500',
    icon: 'text-brand-400',
  },
  danger: {
    value: 'text-red-600',
    accent: 'bg-red-500',
    icon: 'text-red-400',
  },
  success: {
    value: 'text-emerald-600',
    accent: 'bg-emerald-500',
    icon: 'text-emerald-400',
  },
  warning: {
    value: 'text-amber-600',
    accent: 'bg-amber-500',
    icon: 'text-amber-400',
  },
}

export default function MetricCard({ label, value, suffix, tone = 'default', icon: Icon, description }) {
  const styles = TONE_STYLES[tone] || TONE_STYLES.default

  return (
    <div className="card p-4 hover:shadow-md transition-shadow duration-150 relative overflow-hidden">
      {/* Top accent line */}
      <div className={`absolute top-0 left-0 right-0 h-0.5 ${styles.accent}`} />

      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium text-slate-500 truncate">{label}</p>
          <p className={`mt-1.5 text-2xl font-bold tracking-tight ${styles.value}`}>
            {value ?? '—'}
            {suffix && <span className="text-sm font-normal text-slate-400 ml-1">{suffix}</span>}
          </p>
          {description && (
            <p className="text-xs text-slate-400 mt-1">{description}</p>
          )}
        </div>
        {Icon && (
          <div className={`shrink-0 ${styles.icon}`}>
            <Icon />
          </div>
        )}
      </div>
    </div>
  )
} 
