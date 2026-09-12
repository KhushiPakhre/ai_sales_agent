import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client.js'
import { useApiData } from '../hooks/useApiData.js'
import { EmptyState, ErrorState, SkeletonRows } from '../components/Feedback.jsx'
import PageHeader from '../components/PageHeader.jsx'

function Toggle({ checked, onChange, label }) {
  return (
    <label className="flex items-center gap-2.5 cursor-pointer select-none">
      <button
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 ${
          checked ? 'bg-brand-500' : 'bg-slate-200'
        }`}
      >
        <span
          className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow-sm transition-transform duration-200 ${
            checked ? 'translate-x-[18px]' : 'translate-x-1'
          }`}
        />
      </button>
      <span className="text-sm text-slate-600">{label}</span>
    </label>
  )
}

function fmtDate(ts) {
  if (!ts) return ''
  try { return new Date(ts).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) }
  catch { return '' }
}

export default function Handoffs() {
  const [pendingOnly, setPendingOnly] = useState(true)
  const { data: handoffs, loading, error, reload } = useApiData(() => api.listHandoffs(pendingOnly), [pendingOnly])

  return (
    <div>
      <PageHeader
        title="Handoffs"
        subtitle="Leads routed to human reps for negotiation or follow-up"
        actions={
          <Toggle
            checked={pendingOnly}
            onChange={setPendingOnly}
            label="Pending only"
          />
        }
      />

      {error && <ErrorState message={error.message} onRetry={reload} />}

      {!error && (
        <div className="space-y-3">
          {loading && <div className="card"><SkeletonRows rows={3} cols={3} /></div>}

          {!loading && (!handoffs || handoffs.length === 0) && (
            <EmptyState
              title={pendingOnly ? 'No pending handoffs' : 'No handoffs'}
              description={pendingOnly
                ? 'All caught up. Toggle to view all handoffs.'
                : 'Escalated leads will appear here once Nia routes them to a human.'}
            />
          )}

          {!loading && handoffs?.map((h) => {
            const isUrgent = h.urgency === 'urgent'
            return (
              <div
                key={h.lead_id}
                className={`card p-5 border-l-4 ${
                  isUrgent ? 'border-l-red-500' : 'border-l-slate-200'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="font-semibold text-slate-900 text-sm">{h.contact_name || h.lead_id}</p>
                    {h.company_name && <p className="text-xs text-slate-500 mt-0.5">{h.company_name}</p>}
                  </div>
                  <span className={`badge shrink-0 ${
                    isUrgent
                      ? 'bg-red-50 text-red-700 ring-1 ring-red-200'
                      : 'bg-slate-100 text-slate-600'
                  }`}>
                    {isUrgent ? '⚠️ Urgent' : 'Normal'}
                  </span>
                </div>

                {h.summary && <p className="text-sm text-slate-700 mt-2 leading-relaxed">{h.summary}</p>}

                <div className="grid sm:grid-cols-2 gap-3 mt-3">
                  <div>
                    <p className="text-xs text-slate-500 font-medium mb-0.5">Reason</p>
                    <p className="text-sm text-slate-800">{h.reason}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 font-medium mb-0.5">Suggested next step</p>
                    <p className="text-sm text-slate-800">{h.suggested_next_step}</p>
                  </div>
                </div>

                <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-100">
                  {h.created_at && (
                    <p className="text-xs text-slate-400">{fmtDate(h.created_at)}</p>
                  )}
                  <Link
                    to={`/leads/${encodeURIComponent(h.lead_id)}`}
                    className="btn-secondary text-xs ml-auto"
                  >
                    View lead
                  </Link>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
