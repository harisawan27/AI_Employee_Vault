'use client';

import { useQuery } from '@tanstack/react-query';
import { getDashboardStats } from '@/lib/api';
import {
  ClipboardCheck,
  CheckCircle,
  Inbox,
  Activity,
  Circle,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: number;
  icon: any;
  color: string;
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-3xl font-bold mt-1">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => getDashboardStats().then((r) => r.data),
    refetchInterval: 30_000,
  });

  if (isLoading || !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-4 border-brand-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Pending Tasks" value={stats.pending_tasks} icon={Inbox} color="bg-orange-500" />
        <StatCard label="Approvals Waiting" value={stats.approvals_waiting} icon={ClipboardCheck} color="bg-blue-500" />
        <StatCard label="Done Today" value={stats.done_today} icon={CheckCircle} color="bg-green-500" />
        <StatCard label="Active Services" value={stats.services?.filter((s: any) => s.status === 'active').length || 0} icon={Activity} color="bg-purple-500" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Activity Timeline */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold mb-4">Recent Activity</h2>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {stats.timeline?.length === 0 && (
              <p className="text-gray-400 text-sm">No recent activity</p>
            )}
            {stats.timeline?.map((event: any, i: number) => (
              <div key={i} className="flex items-start gap-3 text-sm">
                <div className={`mt-1 w-2 h-2 rounded-full flex-shrink-0 ${
                  event.status === 'success' ? 'bg-green-500' :
                  event.status === 'error' ? 'bg-red-500' : 'bg-gray-400'
                }`} />
                <div className="flex-1 min-w-0">
                  <p className="text-gray-900 truncate">
                    <span className="font-medium">{event.category}</span>
                    {' / '}
                    {event.action}
                  </p>
                  <p className="text-gray-400 text-xs">
                    {event.timestamp ? formatDistanceToNow(new Date(event.timestamp), { addSuffix: true }) : ''}
                  </p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  event.status === 'success' ? 'bg-green-100 text-green-700' :
                  event.status === 'error' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'
                }`}>
                  {event.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Service Health */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold mb-4">Service Health</h2>
          <div className="space-y-3">
            {stats.services?.map((svc: any) => (
              <div key={svc.name} className="flex items-center justify-between py-2">
                <div className="flex items-center gap-3">
                  <Circle
                    className={`w-3 h-3 ${
                      svc.status === 'active' ? 'text-green-500 fill-green-500' :
                      svc.status === 'stale' ? 'text-yellow-500 fill-yellow-500' :
                      'text-gray-400 fill-gray-400'
                    }`}
                  />
                  <span className="text-sm font-medium">{svc.name.replace(/_/g, ' ')}</span>
                </div>
                <span className="text-xs text-gray-400">
                  {svc.last_update_minutes_ago !== null
                    ? `${Math.round(svc.last_update_minutes_ago)}m ago`
                    : 'No log file'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
