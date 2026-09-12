import React, { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client.js'
import { useApiData } from '../hooks/useApiData.js'
import { EmptyState, ErrorState, SkeletonRows } from '../components/Feedback.jsx'
import { useToast } from '../components/Toast.jsx'
import PageHeader from '../components/PageHeader.jsx'

const WORKSPACE_TYPES = [
  'hot_desk', 'dedicated_desk', 'private_cabin',
  'managed_office', 'day_pass', 'meeting_room'
]

const TYPE_LABELS = {
  hot_desk: 'Hot Desk',
  dedicated_desk: 'Dedicated Desk',
  private_cabin: 'Private Cabin',
  managed_office: 'Managed Office',
  day_pass: 'Day Pass',
  meeting_room: 'Meeting Room',
}

const TYPE_STYLES = {
  hot_desk: 'bg-blue-50 text-blue-700',
  dedicated_desk: 'bg-violet-50 text-violet-700',
  private_cabin: 'bg-brand-50 text-brand-700',
  managed_office: 'bg-emerald-50 text-emerald-700',
  day_pass: 'bg-amber-50 text-amber-700',
  meeting_room: 'bg-orange-50 text-orange-700',
}

const emptyForm = {
  name: '', city: '', workspace_type: 'hot_desk',
  capacity_min: 1, capacity_max: 10,
  price_per_seat_inr: 5000, amenities: '',
  available_from: 'immediate', rating: 4.0, daily_capacity: '',
}

// Simple debounce hook
function useDebounce(value, delay) {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  return debounced
}

export default function Workspaces() {
  const [cityInput, setCityInput] = useState('')
  const [type, setType] = useState('all')
  const [showForm, setShowForm] = useState(false)
  const debouncedCity = useDebounce(cityInput, 300)

  const { data: workspaces, loading, error, reload } = useApiData(
    () => api.listWorkspaces({
      city: debouncedCity || undefined,
      workspace_type: type === 'all' ? undefined : type
    }),
    [debouncedCity, type]
  )

  return (
    <div>
      <PageHeader
        title="Workspaces"
        subtitle="Inventory available for Nia to recommend"
        badge={workspaces ? `${workspaces.length} listings` : undefined}
        actions={
          <button
            className={showForm ? 'btn-secondary' : 'btn-primary'}
            onClick={() => setShowForm((s) => !s)}
          >
            {showForm ? 'Cancel' : '+ Add workspace'}
          </button>
        }
      />

      {showForm && (
        <div className="mb-6">
          <WorkspaceForm onDone={() => { setShowForm(false); reload() }} />
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-2 mb-5">
        <input
          className="input sm:max-w-xs"
          placeholder="Filter by city…"
          value={cityInput}
          onChange={(e) => setCityInput(e.target.value)}
        />
        <select
          className="input sm:max-w-[200px]"
          value={type}
          onChange={(e) => setType(e.target.value)}
        >
          <option value="all">All types</option>
          {WORKSPACE_TYPES.map((t) => (
            <option key={t} value={t}>{TYPE_LABELS[t] || t.replace(/_/g, ' ')}</option>
          ))}
        </select>
        {(cityInput || type !== 'all') && (
          <button
            className="btn-ghost text-xs text-slate-500"
            onClick={() => { setCityInput(''); setType('all') }}
          >
            Clear filters
          </button>
        )}
      </div>

      {error && <ErrorState message={error.message} onRetry={reload} />}

      {!error && (
        <>
          {loading && (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="card p-4 animate-pulse">
                  <div className="h-4 bg-slate-100 rounded w-3/4 mb-2" />
                  <div className="h-3 bg-slate-100 rounded w-1/2 mb-4" />
                  <div className="h-3 bg-slate-100 rounded w-full" />
                </div>
              ))}
            </div>
          )}

          {!loading && (!workspaces || workspaces.length === 0) && (
            <EmptyState
              title="No workspaces match"
              description="Try clearing filters or add new inventory."
            />
          )}

          {!loading && workspaces?.length > 0 && (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {workspaces.map((w) => (
                <Link
                  key={w.id}
                  to={`/workspaces/${w.id}`}
                  className="card-hover p-4 flex flex-col gap-3"
                >
                  {/* Header */}
                  <div>
                    <p className="font-semibold text-slate-900 text-sm leading-snug">{w.name}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{w.city}</p>
                  </div>

                  {/* Badges */}
                  <div className="flex flex-wrap gap-1.5">
                    <span className={`badge ${TYPE_STYLES[w.workspace_type] || 'bg-slate-100 text-slate-600'}`}>
                      {TYPE_LABELS[w.workspace_type] || w.workspace_type.replace(/_/g, ' ')}
                    </span>
                    <span className="badge bg-slate-100 text-slate-600">
                      {w.capacity_min}–{w.capacity_max} seats
                    </span>
                    <span className="badge bg-amber-50 text-amber-700">★ {w.rating}</span>
                  </div>

                  {/* Price */}
                  <div className="flex items-baseline gap-1">
                    <span className="font-bold text-slate-900 text-sm">
                      ₹{w.price_per_seat_inr.toLocaleString('en-IN')}
                    </span>
                    <span className="text-xs text-slate-500">
                      {w.workspace_type === 'day_pass' || w.workspace_type === 'meeting_room'
                        ? '/ day'
                        : '/ seat / month'}
                    </span>
                  </div>

                  {/* Amenities preview */}
                  {w.amenities?.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {w.amenities.slice(0, 3).map((a) => (
                        <span key={a} className="badge bg-slate-50 text-slate-500 ring-1 ring-slate-200">{a}</span>
                      ))}
                      {w.amenities.length > 3 && (
                        <span className="badge bg-slate-50 text-slate-400">+{w.amenities.length - 3} more</span>
                      )}
                    </div>
                  )}

                  {/* Available from */}
                  <p className="text-xs text-slate-400">
                    Available: {w.available_from}
                  </p>
                </Link>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

function WorkspaceForm({ onDone }) {
  const [form, setForm] = useState(emptyForm)
  const [saving, setSaving] = useState(false)
  const { push } = useToast()

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await api.createWorkspace({
        ...form,
        capacity_min: Number(form.capacity_min),
        capacity_max: Number(form.capacity_max),
        price_per_seat_inr: Number(form.price_per_seat_inr),
        rating: Number(form.rating),
        daily_capacity: form.daily_capacity ? Number(form.daily_capacity) : null,
        amenities: form.amenities.split(',').map((a) => a.trim()).filter(Boolean),
      })
      push('Workspace added successfully')
      onDone()
    } catch (err) {
      push(err.message || 'Failed to add workspace', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="card p-5">
      <p className="section-title mb-4">Add Workspace</p>
      <form onSubmit={submit} className="grid sm:grid-cols-2 gap-4">
        <div>
          <label className="label">Name *</label>
          <input required className="input" placeholder="Centre name" value={form.name} onChange={set('name')} />
        </div>
        <div>
          <label className="label">City *</label>
          <input required className="input" placeholder="Mumbai" value={form.city} onChange={set('city')} />
        </div>
        <div>
          <label className="label">Workspace type</label>
          <select className="input" value={form.workspace_type} onChange={set('workspace_type')}>
            {WORKSPACE_TYPES.map((t) => (
              <option key={t} value={t}>{TYPE_LABELS[t]}</option>
            ))}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">Min seats</label>
            <input type="number" min="1" required className="input" value={form.capacity_min} onChange={set('capacity_min')} />
          </div>
          <div>
            <label className="label">Max seats</label>
            <input type="number" min="1" required className="input" value={form.capacity_max} onChange={set('capacity_max')} />
          </div>
        </div>
        <div>
          <label className="label">Price / seat / month (₹)</label>
          <input type="number" min="0" required className="input" value={form.price_per_seat_inr} onChange={set('price_per_seat_inr')} />
        </div>
        <div>
          <label className="label">Daily capacity <span className="text-slate-400">(day pass / meeting room)</span></label>
          <input type="number" min="0" className="input" placeholder="e.g. 20" value={form.daily_capacity} onChange={set('daily_capacity')} />
        </div>
        <div>
          <label className="label">Available from</label>
          <input className="input" placeholder="immediate / 30 days" value={form.available_from} onChange={set('available_from')} />
        </div>
        <div>
          <label className="label">Rating (0-5)</label>
          <input type="number" step="0.1" min="0" max="5" className="input" value={form.rating} onChange={set('rating')} />
        </div>
        <div className="sm:col-span-2">
          <label className="label">Amenities <span className="text-slate-400">(comma-separated)</span></label>
          <input className="input" placeholder="wifi, parking, cafeteria, AC" value={form.amenities} onChange={set('amenities')} />
        </div>
        <div className="sm:col-span-2 flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button type="button" onClick={onDone} className="btn-secondary">Cancel</button>
          <button type="submit" disabled={saving} className="btn-primary">
            {saving ? 'Saving…' : 'Save workspace'}
          </button>
        </div>
      </form>
    </div>
  )
}
