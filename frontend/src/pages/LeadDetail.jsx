import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api, ApiError } from '../api/client.js'
import { useApiData } from '../hooks/useApiData.js'
import { TierBadge, StatusBadge, ErrorState, SkeletonCard, EmptyState } from '../components/Feedback.jsx'
import PageHeader from '../components/PageHeader.jsx'

function Field({ label, value }) {
  return (
    <div>
      <p className="field-label">{label}</p>
      <p className="field-value">{value ?? '—'}</p>
    </div>
  )
}

function fmtBudget(v) {
  if (!v) return null
  return `₹${Number(v).toLocaleString('en-IN')} / seat`
}

export default function LeadDetail() {
  const { leadId } = useParams()
  const { data: lead, loading, error, reload } = useApiData(() => api.getLead(leadId), [leadId])
  const [handoff, setHandoff] = useState(null)

  useEffect(() => {
    let cancelled = false
    api.getHandoff(leadId).then((h) => !cancelled && setHandoff(h)).catch(() => {})
    return () => { cancelled = true }
  }, [leadId])

  if (loading) {
    return (
      <div className="grid lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-3">
          <SkeletonCard lines={3} />
          <SkeletonCard lines={3} />
        </div>
        <SkeletonCard lines={4} />
      </div>
    )
  }

  if (error) {
    const notFound = error instanceof ApiError && error.status === 404
    return notFound
      ? <EmptyState title="Lead not found" description={`No lead with ID: ${leadId}`} />
      : <ErrorState message={error.message} onRetry={reload} />
  }

  const req = lead.requirement

  return (
    <div>
      <PageHeader
        title={req.contact_name || lead.lead_id}
        subtitle={req.company_name || 'No company on file'}
        actions={
          <Link to={`/chat/${encodeURIComponent(lead.lead_id)}`} className="btn-primary">
            Continue in chat
          </Link>
        }
      />

      <div className="grid lg:grid-cols-3 gap-5">
        {/* Main: conversation timeline */}
        <div className="lg:col-span-2 card p-5">
          <p className="section-title mb-4">
            Conversation
            <span className="ml-2 text-slate-400 font-normal text-xs">{lead.history.length} messages</span>
          </p>
          {lead.history.length === 0 ? (
            <EmptyState title="No messages yet" description="This lead has no conversation history yet." />
          ) : (
            <div className="space-y-3 max-h-[36rem] overflow-y-auto pr-1">
              {lead.history.map((turn, i) => {
                const isInbound = turn.direction === 'inbound'
                return (
                  <div key={i} className={`flex ${isInbound ? 'justify-start' : 'justify-end'}`}>
                    <div
                      className={
                        'max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ' +
                        (isInbound
                          ? 'bg-slate-100 text-slate-800 rounded-bl-sm'
                          : 'bg-brand-50 text-brand-900 rounded-br-sm border border-brand-100')
                      }
                    >
                      <p className="whitespace-pre-wrap break-words">{turn.text}</p>
                      <p className="text-[10px] text-slate-400 mt-1.5">
                        {isInbound ? 'Lead' : 'Nia'} · {new Date(turn.timestamp).toLocaleString('en-IN', { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' })}
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Qualification card */}
          <div className="card p-4">
            <div className="flex items-center justify-between mb-4">
              <p className="section-title">Qualification</p>
              <TierBadge tier={lead.tier} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Location" value={req.location} />
              <Field label="Team size" value={req.team_size} />
              <Field label="Workspace type" value={req.workspace_type?.replace(/_/g, ' ')} />
              <Field label="Budget / seat" value={fmtBudget(req.budget_per_seat)} />
              <Field label="Timeline" value={req.move_in_timeline} />
              <Field label="Channel" value={req.channel} />
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100">
              <StatusBadge status={lead.status} />
            </div>
          </div>

          {/* Recommendations shown */}
          {lead.last_recommendations?.length > 0 && (
            <div className="card p-4">
              <p className="section-title mb-3">Recommendations shown</p>
              <div className="space-y-2">
                {lead.last_recommendations.map((ws) => (
                  <Link
                    key={ws.id}
                    to={`/workspaces/${ws.id}`}
                    className="flex items-center justify-between p-2.5 rounded-lg hover:bg-slate-50 border border-slate-100 transition-colors"
                  >
                    <div className="min-w-0">
                      <p className="font-medium text-sm text-slate-900 truncate">{ws.name}</p>
                      <p className="text-xs text-slate-500">{ws.city} · ₹{ws.price_per_seat_inr}/seat</p>
                    </div>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-slate-400 shrink-0 ml-2" strokeLinecap="round">
                      <path d="M9 18l6-6-6-6" />
                    </svg>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Bookings */}
          {lead.bookings?.length > 0 && (
            <div className="card p-4">
              <p className="section-title mb-3">Bookings</p>
              <div className="space-y-2">
                {lead.bookings.map((b) => (
                  <div key={b.booking_id} className="flex items-center justify-between text-sm">
                    <div className="min-w-0">
                      <p className="font-medium text-slate-900 truncate">{b.workspace_name}</p>
                      <p className="text-xs text-slate-500">{b.date}{b.time ? ` at ${b.time}` : ''}</p>
                    </div>
                    <StatusBadge status={b.status} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tour */}
          {lead.tour && (
            <div className="card p-4">
              <p className="section-title mb-2">Tour</p>
              <p className="text-sm font-medium text-slate-900">{lead.tour.workspace_name}</p>
              <p className="text-xs text-slate-500 mt-0.5">
                {new Date(lead.tour.proposed_time).toLocaleString('en-IN', { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
              </p>
              <div className="mt-2">
                <StatusBadge status={lead.tour.status} />
              </div>
            </div>
          )}

          {/* Handoff */}
          {handoff && (
            <div className="card p-4 border-brand-200">
              <p className="section-title mb-3">Handoff</p>
              <div className="space-y-2">
                <div>
                  <p className="field-label">Reason</p>
                  <p className="text-sm text-slate-800">{handoff.reason}</p>
                </div>
                <div>
                  <p className="field-label">Suggested next step</p>
                  <p className="text-sm text-slate-800">{handoff.suggested_next_step}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
