 import React from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client.js'
import { useApiData } from '../hooks/useApiData.js'
import MetricCard from '../components/MetricCard.jsx'
import PageHeader from '../components/PageHeader.jsx'
import { ErrorState, SkeletonCard } from '../components/Feedback.jsx'

// Metric Icons
const LeadsIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
  </svg>
)
const HotIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 2c0 4-4 6-4 10a4 4 0 008 0c0-4-4-6-4-10z" />
    <path d="M12 12c0 2-2 3-2 5a2 2 0 004 0c0-2-2-3-2-5z" />
  </svg>
)
const BookingIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="4" width="18" height="18" rx="2" />
    <line x1="16" y1="2" x2="16" y2="6" />
    <line x1="8" y1="2" x2="8" y2="6" />
    <line x1="3" y1="10" x2="21" y2="10" />
    <path d="M9 16l2 2 4-4" />
  </svg>
)
const TourIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <polyline points="12,6 12,12 16,14" />
  </svg>
)
const HandoffIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="17,1 21,5 17,9" />
    <path d="M3 11V9a4 4 0 014-4h14" />
    <polyline points="7,23 3,19 7,15" />
    <path d="M21 13v2a4 4 0 01-4 4H3" />
  </svg>
)
const ConversionIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="22,7 13.5,15.5 8.5,10.5 2,17" />
    <polyline points="16,7 22,7 22,13" />
  </svg>
)

function TierBar({ label, value, total, color, bgColor }) {
  const pct = total && total > 0 ? Math.round((value / total) * 100) : 0
  return (
    <div>
      <div className="flex justify-between items-center text-xs mb-1.5">
        <span className="font-medium text-slate-700">{label}</span>
        <span className="text-slate-500">
          <span className="font-semibold text-slate-800">{value}</span>
          <span className="text-slate-400 ml-1">({pct}%)</span>
        </span>
      </div>
      <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all duration-700 ease-out`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

function QuickActionCard({ to, icon: Icon, label, description, accent }) {
  return (
    <Link
      to={to}
      className="flex items-start gap-3 p-3 rounded-lg border border-slate-200 hover:border-brand-300 hover:bg-brand-50/50 transition-all duration-150 group"
    >
      <div className={`h-8 w-8 rounded-lg flex items-center justify-center shrink-0 ${accent}`}>
        <Icon />
      </div>
      <div className="min-w-0">
        <p className="text-sm font-medium text-slate-900 group-hover:text-brand-700">{label}</p>
        <p className="text-xs text-slate-500 mt-0.5">{description}</p>
      </div>
    </Link>
  )
}

const ChatActionIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="text-brand-600">
    <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
  </svg>
)
const LeadsActionIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="text-violet-600">
    <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
  </svg>
)
const HandoffActionIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="text-amber-600">
    <polyline points="17,1 21,5 17,9" />
    <path d="M3 11V9a4 4 0 014-4h14" />
    <polyline points="7,23 3,19 7,15" />
    <path d="M21 13v2a4 4 0 01-4 4H3" />
  </svg>
)

export default function Dashboard() {
  const { data, loading, error, reload } = useApiData(() => api.getAnalytics(), [])

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        subtitle="Live snapshot of your pipeline, bookings, and agent performance."
      />

      {error && <ErrorState message={error.message} onRetry={reload} />}

      {!error && (
        <>
          {/* Metric cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
            {loading || !data ? (
              Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)
            ) : (
              <>
                <MetricCard label="Total Leads" value={data.total_leads} icon={LeadsIcon} />
                <MetricCard label="Hot Leads" value={data.hot_leads} tone="danger" icon={HotIcon} />
                <MetricCard label="Bookings" value={data.total_bookings} tone="success" icon={BookingIcon} />
                <MetricCard label="Tours" value={data.total_tours} icon={TourIcon} />
                <MetricCard label="Pending Handoffs" value={data.pending_handoffs} tone="warning" icon={HandoffIcon} />
                <MetricCard
                  label="Conversion Rate"
                  value={data.conversion_rate}
                  suffix="%"
                  tone={data.conversion_rate > 0 ? 'success' : 'default'}
                  icon={ConversionIcon}
                />
              </>
            )}
          </div>

          {/* Two-column section: Pipeline + Quick Actions */}
          {data && (
            <div className="grid sm:grid-cols-2 gap-4">
              {/* Lead quality */}
              <div className="card p-5">
                <p className="section-title mb-4">Lead Pipeline</p>
                <div className="space-y-3">
                  <TierBar label="Hot" value={data.hot_leads} total={data.total_leads} color="bg-red-500" />
                  <TierBar label="Warm" value={data.warm_leads} total={data.total_leads} color="bg-amber-400" />
                  <TierBar label="Cold" value={data.cold_leads} total={data.total_leads} color="bg-slate-300" />
                </div>
                {data.total_leads === 0 && (
                  <p className="text-xs text-slate-400 mt-4 text-center">No leads yet. Start a chat conversation to generate leads.</p>
                )}
              </div>

              {/* Quick actions */}
              <div className="card p-5">
                <p className="section-title mb-4">Quick Actions</p>
                <div className="space-y-2">
                  <QuickActionCard
                    to="/chat"
                    icon={ChatActionIcon}
                    label="Start a conversation"
                    description="Chat with a new lead via Nia"
                    accent="bg-brand-50"
                  />
                  <QuickActionCard
                    to="/leads"
                    icon={LeadsActionIcon}
                    label="View all leads"
                    description="Browse and filter your CRM"
                    accent="bg-violet-50"
                  />
                  <QuickActionCard
                    to="/handoffs"
                    icon={HandoffActionIcon}
                    label="Review handoffs"
                    description="Leads requiring human follow-up"
                    accent="bg-amber-50"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Workspace utilization */}
          {data?.workspace_utilization?.length > 0 && (
            <div className="card p-5">
              <p className="section-title mb-4">Workspace Utilization <span className="text-slate-400 font-normal text-xs ml-1">(by bookings)</span></p>
              <div className="space-y-3">
                {(() => {
                  const maxCount = Math.max(...data.workspace_utilization.map(w => w.booking_count), 1)
                  return data.workspace_utilization.map((w) => (
                    <div key={w.workspace_id} className="flex items-center gap-3 text-sm">
                      <span className="text-slate-700 w-40 sm:w-56 truncate shrink-0">
                        {w.name}
                        <span className="text-slate-400 text-xs ml-1">({w.city})</span>
                      </span>
                      <div className="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-brand-400 transition-all duration-700"
                          style={{ width: `${Math.round((w.booking_count / maxCount) * 100)}%` }}
                        />
                      </div>
                      <span className="text-slate-600 font-medium text-xs w-16 text-right shrink-0">
                        {w.booking_count} {w.booking_count === 1 ? 'booking' : 'bookings'}
                      </span>
                    </div>
                  ))
                })()}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
