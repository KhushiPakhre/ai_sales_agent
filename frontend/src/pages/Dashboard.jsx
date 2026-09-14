import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Users, 
  Flame, 
  CalendarCheck, 
  Compass, 
  UserCheck, 
  TrendingUp,
  ArrowRight,
  MessageSquare,
  Sparkles,
  Building2
} from 'lucide-react';
import MetricCard from '../components/MetricCard';
import { getAnalyticsOverview, getLeads, getHandoffs, getWorkspaces } from '../api/client';

export default function Dashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState({
    leads: [],
    handoffs: [],
    workspaces: [],
    analytics: null,
    loading: true,
    error: null
  });

  useEffect(() => {
    async function loadData() {
      try {
        const [leads, handoffs, workspaces, analytics] = await Promise.all([
          getLeads(),
          getHandoffs(),
          getWorkspaces(),
          getAnalyticsOverview()
        ]);
        setData({
          leads: Array.isArray(leads) ? leads : [],
          handoffs: Array.isArray(handoffs) ? handoffs : [],
          workspaces: Array.isArray(workspaces) ? workspaces : [],
          analytics,
          loading: false,
          error: null
        });
      } catch (err) {
        setData(prev => ({ ...prev, loading: false, error: err.message }));
      }
    }
    loadData();
  }, []);

  if (data.loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (data.error) {
    return (
      <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-sm">
        Failed to load dashboard data: {data.error}
      </div>
    );
  }

  const leads = data.leads;
  const hotLeads = leads.filter(l => (l.score_category || l.scoreCategory || '').toLowerCase() === 'hot');
  const warmLeads = leads.filter(l => (l.score_category || l.scoreCategory || '').toLowerCase() === 'warm');
  const coldLeads = leads.filter(l => (l.score_category || l.scoreCategory || '').toLowerCase() === 'cold');

  const pendingHandoffs = data.handoffs.filter(h => h.status === 'pending');
  const analyticsData = data.analytics || {};

  const handleKeyDown = (e, callback) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      callback();
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-slate-500 text-sm mt-0.5">Overview of sales AI activity and pipeline health</p>
        </div>
      </div>

      {/* Top Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <MetricCard
          title="Total Leads"
          value={leads.length}
          icon={Users}
          trend={+12}
          color="indigo"
          onClick={() => navigate('/leads')}
        />
        <MetricCard
          title="Hot Leads"
          value={hotLeads.length}
          icon={Flame}
          color="rose"
          onClick={() => navigate('/leads?score=hot')}
        />
        <MetricCard
          title="Bookings"
          value={analyticsData.total_bookings ?? 0}
          icon={CalendarCheck}
          trend={+8}
          color="emerald"
          onClick={() => navigate('/bookings')}
        />
        <MetricCard
          title="Tours Scheduled"
          value={analyticsData.total_tours ?? 0}
          icon={Compass}
          color="amber"
          onClick={() => navigate('/tours')}
        />
        <MetricCard
          title="Pending Handoffs"
          value={pendingHandoffs.length}
          icon={UserCheck}
          color="violet"
          onClick={() => navigate('/handoffs?status=pending')}
        />
        <MetricCard
          title="Conversion Rate"
          value={`${analyticsData.conversion_rate ?? 0}%`}
          icon={TrendingUp}
          trend={+2.4}
          color="sky"
          onClick={() => navigate('/analytics')}
        />
      </div>

      {/* Main Grid: Pipeline + Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pipeline Breakdown */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900 mb-4">Lead Pipeline</h2>
          <div className="space-y-4">
            <div
              role="button"
              tabIndex={0}
              onClick={() => navigate('/leads?score=hot')}
              onKeyDown={(e) => handleKeyDown(e, () => navigate('/leads?score=hot'))}
              className="p-2 -mx-2 rounded-lg cursor-pointer hover:bg-slate-50 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
            >
              <div className="flex justify-between text-sm mb-1.5">
                <span className="font-medium text-slate-700 flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                  Hot Leads
                </span>
                <span className="text-slate-500 font-medium">
                  {hotLeads.length} ({leads.length ? Math.round((hotLeads.length / leads.length) * 100) : 0}%)
                </span>
              </div>
              <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                <div 
                  className="bg-rose-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${leads.length ? (hotLeads.length / leads.length) * 100 : 0}%` }}
                />
              </div>
            </div>

            <div
              role="button"
              tabIndex={0}
              onClick={() => navigate('/leads?score=warm')}
              onKeyDown={(e) => handleKeyDown(e, () => navigate('/leads?score=warm'))}
              className="p-2 -mx-2 rounded-lg cursor-pointer hover:bg-slate-50 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
            >
              <div className="flex justify-between text-sm mb-1.5">
                <span className="font-medium text-slate-700 flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                  Warm Leads
                </span>
                <span className="text-slate-500 font-medium">
                  {warmLeads.length} ({leads.length ? Math.round((warmLeads.length / leads.length) * 100) : 0}%)
                </span>
              </div>
              <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                <div 
                  className="bg-amber-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${leads.length ? (warmLeads.length / leads.length) * 100 : 0}%` }}
                />
              </div>
            </div>

            <div
              role="button"
              tabIndex={0}
              onClick={() => navigate('/leads?score=cold')}
              onKeyDown={(e) => handleKeyDown(e, () => navigate('/leads?score=cold'))}
              className="p-2 -mx-2 rounded-lg cursor-pointer hover:bg-slate-50 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
            >
              <div className="flex justify-between text-sm mb-1.5">
                <span className="font-medium text-slate-700 flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-sky-500"></span>
                  Cold Leads
                </span>
                <span className="text-slate-500 font-medium">
                  {coldLeads.length} ({leads.length ? Math.round((coldLeads.length / leads.length) * 100) : 0}%)
                </span>
              </div>
              <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden">
                <div 
                  className="bg-sky-500 h-full rounded-full transition-all duration-500"
                  style={{ width: `${leads.length ? (coldLeads.length / leads.length) * 100 : 0}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900 mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <button
              onClick={() => navigate('/chat')}
              className="w-full flex items-center justify-between p-3 rounded-lg border border-slate-200 hover:border-indigo-200 hover:bg-indigo-50/50 text-slate-700 hover:text-indigo-600 font-medium text-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
            >
              <span className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-indigo-500" />
                Start a conversation
              </span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => navigate('/leads')}
              className="w-full flex items-center justify-between p-3 rounded-lg border border-slate-200 hover:border-indigo-200 hover:bg-indigo-50/50 text-slate-700 hover:text-indigo-600 font-medium text-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
            >
              <span className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-500" />
                View all leads
              </span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => navigate('/handoffs?status=pending')}
              className="w-full flex items-center justify-between p-3 rounded-lg border border-slate-200 hover:border-indigo-200 hover:bg-indigo-50/50 text-slate-700 hover:text-indigo-600 font-medium text-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
            >
              <span className="flex items-center gap-2">
                <UserCheck className="w-4 h-4 text-violet-500" />
                Review handoffs
              </span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Workspace Utilization */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm">
        <h2 className="text-base font-semibold text-slate-900 mb-4 flex items-center gap-2">
          <Building2 className="w-5 h-5 text-indigo-600" />
          Workspace Utilization
        </h2>
        {data.workspaces.length === 0 ? (
          <div className="p-4 text-sm text-slate-500 bg-slate-50 rounded-lg border border-slate-100">
            No workspace data available.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {data.workspaces.slice(0, 4).map((ws) => (
              <div
                key={ws.id}
                role="button"
                tabIndex={0}
                onClick={() => navigate(ws.id ? `/workspaces/${ws.id}` : '/workspaces')}
                onKeyDown={(e) => handleKeyDown(e, () => navigate(ws.id ? `/workspaces/${ws.id}` : '/workspaces'))}
                className="p-4 rounded-lg border border-slate-100 bg-slate-50/50 cursor-pointer hover:border-indigo-200 hover:shadow-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
              >
                <div className="font-medium text-slate-800 text-sm truncate">{ws.name}</div>
                <div className="text-xs text-slate-500 mt-0.5">{ws.city || 'Location'}</div>
                <div className="mt-3 flex items-center justify-between">
                  <span className="text-xs text-slate-500">Active bookings</span>
                  <span className="text-sm font-semibold text-indigo-600">{ws.active_bookings ?? 0}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
