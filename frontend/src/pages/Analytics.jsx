import React from 'react'
import { api } from '../api/client.js'
import { useApiData } from '../hooks/useApiData.js'
import MetricCard from '../components/MetricCard.jsx'
import PageHeader from '../components/PageHeader.jsx'
import { ErrorState, SkeletonCard, EmptyState } from '../components/Feedback.jsx'

// Metric Icons
const TotalLeadsIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
  </svg>
)
const BookingIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="4" width="18" height="18" rx="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" /><path d="M9 16l2 2 4-4" />
  </svg>
)
const TourIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" /><polyline points="12,6 12,12 16,14" />
  </svg>
)
const ConvIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22,7 13.5,15.5 8.5,10.5 2,17" /><polyline points="16,7 22,7 22,13" />
  </svg>
)
const HandoffIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="17,1 21,5 17,9" /><path d="M3 11V9a4 4 0 014-4h14" />
    <polyline points="7,23 3,19 7,15" /><path d="M21 13v2a4 4 0 01-4 4H3" />
  </svg>
)
const ShowRateIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" />
  </svg>
)

// Conversion funnel stage
function FunnelStage({ label, value, total, color, isLast }) {
  const pct = total && total > 0 ? Math.round((value / total) * 100) : 0
  const width = total > 0 ? Math.max(pct, 8) : 100  // min 8% for visibility
  return (
    <div className="flex items-center gap-4">
      <div className="w-24 text-right text-xs text-slate-500 font-medium shrink-0">{label}</div>
      <div className="flex-1 flex items-center gap-3">
        <div className="flex-1 h-9 bg-slate-50 rounded-lg overflow-hidden relative">
          <div
            className={`h-full ${color} rounded-lg flex items-center px-3 transition-all duration-700`}
            style={{ width: `${width}%` }}
          >
            <span className="text-white text-sm font-bold whitespace-nowrap">{value}</span>
          </div>
        </div>
        <span className="text-xs text-slate-400 w-10 shrink-0">{pct}%</span>
      </div>
      {!isLast && (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-slate-300 absolute -mb-9 ml-28 hidden" strokeLinecap="round">
          <path d="M12 5v14M5 12l7 7 7-7" />
        </svg>
      )}
    </div>
  )
}

export default function Analytics() {
  const { data, loading, error, reload } = useApiData(() => api.getAnalytics(), [])

  return (
    <div>
      <PageHeader
        title="Analytics"
        subtitle="Performance metrics computed from your live database"
      />

      {error && <ErrorState message={error.message} onRetry={reload} />}

      {!error && (loading || !data) && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {Array.from({ length: 8 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      )}

      {!error && data && (
        <div className="space-y-6">
          {/* Full metric grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <MetricCard label="Total Leads" value={data.total_leads} icon={TotalLeadsIcon} />
            <MetricCard label="Hot Leads" value={data.hot_leads} tone="danger" />
            <MetricCard label="Warm Leads" value={data.warm_leads} tone="warning" />
            <MetricCard label="Cold Leads" value={data.cold_leads} />
            <MetricCard label="Total Bookings" value={data.total_bookings} tone="success" icon={BookingIcon} />
            <MetricCard label="Tours Scheduled" value={data.total_tours} icon={TourIcon} />
            <MetricCard label="Pending Handoffs" value={data.pending_handoffs} icon={HandoffIcon} />
            <MetricCard
              label="Conversion Rate"
              value={data.conversion_rate}
              suffix="%"
              tone={data.conversion_rate > 0 ? 'success' : 'default'}
              icon={ConvIcon}
            />
          </div>

          {/* Two-column: Funnel + Show Rate */}
          <div className="grid sm:grid-cols-3 gap-4">
            {/* Conversion funnel */}
            <div className="card p-5 sm:col-span-2">
              <p className="section-title mb-1">Lead → Tour → Booking Pipeline</p>
              <p className="text-xs text-slate-400 mb-5">How leads progress through Nia's qualification flow</p>
              {data.total_leads === 0 ? (
                <EmptyState title="No pipeline data yet" description="Start conversations with leads to see the funnel." />
              ) : (
                <div className="space-y-3">
                  <FunnelStage label="Leads" value={data.total_leads} total={data.total_leads} color="bg-brand-500" />
                  <FunnelStage label="Tours" value={data.total_tours} total={data.total_leads} color="bg-amber-500" />
                  <FunnelStage label="Bookings" value={data.total_bookings} total={data.total_leads} color="bg-emerald-500" isLast />
                </div>
              )}
            </div>

            {/* Tour show rate */}
            <div className="card p-5">
              <p className="section-title mb-1">Tour Show Rate</p>
              <p className="text-xs text-slate-400 mb-5">Completed vs. no-show tours</p>
              {data.tour_show_rate != null ? (
                <div className="text-center py-4">
                  <p className="text-4xl font-bold text-slate-900">{data.tour_show_rate}<span className="text-xl text-slate-400">%</span></p>
                  <p className="text-xs text-slate-400 mt-2">of scheduled tours were attended</p>
                  {/* Simple donut representation */}
                  <div className="mt-4 flex items-center justify-center gap-4 text-xs">
                    <span className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
                      <span className="text-slate-500">Completed</span>
                    </span>
                    <span className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-red-400"></span>
                      <span className="text-slate-500">No-show</span>
                    </span>
                  </div>
                </div>
              ) : (
                <EmptyState title="No tour data" description="Appears after tours are completed or marked no-show." />
              )}
            </div>
          </div>

          {/* Lead quality distribution */}
          <div className="card p-5">
            <p className="section-title mb-4">Lead Quality Distribution</p>
            {data.total_leads === 0 ? (
              <EmptyState title="No leads yet" />
            ) : (
              <div className="space-y-3">
                {[
                  { label: 'Hot', value: data.hot_leads, color: 'bg-red-500', textColor: 'text-red-600' },
                  { label: 'Warm', value: data.warm_leads, color: 'bg-amber-400', textColor: 'text-amber-600' },
                  { label: 'Cold', value: data.cold_leads, color: 'bg-slate-300', textColor: 'text-slate-600' },
                ].map(({ label, value, color, textColor }) => {
                  const pct = data.total_leads > 0 ? Math.round((value / data.total_leads) * 100) : 0
                  return (
                    <div key={label} className="flex items-center gap-4">
                      <span className={`text-sm font-medium ${textColor} w-12 shrink-0`}>{label}</span>
                      <div className="flex-1 h-3 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${color} transition-all duration-700`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-slate-700 w-8 text-right shrink-0">{value}</span>
                      <span className="text-xs text-slate-400 w-8 shrink-0">{pct}%</span>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* Workspace utilization */}
          <div className="card p-5">
            <p className="section-title mb-4">Workspace Utilization <span className="font-normal text-slate-400 text-xs ml-1">(by confirmed bookings)</span></p>
            {data.workspace_utilization.length === 0 ? (
              <EmptyState
                title="No bookings yet"
                description="Utilization data appears once workspaces start receiving bookings."
              />
            ) : (
              <div className="space-y-2.5">
                {(() => {
                  const maxCount = Math.max(...data.workspace_utilization.map(w => w.booking_count), 1)
                  return data.workspace_utilization.map((w) => (
                    <div key={w.workspace_id} className="flex items-center gap-4">
                      <div className="min-w-0 w-48 shrink-0">
                        <p className="text-sm text-slate-700 font-medium truncate">{w.name}</p>
                        <p className="text-xs text-slate-400">{w.city} · {w.workspace_type.replace(/_/g, ' ')}</p>
                      </div>
                      <div className="flex-1 h-3 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-brand-400 rounded-full transition-all duration-700"
                          style={{ width: `${Math.round((w.booking_count / maxCount) * 100)}%` }}
                        />
                      </div>
                      <span className="text-sm font-semibold text-slate-700 shrink-0 w-20 text-right">
                        {w.booking_count} {w.booking_count === 1 ? 'booking' : 'bookings'}
                      </span>
                    </div>
                  ))
                })()}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
