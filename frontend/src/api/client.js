import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getLeads = async () => {
  const res = await api.get('/api/leads');
  return res.data;
};

export const getLead = async (id) => {
  const res = await api.get(`/api/leads/${id}`);
  return res.data;
};

export const getBookings = async () => {
  const res = await api.get('/api/bookings');
  return res.data;
};

export const getTours = async () => {
  const res = await api.get('/api/tours');
  return res.data;
};

export const getHandoffs = async () => {
  const res = await api.get('/api/handoffs');
  return res.data;
};

export const updateHandoffStatus = async (id, status, notes) => {
  const res = await api.patch(`/api/handoffs/${id}`, { status, notes });
  return res.data;
};

export const getWorkspaces = async () => {
  const res = await api.get('/api/workspaces');
  return res.data;
};

export const getAnalyticsOverview = async () => {
  const res = await api.get('/api/analytics/overview');
  return res.data;
};

export const sendMessage = async (message, sessionId = null) => {
  const res = await api.post('/api/chat/message', { message, session_id: sessionId });
  return res.data;
};

export default api;
