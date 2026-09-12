import React, { useState, useEffect } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'

// Inline SVG icons — 20x20, strokeWidth 1.75, matching design system
const Icons = {
  Dashboard: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
    </svg>
  ),
  Chat: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
    </svg>
  ),
  Leads: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 00-3-3.87" />
      <path d="M16 3.13a4 4 0 010 7.75" />
    </svg>
  ),
  Workspaces: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
      <polyline points="9,22 9,12 15,12 15,22" />
    </svg>
  ),
  Bookings: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="4" width="18" height="18" rx="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
      <path d="M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01" />
    </svg>
  ),
  Tours: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12,6 12,12 16,14" />
    </svg>
  ),
  Handoffs: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="17,1 21,5 17,9" />
      <path d="M3 11V9a4 4 0 014-4h14" />
      <polyline points="7,23 3,19 7,15" />
      <path d="M21 13v2a4 4 0 01-4 4H3" />
    </svg>
  ),
  Analytics: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10" />
      <line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" />
      <line x1="2" y1="20" x2="22" y2="20" />
    </svg>
  ),
  Menu: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round">
      <path d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  ),
  Close: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round">
      <path d="M6 6l12 12M18 6L6 18" />
    </svg>
  ),
  Bolt: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
    </svg>
  ),
}

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: Icons.Dashboard, end: true },
  { to: '/chat', label: 'Chat', icon: Icons.Chat },
  { to: '/leads', label: 'Leads', icon: Icons.Leads },
  { to: '/workspaces', label: 'Workspaces', icon: Icons.Workspaces },
  { to: '/bookings', label: 'Bookings', icon: Icons.Bookings },
  { to: '/tours', label: 'Tours', icon: Icons.Tours },
  { to: '/handoffs', label: 'Handoffs', icon: Icons.Handoffs },
  { to: '/analytics', label: 'Analytics', icon: Icons.Analytics },
]

function NavItems({ onNavigate }) {
  return (
    <nav className="flex flex-col gap-0.5 px-2">
      {NAV_ITEMS.map((item) => {
        const Icon = item.icon
        return (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={onNavigate}
            className={({ isActive }) =>
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ' +
              (isActive
                ? 'bg-brand-500 text-white shadow-sm'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900')
            }
          >
            {({ isActive }) => (
              <>
                <span className={isActive ? 'text-white' : 'text-slate-400'}>
                  <Icon />
                </span>
                {item.label}
              </>
            )}
          </NavLink>
        )
      })}
    </nav>
  )
}

export default function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()

  // Close mobile menu on route change
  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  // Close on Escape
  useEffect(() => {
    if (!mobileOpen) return
    const handler = (e) => { if (e.key === 'Escape') setMobileOpen(false) }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [mobileOpen])

  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex md:w-60 md:flex-col md:fixed md:inset-y-0 border-r border-slate-200 bg-white">
        {/* Brand header */}
        <div className="h-14 flex items-center px-4 border-b border-slate-200 shrink-0">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-md bg-brand-500 flex items-center justify-center">
              <span className="text-white font-bold text-sm">Q</span>
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="font-semibold text-slate-900 text-sm">Qdesq</span>
              <span className="text-[11px] font-semibold text-brand-600 tracking-wide uppercase bg-brand-50 px-1.5 py-0.5 rounded">Sales+</span>
            </div>
          </div>
        </div>

        {/* Nav */}
        <div className="flex-1 overflow-y-auto py-3">
          <NavItems />
        </div>

        {/* Sidebar footer */}
        <div className="px-4 py-3 border-t border-slate-100 shrink-0">
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded-full bg-brand-100 flex items-center justify-center shrink-0">
              <span className="text-brand-600 text-[10px]">
                <Icons.Bolt />
              </span>
            </div>
            <div className="min-w-0">
              <p className="text-[11px] font-medium text-slate-700 truncate">Powered by Nia</p>
              <p className="text-[10px] text-slate-400">AI Sales Agent</p>
            </div>
            <span className="ml-auto flex items-center gap-1 shrink-0">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
              <span className="text-[10px] text-slate-400">Live</span>
            </span>
          </div>
        </div>
      </aside>

      {/* Mobile top bar */}
      <header className="md:hidden sticky top-0 z-40 h-14 flex items-center justify-between px-4 bg-white border-b border-slate-200 shadow-sm">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-md bg-brand-500 flex items-center justify-center">
            <span className="text-white font-bold text-sm">Q</span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="font-semibold text-slate-900 text-sm">Qdesq</span>
            <span className="text-[11px] font-semibold text-brand-600 tracking-wide uppercase bg-brand-50 px-1.5 py-0.5 rounded">Sales+</span>
          </div>
        </div>
        <button
          aria-label="Open menu"
          onClick={() => setMobileOpen(true)}
          className="h-9 w-9 flex items-center justify-center rounded-lg hover:bg-slate-100 text-slate-600"
        >
          <Icons.Menu />
        </button>
      </header>

      {/* Mobile slide-over menu */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-50">
          <div className="absolute inset-0 bg-slate-900/50" onClick={() => setMobileOpen(false)} />
          <div className="absolute inset-y-0 left-0 w-72 bg-white shadow-2xl flex flex-col animate-slide-in">
            <div className="h-14 flex items-center justify-between px-4 border-b border-slate-200">
              <div className="flex items-center gap-2">
                <div className="h-7 w-7 rounded-md bg-brand-500 flex items-center justify-center">
                  <span className="text-white font-bold text-sm">Q</span>
                </div>
                <span className="font-semibold text-slate-900 text-sm">Qdesq Sales+</span>
              </div>
              <button
                aria-label="Close menu"
                onClick={() => setMobileOpen(false)}
                className="h-9 w-9 flex items-center justify-center rounded-lg hover:bg-slate-100 text-slate-600"
              >
                <Icons.Close />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto py-3">
              <NavItems onNavigate={() => setMobileOpen(false)} />
            </div>
            <div className="px-4 py-3 border-t border-slate-100">
              <div className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
                <span className="text-xs text-slate-500">Nia AI Agent — Live</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main content */}
      <main className="flex-1 md:ml-60 min-w-0">
        <div className="max-w-screen-xl mx-auto w-full p-4 md:p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
