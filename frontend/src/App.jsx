import React from 'react'
import { Routes, Route } from 'react-router-dom'
import AppLayout from './components/AppLayout.jsx'
import { ToastProvider } from './components/Toast.jsx'

import Dashboard from './pages/Dashboard.jsx'
import ChatPage from './pages/ChatPage.jsx'
import Leads from './pages/Leads.jsx'
import LeadDetail from './pages/LeadDetail.jsx'
import Workspaces from './pages/Workspaces.jsx'
import WorkspaceDetail from './pages/WorkspaceDetail.jsx'
import Bookings from './pages/Bookings.jsx'
import Tours from './pages/Tours.jsx'
import Handoffs from './pages/Handoffs.jsx'
import Analytics from './pages/Analytics.jsx'

export default function App() {
  return (
    <ToastProvider>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/chat/:leadId" element={<ChatPage />} />
          <Route path="/leads" element={<Leads />} />
          <Route path="/leads/:leadId" element={<LeadDetail />} />
          <Route path="/workspaces" element={<Workspaces />} />
          <Route path="/workspaces/:workspaceId" element={<WorkspaceDetail />} />
          <Route path="/bookings" element={<Bookings />} />
          <Route path="/tours" element={<Tours />} />
          <Route path="/handoffs" element={<Handoffs />} />
          <Route path="/analytics" element={<Analytics />} />
        </Route>
      </Routes>
    </ToastProvider>
  )
}
