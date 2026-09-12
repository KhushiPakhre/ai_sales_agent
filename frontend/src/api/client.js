const BASE = import.meta.env.VITE_API_BASE_URL || '/api'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function request(path, options = {}) {
  let resp
  try {
    resp = await fetch(`${BASE}${path}`, {
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
      ...options,
    })
  } catch (err) {
    throw new ApiError('Network error - check your connection and try again.', 0)
  }

  if (!resp.ok) {
    let detail = `Request failed (${resp.status})`
    try {
      const body = await resp.json()
      detail = body.detail || detail
    } catch {
      // response wasn't JSON - keep the generic message
    }
    throw new ApiError(detail, resp.status)
  }

  if (resp.status === 204) return null
  return resp.json()
}

export const api = {
  // Leads
  listLeads: () => request('/leads'),
  getLead: (leadId) => request(`/leads/${encodeURIComponent(leadId)}`),
  createLead: (payload) => request('/leads', { method: 'POST', body: JSON.stringify(payload) }),
  updateLead: (leadId, payload) =>
    request(`/leads/${encodeURIComponent(leadId)}`, { method: 'PATCH', body: JSON.stringify(payload) }),

  // Chat
  sendMessage: (payload) => request('/chat/message', { method: 'POST', body: JSON.stringify(payload) }),
  getChatHistory: (leadId) => request(`/chat/${encodeURIComponent(leadId)}/history`),

  // Workspaces
  listWorkspaces: (params = {}) => {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v != null && v !== ''))
    const suffix = qs.toString() ? `?${qs}` : ''
    return request(`/workspaces${suffix}`)
  },
  getWorkspace: (id) => request(`/workspaces/${encodeURIComponent(id)}`),
  createWorkspace: (payload) => request('/workspaces', { method: 'POST', body: JSON.stringify(payload) }),
  updateWorkspace: (id, payload) =>
    request(`/workspaces/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify(payload) }),

  // Availability
  getAvailability: (workspaceId, params = {}) => {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v != null && v !== ''))
    const suffix = qs.toString() ? `?${qs}` : ''
    return request(`/workspaces/${encodeURIComponent(workspaceId)}/availability${suffix}`)
  },

  // Bookings
  listBookings: () => request('/bookings'),
  getBooking: (id) => request(`/bookings/${encodeURIComponent(id)}`),
  createBooking: (payload) => request('/bookings', { method: 'POST', body: JSON.stringify(payload) }),
  updateBooking: (id, payload) =>
    request(`/bookings/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify(payload) }),

  // Tours
  listTours: () => request('/tours'),
  getTour: (id) => request(`/tours/${encodeURIComponent(id)}`),
  createTour: (payload) => request('/tours', { method: 'POST', body: JSON.stringify(payload) }),
  updateTour: (id, payload) =>
    request(`/tours/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify(payload) }),

  // Handoffs
  listHandoffs: (pendingOnly = false) => request(`/handoffs${pendingOnly ? '?pending_only=true' : ''}`),
  getHandoff: (leadId) => request(`/handoffs/${encodeURIComponent(leadId)}`),

  // Analytics
  getAnalytics: () => request('/analytics'),
}
