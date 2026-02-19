'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getAuditEvents } from '@/lib/api';
import { Search, ScrollText } from 'lucide-react';
import { format } from 'date-fns';

const statusColors: Record<string, string> = {
  success: 'bg-green-100 text-green-700',
  error: 'bg-red-100 text-red-700',
  pending: 'bg-yellow-100 text-yellow-700',
};

export default function AuditPage() {
  const [category, setCategory] = useState('');
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ['audit', category, status, search, page],
    queryFn: () =>
      getAuditEvents({
        ...(category ? { category } : {}),
        ...(status ? { status } : {}),
        ...(search ? { search } : {}),
        page,
        per_page: 50,
      }).then((r) => r.data),
    refetchInterval: 60_000,
  });

  return (
    <div className="max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Audit Log</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search events..."
            className="pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm w-full sm:w-64"
          />
        </div>
        <select
          value={category}
          onChange={(e) => { setCategory(e.target.value); setPage(1); }}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
        >
          <option value="">All categories</option>
          <option value="email">Email</option>
          <option value="social_media">Social Media</option>
          <option value="dashboard">Dashboard</option>
          <option value="approval">Approval</option>
          <option value="system">System</option>
        </select>
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
        >
          <option value="">All statuses</option>
          <option value="success">Success</option>
          <option value="error">Error</option>
        </select>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin h-8 w-8 border-4 border-brand-500 border-t-transparent rounded-full" />
        </div>
      )}

      {!isLoading && data?.events?.length === 0 && (
        <div className="text-center py-16">
          <ScrollText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No audit events found</p>
        </div>
      )}

      {/* Table (desktop) / Cards (mobile) */}
      {data?.events?.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          {/* Desktop table */}
          <div className="hidden sm:block overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-left">
                  <th className="px-4 py-3 font-medium text-gray-500">Time</th>
                  <th className="px-4 py-3 font-medium text-gray-500">Category</th>
                  <th className="px-4 py-3 font-medium text-gray-500">Action</th>
                  <th className="px-4 py-3 font-medium text-gray-500">Status</th>
                  <th className="px-4 py-3 font-medium text-gray-500">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.events.map((event: any, i: number) => (
                  <tr key={i} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                      {event.timestamp
                        ? format(new Date(event.timestamp), 'MMM d, HH:mm:ss')
                        : '-'}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded-full bg-gray-100 text-gray-700 text-xs">
                        {event.category}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-900">{event.action}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                        statusColors[event.status] || 'bg-gray-100 text-gray-600'
                      }`}>
                        {event.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-500 max-w-xs truncate">
                      {event.details ? JSON.stringify(event.details) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile card list */}
          <div className="sm:hidden divide-y divide-gray-100">
            {data.events.map((event: any, i: number) => (
              <div key={i} className="p-4 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded-full bg-gray-100 text-gray-700 text-xs">
                    {event.category}
                  </span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    statusColors[event.status] || 'bg-gray-100 text-gray-600'
                  }`}>
                    {event.status}
                  </span>
                </div>
                <p className="text-sm text-gray-900">{event.action}</p>
                <p className="text-xs text-gray-400">
                  {event.timestamp
                    ? format(new Date(event.timestamp), 'MMM d, HH:mm:ss')
                    : '-'}
                </p>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {data.pages > 1 && (
            <div className="flex flex-col sm:flex-row items-center justify-between px-4 py-3 gap-2 border-t border-gray-100">
              <span className="text-sm text-gray-500">
                Page {data.page} of {data.pages} ({data.total} events)
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="px-3 py-1 text-sm border rounded-lg disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                  disabled={page >= data.pages}
                  className="px-3 py-1 text-sm border rounded-lg disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
