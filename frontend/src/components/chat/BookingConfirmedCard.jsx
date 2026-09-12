import React from 'react'

export default function BookingConfirmedCard({ booking, workspaceHint }) {
  const workspaceName = booking.workspace_name || workspaceHint

  return (
    <div className="card p-4 max-w-sm border-emerald-200 bg-emerald-50/30">
      {/* Header */}
      <div className="flex items-center gap-2.5 mb-3">
        <div className="h-8 w-8 rounded-full bg-emerald-100 flex items-center justify-center shrink-0">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="text-emerald-600" strokeLinecap="round" strokeLinejoin="round">
            <path d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <div>
          <p className="font-semibold text-sm text-slate-900">Booking Confirmed</p>
          <p className="text-xs text-slate-500">Here are your booking details</p>
        </div>
      </div>

      {/* Details */}
      <dl className="space-y-2 text-sm border-t border-emerald-100 pt-3">
        <div className="flex justify-between">
          <dt className="text-slate-500">Booking ID</dt>
          <dd className="font-medium text-slate-900 font-mono text-xs">{booking.booking_id}</dd>
        </div>
        {workspaceName && (
          <div className="flex justify-between">
            <dt className="text-slate-500">Workspace</dt>
            <dd className="font-medium text-slate-900 text-right max-w-[55%]">{workspaceName}</dd>
          </div>
        )}
        <div className="flex justify-between">
          <dt className="text-slate-500">Date</dt>
          <dd className="font-medium text-slate-900">
            {booking.date}{booking.time ? ` at ${booking.time}` : ''}
          </dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-slate-500">Seats</dt>
          <dd className="font-medium text-slate-900">{booking.seats}</dd>
        </div>
      </dl>
    </div>
  )
}
