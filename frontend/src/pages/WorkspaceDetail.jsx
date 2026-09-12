import React, { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api, ApiError } from '../api/client.js'
import { useApiData } from '../hooks/useApiData.js'
import { ErrorState, SkeletonCard, EmptyState } from '../components/Feedback.jsx'
import { useToast } from '../components/Toast.jsx'
import PageHeader from '../components/PageHeader.jsx'

const TYPE_STYLES = {
  hot_desk: 'bg-blue-50 text-blue-700',
  dedicated_desk: 'bg-violet-50 text-violet-700',
  private_cabin: 'bg-brand-50 text-brand-700',
  managed_office: 'bg-emerald-50 text-emerald-700',
  day_pass: 'bg-amber-50 text-amber-700',
  meeting_room: 'bg-orange-50 text-orange-700',
}

function Info({ label, value }) {
  return (
    <div>
      <p className="field-label">{label}</p>
      <p className="field-value">{value ?? '—'}</p>
    </div>
  )
}

export default function WorkspaceDetail() {
  const { workspaceId } = useParams()
  const { data: ws, loading, error, reload } = useApiData(() => api.getWorkspace(workspaceId), [workspaceId])
  const [editing, setEditing] = useState(false)

  if (loading) return <div className="max-w-2xl"><SkeletonCard lines={4} /></div>
  if (error) {
    const notFound = error instanceof ApiError && error.status === 404
    return notFound
      ? <EmptyState title="Workspace not found" />
      : <ErrorState message={error.message} onRetry={reload} />
  }

  const priceLabel = (ws.workspace_type === 'day_pass' || ws.workspace_type === 'meeting_room') ? '/ day' : '/ seat / month'

  return (
    <div className="max-w-2xl">
      <div className="mb-2">
        <Link to="/workspaces" className="text-xs text-slate-400 hover:text-slate-700 flex items-center gap-1">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M15 18l-6-6 6-6" /></svg>
          Workspaces
        </Link>
      </div>

      <PageHeader
        title={ws.name}
        subtitle={`${ws.city} · ${ws.workspace_type.replace(/_/g, ' ')}`}
        actions={
          <button className="btn-secondary" onClick={() => setEditing((e) => !e)}>
            {editing ? 'Cancel' : 'Edit'}
          </button>
        }
      />

      {editing ? (
        <EditForm ws={ws} onDone={() => { setEditing(false); reload() }} />
      ) : (
        <div className="space-y-4">
          <div className="card p-5">
            <div className="grid grid-cols-2 gap-5">
              <Info label="Price" value={`₹${ws.price_per_seat_inr.toLocaleString('en-IN')} ${priceLabel}`} />
              <Info label="Capacity" value={`${ws.capacity_min}–${ws.capacity_max} seats`} />
              <Info label="Rating" value={`★ ${ws.rating}`} />
              <Info label="Available from" value={ws.available_from} />
              {ws.daily_capacity != null && <Info label="Daily capacity" value={ws.daily_capacity} />}
            </div>

            {ws.amenities?.length > 0 && (
              <div className="mt-5 pt-4 border-t border-slate-100">
                <p className="field-label mb-2">Amenities</p>
                <div className="flex flex-wrap gap-1.5">
                  {ws.amenities.map((a) => (
                    <span key={a} className="badge bg-slate-100 text-slate-600 ring-1 ring-slate-200">{a}</span>
                  ))}
                </div>
              </div>
            )}

            <div className="mt-4">
              <span className={`badge ${TYPE_STYLES[ws.workspace_type] || 'bg-slate-100 text-slate-600'}`}>
                {ws.workspace_type.replace(/_/g, ' ')}
              </span>
            </div>
          </div>

          {(ws.workspace_type === 'day_pass' || ws.workspace_type === 'meeting_room') && (
            <AvailabilityChecker workspaceId={ws.id} />
          )}
        </div>
      )}
    </div>
  )
}

function AvailabilityChecker({ workspaceId }) {
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [result, setResult] = useState(null)
  const [checking, setChecking] = useState(false)
  const { push } = useToast()

  const check = async () => {
    setChecking(true)
    setResult(null)
    try {
      setResult(await api.getAvailability(workspaceId, { date }))
    } catch (err) {
      push(err.message || 'Could not check availability', 'error')
    } finally {
      setChecking(false)
    }
  }

  return (
    <div className="card p-5">
      <p className="section-title mb-4">Check availability</p>
      <div className="flex flex-col sm:flex-row gap-2">
        <input
          type="date"
          className="input sm:max-w-[200px]"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />
        <button className="btn-primary" onClick={check} disabled={checking}>
          {checking ? 'Checking…' : 'Check'}
        </button>
      </div>
      {result && (
        <div className={`mt-4 flex items-center gap-2 text-sm font-medium ${
          result.is_available ? 'text-emerald-600' : 'text-red-600'
        }`}>
          <span className={`h-2 w-2 rounded-full ${result.is_available ? 'bg-emerald-500' : 'bg-red-500'}`} />
          {result.is_available
            ? `${result.slots_remaining} of ${result.daily_capacity} slots available on ${result.date}`
            : `Fully booked on ${result.date}`}
        </div>
      )}
    </div>
  )
}

function EditForm({ ws, onDone }) {
  const [form, setForm] = useState({
    name: ws.name, city: ws.city,
    price_per_seat_inr: ws.price_per_seat_inr,
    capacity_min: ws.capacity_min, capacity_max: ws.capacity_max,
    available_from: ws.available_from, rating: ws.rating,
    amenities: ws.amenities.join(', '),
  })
  const [saving, setSaving] = useState(false)
  const { push } = useToast()
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await api.updateWorkspace(ws.id, {
        ...form,
        price_per_seat_inr: Number(form.price_per_seat_inr),
        capacity_min: Number(form.capacity_min),
        capacity_max: Number(form.capacity_max),
        rating: Number(form.rating),
        amenities: form.amenities.split(',').map((a) => a.trim()).filter(Boolean),
      })
      push('Workspace updated')
      onDone()
    } catch (err) {
      push(err.message || 'Update failed', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="card p-5">
      <p className="section-title mb-4">Edit Workspace</p>
      <form onSubmit={submit} className="grid sm:grid-cols-2 gap-4">
        <div><label className="label">Name</label><input className="input" value={form.name} onChange={set('name')} /></div>
        <div><label className="label">City</label><input className="input" value={form.city} onChange={set('city')} /></div>
        <div><label className="label">Price / seat</label><input type="number" className="input" value={form.price_per_seat_inr} onChange={set('price_per_seat_inr')} /></div>
        <div className="grid grid-cols-2 gap-3">
          <div><label className="label">Min seats</label><input type="number" className="input" value={form.capacity_min} onChange={set('capacity_min')} /></div>
          <div><label className="label">Max seats</label><input type="number" className="input" value={form.capacity_max} onChange={set('capacity_max')} /></div>
        </div>
        <div><label className="label">Available from</label><input className="input" value={form.available_from} onChange={set('available_from')} /></div>
        <div><label className="label">Rating</label><input type="number" step="0.1" className="input" value={form.rating} onChange={set('rating')} /></div>
        <div className="sm:col-span-2"><label className="label">Amenities</label><input className="input" value={form.amenities} onChange={set('amenities')} /></div>
        <div className="sm:col-span-2 flex justify-end gap-2 pt-2 border-t border-slate-100">
          <button type="button" onClick={onDone} className="btn-secondary">Cancel</button>
          <button className="btn-primary" disabled={saving}>{saving ? 'Saving…' : 'Save changes'}</button>
        </div>
      </form>
    </div>
  )
}
