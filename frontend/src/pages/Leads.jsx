import React, { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client.js'
import { useApiData } from '../hooks/useApiData.js'
import { TierBadge, StatusBadge, EmptyState, ErrorState, SkeletonRows } from '../components/Feedback.jsx'
import PageHeader from '../components/PageHeader.jsx'

const SORT_OPTIONS = [
  { value: 'last_activity_desc', label: 'Most recent' },
  { value: 'tier', label: 'Tier: Hot first' },
  { value: 'team_size_desc', label: 'Team size: Largest' },
]

const TIER_RANK = { hot: 0, warm: 1, cold: 2 }

function fmtDate(ts) {
  if (!ts) return '\u2014'
  try {
    return new Date(ts).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
  } catch { return '\u2014' }
}

function fmtBudget(v) {
  if (!v) return '\u2014'
  return `\u20b9${Number(v).toLocaleString('en-IN')}`
}

export default function Leads() {
  const { data: leads, loading, error, reload } = useApiData(() => api.listLeads(), [])
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [tierFilter, setTierFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sortBy, setSortBy] = useState('last_activity_desc')

  const filtered = useMemo(() => {
    if (!leads) return []
    let result = leads.filter((l) => {
      if (tierFilter !== 'all' && l.tier !== tierFilter) return false
      if (statusFilter !== 'all' && l.status !== statusFilter) return false
      if (!search.trim()) return true
      const q = search.toLowerCase()
      return (
        l.lead_id.toLowerCase().includes(q) ||
        (l.contact_name || '').toLowerCase().includes(q) ||
        (l.company_name || '').toLowerCase().includes(q) ||
        (l.location || '').toLowerCase().includes(q)
      )
    })
    result = [...result].sort((a, b) => {
      if (sortBy === 'tier') return (TIER_RANK[a.tier] ?? 3) - (TIER_RANK[b.tier] ?? 3)
      if (sortBy === 'team_size_desc') return (b.team_size || 0) - (a.team_size || 0)
      return new Date(b.last_activity || 0) - new Date(a.last_activity || 0)
    })
    return result
  }, [leads, search, tierFilter, statusFilter, sortBy])

  const hasFilters = search || tierFilter !== 'all' || statusFilter !== 'all'
  const clearFilters = () => { setSearch(''); setTierFilter('all'); setStatusFilter('all') }

  // Get unique statuses for filter dropdown
  const statuses = useMemo(() => {
    if (!leads) return []
    return [...new Set(leads.map(l => l.status).filter(Boolean))]
  }, [leads])

  return (
    <div>
      <PageHeader
        title="Leads"
        subtitle="Your CRM — all leads qualified by Nia"
        badge={leads ? `${leads.length} total` : undefined}
      />

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-2 mb-4">
        <input
          className="input sm:max-w-xs"
          placeholder="Search name, company, city…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select className="input sm:max-w-[140px]" value={tierFilter} onChange={(e) => setTierFilter(e.target.value)}>
          <option value="all">All tiers</option>
          <option value="hot">Hot</option>
          <option value="warm">Warm</option>
          <option value="cold">Cold</option>
        </select>
        <select className="input sm:max-w-[160px]" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="all">All statuses</option>
          {statuses.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
        </select>
        <select className="input sm:max-w-[180px]" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
          {SORT_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        {hasFilters && (
          <button onClick={clearFilters} className="btn-ghost text-xs text-slate-500 whitespace-nowrap">
            Clear filters
          </button>
        )}
      </div>

      {/* Filtered count */}
      {!loading && leads && hasFilters && (
        <p className="text-xs text-slate-500 mb-3">
          Showing {filtered.length} of {leads.length} leads
        </p>
      )}

      {error && <ErrorState message={error.message} onRetry={reload} />}

      {!error && (
        <div className="card overflow-hidden">
          {loading && <SkeletonRows rows={6} cols={6} />}

          {!loading && filtered.length === 0 && (
            <EmptyState
              title={hasFilters ? 'No leads match your filters' : 'No leads yet'}
              description={hasFilters ? 'Try adjusting your search or filters.' : 'Start a chat with a lead to see them appear here.'}
              action={hasFilters ? <button onClick={clearFilters} className="btn-secondary">Clear filters</button> : undefined}
            />
          )}

          {!loading && filtered.length > 0 && (
            <>
              {/* Desktop table */}
              <table className="hidden md:table w-full text-sm">
                <thead className="bg-slate-50 border-b border-slate-100">
                  <tr>
                    <th className="text-left text-xs font-medium text-slate-500 px-5 py-3">Lead</th>
                    <th className="text-left text-xs font-medium text-slate-500 px-4 py-3">Location</th>
                    <th className="text-left text-xs font-medium text-slate-500 px-4 py-3">Workspace</th>
                    <th className="text-left text-xs font-medium text-slate-500 px-4 py-3">Team</th>
                    <th className="text-left text-xs font-medium text-slate-500 px-4 py-3">Budget</th>
                    <th className="text-left text-xs font-medium text-slate-500 px-4 py-3">Tier</th>
                    <th className="text-left text-xs font-medium text-slate-500 px-4 py-3">Status</th>
                    <th className="text-left text-xs font-medium text-slate-500 px-4 py-3">Last Activity</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filtered.map((l) => (
                    <tr
                      key={l.lead_id}
                      onClick={() => navigate(`/leads/${encodeURIComponent(l.lead_id)}`)}
                      className="hover:bg-slate-50 cursor-pointer transition-colors"
                    >
                      <td className="px-5 py-3.5">
                        <p className="font-medium text-slate-900">{l.contact_name || l.lead_id}</p>
                        {l.company_name && <p className="text-xs text-slate-500 mt-0.5">{l.company_name}</p>}
                      </td>
                      <td className="px-4 py-3.5 text-slate-600">{l.location || '—'}</td>
                      <td className="px-4 py-3.5 text-slate-600">{(l.workspace_type || '—').replace(/_/g, ' ')}</td>
                      <td className="px-4 py-3.5 text-slate-600">{l.team_size ?? '—'}</td>
                      <td className="px-4 py-3.5 text-slate-600">{fmtBudget(l.budget_per_seat)}</td>
                      <td className="px-4 py-3.5"><TierBadge tier={l.tier} /></td>
                      <td className="px-4 py-3.5"><StatusBadge status={l.status} /></td>
                      <td className="px-4 py-3.5 text-slate-500 text-xs">{fmtDate(l.last_activity)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Mobile cards */}
              <div className="md:hidden divide-y divide-slate-100">
                {filtered.map((l) => (
                  <div
                    key={l.lead_id}
                    onClick={() => navigate(`/leads/${encodeURIComponent(l.lead_id)}`)}
                    className="px-4 py-3.5 active:bg-slate-50 cursor-pointer"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="font-medium text-slate-900 text-sm">{l.contact_name || l.lead_id}</p>
                        {l.company_name && <p className="text-xs text-slate-500">{l.company_name}</p>}
                      </div>
                      <TierBadge tier={l.tier} />
                    </div>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {l.location && <span className="badge bg-slate-100 text-slate-600">{l.location}</span>}
                      {l.workspace_type && <span className="badge bg-slate-100 text-slate-600">{l.workspace_type.replace(/_/g, ' ')}</span>}
                      <StatusBadge status={l.status} />
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
