import React from 'react'

const TOUR_STATUS_LABEL = {
  proposed: 'Tour pencilled in',
  confirmed: 'Tour confirmed',
  reminded: 'Reminder sent',
  no_show: 'Missed — awaiting reschedule',
  completed: 'Tour completed',
}

export default function HandoffCard({ handoff, tour }) {
  return (
    <div className="card p-4 max-w-sm border-brand-200 bg-brand-50/20">
      {/* Header */}
      <div className="flex items-center gap-2.5 mb-3">
        <div className="h-8 w-8 rounded-full bg-brand-100 flex items-center justify-center shrink-0">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="text-brand-600" strokeLinecap="round" strokeLinejoin="round">
            <path d="M17 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75" />
          </svg>
        </div>
        <div>
          <p className="font-semibold text-sm text-slate-900">Connecting you with our team</p>
          <p className="text-xs text-slate-500">A sales specialist will follow up with you</p>
        </div>
      </div>

      {/* Details */}
      <div className="space-y-2.5 border-t border-brand-100 pt-3">
        <div>
          <p className="text-xs font-medium text-slate-500 mb-0.5">Reason</p>
          <p className="text-sm text-slate-800">{handoff.reason}</p>
        </div>
        <div>
          <p className="text-xs font-medium text-slate-500 mb-0.5">Next step</p>
          <p className="text-sm text-slate-800">{handoff.suggested_next_step}</p>
        </div>
      </div>

      {/* Tour info if present */}
      {tour && (
        <div className="mt-3 pt-3 border-t border-brand-100">
          <p className="text-xs font-medium text-slate-500 mb-1">
            {TOUR_STATUS_LABEL[tour.status] || 'Tour scheduled'}
          </p>
          <p className="text-sm text-slate-800">
            {tour.workspace_name} &middot; {new Date(tour.proposed_time).toLocaleString()}
          </p>
        </div>
      )}

      {/* Urgency badge */}
      <div className="mt-3">
        <span className={
          'badge ' + (handoff.urgency === 'urgent'
            ? 'bg-red-50 text-red-700 ring-1 ring-red-200'
            : 'bg-slate-100 text-slate-600')
        }>
          {handoff.urgency === 'urgent' ? '\u26a0\ufe0f Urgent' : 'Normal priority'}
        </span>
      </div>
    </div>
  )
}
