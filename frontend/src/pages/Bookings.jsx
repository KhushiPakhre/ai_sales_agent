import React from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client.js'
import { useApiData } from '../hooks/useApiData.js'
import { StatusBadge, EmptyState, ErrorState, SkeletonRows } from '../components/Feedback.jsx'
import { useToast } from '../components/Toast.jsx'
import PageHeader from '../components/PageHeader.jsx'

export default function Bookings() {
  const { data: bookings, loading, error, reload } = useApiData(() => api.listBookings(), [])
  const { push } = useToast()

  const setStatus = async (bookingId, status) => {
    try {
      await api.updateBooking(bookingId, { status })
      push(`Booking marked ${status.replace(/_/g, ' ')}`)
      reload()
    } catch (err) {
      push(err.message || 'Could not update booking', 'error')
    }
  }

  return (
    <div>
      <PageHeader
        title="Bookings"
        subtitle="All confirmed and pending bookings"
        badge={bookings ? `${bookings.length} total` : undefined}
      />

      {error && <ErrorState message={error.message} onRetry={reload} />}

      {!error && (
        <div className="card overflow-hidden">
          {loading && <SkeletonRows rows={5} cols={5} />}

          {!loading && (!bookings || bookings.length === 0) && (
            <EmptyState
              title="No bookings yet"
              description="Instant bookings confirmed by Nia, or manual bookings, will appear here."
            />
          )}

          {!loading && bookings?.length > 0 && (
            <div className="divide-y divide-slate-100">
              {bookings.map((b) => (
                <div key={b.booking_id} className="px-5 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-medium text-slate-900 text-sm">{b.workspace_name}</p>
                      <StatusBadge status={b.status} />
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      {b.city} · {b.date}{b.time ? ` at ${b.time}` : ''} · {b.seats} seat{b.seats !== 1 ? 's' : ''}
                    </p>
                    <Link
                      to={`/leads/${encodeURIComponent(b.lead_id)}`}
                      className="text-xs text-brand-600 hover:underline mt-1 inline-block"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {b.contact_name || b.lead_id}
                    </Link>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-slate-400 font-mono hidden sm:inline">{b.booking_id}</span>
                    {b.status === 'confirmed' && (
                      <>
                        <button
                          className="btn-ghost text-xs"
                          onClick={() => setStatus(b.booking_id, 'completed')}
                        >
                          Mark completed
                        </button>
                        <button
                          className="btn-danger text-xs"
                          onClick={() => setStatus(b.booking_id, 'cancelled')}
                        >
                          Cancel
                        </button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
