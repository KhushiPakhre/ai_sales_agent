import React from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client.js'
import { useApiData } from '../hooks/useApiData.js'
import { StatusBadge, EmptyState, ErrorState, SkeletonRows } from '../components/Feedback.jsx'
import { useToast } from '../components/Toast.jsx'
import PageHeader from '../components/PageHeader.jsx'

function fmtDateTime(ts) {
  if (!ts) return '—'
  try {
    return new Date(ts).toLocaleString('en-IN', {
      weekday: 'short', day: 'numeric', month: 'short',
      hour: '2-digit', minute: '2-digit'
    })
  } catch { return ts }
}

export default function Tours() {
  const { data: tours, loading, error, reload } = useApiData(() => api.listTours(), [])
  const { push } = useToast()

  const setStatus = async (leadId, status) => {
    try {
      await api.updateTour(leadId, { status })
      push(`Tour marked ${status.replace(/_/g, ' ')}`)
      reload()
    } catch (err) {
      push(err.message || 'Could not update tour', 'error')
    }
  }

  const upcoming = tours?.filter(t => ['proposed', 'confirmed', 'reminded'].includes(t.status)) || []
  const past = tours?.filter(t => !['proposed', 'confirmed', 'reminded'].includes(t.status)) || []

  return (
    <div>
      <PageHeader
        title="Tours"
        subtitle="Site visits scheduled by Nia"
        badge={tours ? `${tours.length} total` : undefined}
      />

      {error && <ErrorState message={error.message} onRetry={reload} />}

      {!error && (
        <div className="space-y-4">
          {loading && <div className="card"><SkeletonRows rows={4} cols={4} /></div>}

          {!loading && (!tours || tours.length === 0) && (
            <EmptyState
              title="No tours scheduled"
              description="Tours for private cabins, dedicated desks, or managed offices will appear here."
            />
          )}

          {!loading && upcoming.length > 0 && (
            <div className="card overflow-hidden">
              <div className="px-5 py-3 bg-brand-50 border-b border-brand-100">
                <p className="text-xs font-semibold text-brand-700 uppercase tracking-wide">Upcoming</p>
              </div>
              <div className="divide-y divide-slate-100">
                {upcoming.map((t) => (
                  <TourRow key={t.lead_id} tour={t} onSetStatus={setStatus} />
                ))}
              </div>
            </div>
          )}

          {!loading && past.length > 0 && (
            <div className="card overflow-hidden">
              <div className="px-5 py-3 bg-slate-50 border-b border-slate-100">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Past tours</p>
              </div>
              <div className="divide-y divide-slate-100">
                {past.map((t) => (
                  <TourRow key={t.lead_id} tour={t} onSetStatus={setStatus} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function TourRow({ tour: t, onSetStatus }) {
  const isActionable = ['proposed', 'confirmed', 'reminded'].includes(t.status)
  return (
    <div className="px-5 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
      <div className="min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <p className="font-medium text-slate-900 text-sm">{t.workspace_name}</p>
          <StatusBadge status={t.status} />
          {t.reminder_sent && <span className="badge bg-amber-50 text-amber-700">Reminder sent</span>}
        </div>
        <p className="text-xs text-slate-500 mt-1">{fmtDateTime(t.proposed_time)}</p>
        <Link
          to={`/leads/${encodeURIComponent(t.lead_id)}`}
          className="text-xs text-brand-600 hover:underline mt-1 inline-block"
        >
          {t.contact_name || t.lead_id}
        </Link>
      </div>
      {isActionable && (
        <div className="flex items-center gap-2 shrink-0">
          <button className="btn-ghost text-xs" onClick={() => onSetStatus(t.lead_id, 'completed')}>
            Mark completed
          </button>
          <button className="btn-danger text-xs" onClick={() => onSetStatus(t.lead_id, 'no_show')}>
            No-show
          </button>
        </div>
      )}
    </div>
  )
}
