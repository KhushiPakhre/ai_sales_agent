import React from 'react'
import { Link } from 'react-router-dom'

const INSTANT_BOOK_TYPES = ['day_pass', 'meeting_room']

// Pricing label depends on workspace type
function getPriceLabel(wsType) {
  if (wsType === 'day_pass') return '/ day'
  if (wsType === 'meeting_room') return '/ day'
  return '/ seat / month'
}

function TypeBadge({ wsType }) {
  const label = (wsType || '').replace(/_/g, ' ')
  const styles = {
    hot_desk: 'bg-blue-50 text-blue-700',
    dedicated_desk: 'bg-violet-50 text-violet-700',
    private_cabin: 'bg-brand-50 text-brand-700',
    managed_office: 'bg-emerald-50 text-emerald-700',
    day_pass: 'bg-amber-50 text-amber-700',
    meeting_room: 'bg-orange-50 text-orange-700',
  }
  return (
    <span className={`badge ${styles[wsType] || 'bg-slate-100 text-slate-600'}`}>
      {label || 'workspace'}
    </span>
  )
}

export default function RecommendationCard({ recommendation, onScheduleTour }) {
  const ws = recommendation.workspace
  const canScheduleTour = !INSTANT_BOOK_TYPES.includes(ws.workspace_type)
  const priceLabel = getPriceLabel(ws.workspace_type)

  return (
    <div className="card p-4 w-72 sm:w-80 shrink-0 snap-start flex flex-col gap-3">
      {/* Header */}
      <div>
        <p className="font-semibold text-slate-900 text-sm leading-snug">{ws.name}</p>
        <p className="text-xs text-slate-500 mt-0.5">{ws.city}</p>
      </div>

      {/* Metadata badges - each on its own logical group */}
      <div className="flex flex-wrap gap-1.5">
        <TypeBadge wsType={ws.workspace_type} />
        <span className="badge bg-slate-100 text-slate-600">
          {ws.capacity_min}&ndash;{ws.capacity_max} seats
        </span>
        <span className="badge bg-amber-50 text-amber-700">
          &#9733; {ws.rating}
        </span>
      </div>

      {/* Price - clearly labeled */}
      <div className="flex items-baseline gap-1">
        <span className="text-base font-bold text-slate-900">
          &#8377;{ws.price_per_seat_inr.toLocaleString('en-IN')}
        </span>
        <span className="text-xs text-slate-500">{priceLabel}</span>
      </div>

      {/* Match reasons */}
      {recommendation.match_reasons?.length > 0 && (
        <p className="text-xs text-slate-500 leading-relaxed">
          {recommendation.match_reasons.join(' \u00b7 ')}
        </p>
      )}

      {/* Actions - clearly inside this card */}
      <div className="flex gap-2 mt-auto pt-1">
        <Link
          to={`/workspaces/${ws.id}`}
          className="btn-secondary text-xs flex-1 py-2"
        >
          View details
        </Link>
        {canScheduleTour && (
          <button
            onClick={() => onScheduleTour(ws)}
            className="btn-primary text-xs flex-1 py-2"
          >
            Schedule tour
          </button>
        )}
      </div>
    </div>
  )
}
