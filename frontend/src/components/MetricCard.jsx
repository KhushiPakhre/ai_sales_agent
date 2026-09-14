import React from 'react';

const colorStyles = {
  indigo: 'bg-indigo-50 text-indigo-600 border-indigo-100',
  rose: 'bg-rose-50 text-rose-600 border-rose-100',
  emerald: 'bg-emerald-50 text-emerald-600 border-emerald-100',
  amber: 'bg-amber-50 text-amber-600 border-amber-100',
  violet: 'bg-violet-50 text-violet-600 border-violet-100',
  sky: 'bg-sky-50 text-sky-600 border-sky-100'
};

export default function MetricCard({ title, value, icon: Icon, trend, color = 'indigo', onClick }) {
  const isClickable = typeof onClick === 'function';

  return (
    <div
      onClick={onClick}
      role={isClickable ? 'button' : undefined}
      tabIndex={isClickable ? 0 : undefined}
      onKeyDown={isClickable ? (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick(e);
        }
      } : undefined}
      className={`bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm flex flex-col justify-between ${
        isClickable
          ? 'cursor-pointer hover:border-indigo-300 hover:shadow-md transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500'
          : ''
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="text-slate-500 text-xs font-medium uppercase tracking-wider">{title}</span>
        <div className={`p-2 rounded-lg border ${colorStyles[color] || colorStyles.indigo}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      <div className="mt-4 flex items-baseline justify-between">
        <div className="text-2xl font-bold text-slate-900">{value}</div>
        {trend !== undefined && (
          <span className={`text-xs font-medium ${trend >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
            {trend >= 0 ? `+${trend}%` : `${trend}%`}
          </span>
        )}
      </div>
    </div>
  );
}
