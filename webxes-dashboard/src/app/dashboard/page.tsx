'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { getDashboardStats } from '@/lib/api';
import {
  ClipboardCheck,
  CheckCircle,
  Inbox,
  Activity,
  Circle,
  AlertCircle,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

function StatCard({
  label,
  value,
  icon: Icon,
  color,
  href,
}: {
  label: string;
  value: number;
  icon: any;
  color: string;
  href: string;
}) {
  return (
    <Link
      href={href}
      className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 cursor-pointer hover:shadow-md transition group"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-3xl font-bold mt-1">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${color} group-hover:scale-110 transition-transform`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </Link>
  );
}

const categoryLinks: Record<string, string> = {
  approval: '/dashboard/approvals',
  email: '/dashboard/inbox',
  social: '/dashboard/social',
  audit: '/dashboard/audit',
  inbox: '/dashboard/inbox',
};

function getCategoryLink(category: string): string {
  const lower = category.toLowerCase();
  for (const [key, path] of Object.entries(categoryLinks)) {
    if (lower.includes(key)) return path;
  }
  return '/dashboard/audit';
}

export default function DashboardPage() {
  const { data: stats, isLoading, isError } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => getDashboardStats().then((r) => r.data),
    refetchInterval: 30_000,
  });

  if (isError) {
    return (
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
        <div className="bg-white rounded-xl shadow-sm border border-red-100 p-12 text-center">
          <AlertCircle className="w-12 h-12 text-red-300 mx-auto mb-3" />
          <p className="text-gray-600 font-medium">Failed to load dashboard data</p>
          <p className="text-sm text-gray-400 mt-1">Check that the API server is running</p>
        </div>
      </div>
    );
  }

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
        <StatCard label="Pending Tasks" value={stats.pending_tasks} icon={Inbox} color="bg-orange-500" href="/dashboard/inbox" />
        <StatCard label="Approvals Waiting" value={stats.approvals_waiting} icon={ClipboardCheck} color="bg-blue-500" href="/dashboard/approvals" />
        <StatCard label="Done Today" value={stats.done_today} icon={CheckCircle} color="bg-green-500" href="/dashboard/audit" />
        <StatCard label="Active Services" value={stats.services?.filter((s: any) => s.status === 'active').length || 0} icon={Activity} color="bg-purple-500" href="#services" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Activity Timeline */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Recent Activity</h2>
            <Link href="/dashboard/audit" className="text-sm text-brand-600 hover:text-brand-700 font-medium">
              View all
            </Link>
          </div>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {stats.timeline?.length === 0 && (
              <p className="text-gray-400 text-sm">No recent activity</p>
            )}
            {stats.timeline?.map((event: any, i: number) => (
              <Link
                key={i}
                href={getCategoryLink(event.category)}
                className="flex items-start gap-3 text-sm hover:bg-gray-50 rounded-lg p-1.5 -m-1.5 transition"
              >
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
              </Link>
            ))}
          </div>
        </div>

        {/* Service Health */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6" id="services">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Service Health</h2>
            <span className="text-xs text-gray-400">
              {stats.services?.filter((s: any) => s.status === 'active').length || 0}/{stats.services?.length || 0} active
            </span>
          </div>
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
