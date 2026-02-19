'use client';

import { useState, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getApprovals, getApproval } from '@/lib/api';
import { FileText, Mail, Share2, CreditCard, Search, ArrowUpDown } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import ApprovalEditor from '@/components/ApprovalEditor';

const domainTabs = [
  { key: 'all', label: 'All' },
  { key: 'email', label: 'Email', icon: Mail },
  { key: 'social_media', label: 'Social Media', icon: Share2 },
  { key: 'payments', label: 'Payments', icon: CreditCard },
];

const domainColors: Record<string, string> = {
  email: 'border-l-blue-500',
  social_media: 'border-l-purple-500',
  payments: 'border-l-green-500',
  general: 'border-l-gray-400',
};

type SortOrder = 'newest' | 'oldest';

export default function ApprovalsPage() {
  const [activeDomain, setActiveDomain] = useState('all');
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const [loadingItem, setLoadingItem] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOrder, setSortOrder] = useState<SortOrder>('newest');
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['approvals', activeDomain],
    queryFn: () =>
      getApprovals(activeDomain !== 'all' ? { domain: activeDomain } : {}).then(
        (r) => r.data
      ),
    refetchInterval: 15_000,
  });

  // Count per domain
  const domainCounts = useMemo(() => {
    const items = data?.items || [];
    const counts: Record<string, number> = { all: items.length };
    items.forEach((item: any) => {
      counts[item.domain] = (counts[item.domain] || 0) + 1;
    });
    return counts;
  }, [data?.items]);

  // Filter + sort
  const displayItems = useMemo(() => {
    let items = data?.items || [];
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      items = items.filter(
        (item: any) =>
          item.filename?.toLowerCase().includes(q) ||
          item.preview?.toLowerCase().includes(q)
      );
    }
    if (sortOrder === 'oldest') {
      items = [...items].reverse();
    }
    return items;
  }, [data?.items, searchQuery, sortOrder]);

  const handleCardClick = async (item: any) => {
    setLoadingItem(item.id);
    try {
      const res = await getApproval(item.id);
      setSelectedItem(res.data);
    } catch {
      // ignore
    } finally {
      setLoadingItem(null);
    }
  };

  const handleAction = () => {
    queryClient.invalidateQueries({ queryKey: ['approvals'] });
    queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
  };

  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Approval Queue</h1>

      {/* Domain tabs */}
      <div className="flex gap-1 mb-4 bg-gray-100 rounded-lg p-1 w-fit max-w-full overflow-x-auto">
        {domainTabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveDomain(tab.key)}
            className={`flex items-center gap-2 px-4 py-2 text-sm rounded-md transition ${
              activeDomain === tab.key
                ? 'bg-white shadow-sm text-gray-900 font-medium'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.icon && <tab.icon className="w-4 h-4" />}
            {tab.label}
            {domainCounts[tab.key] !== undefined && (
              <span className="text-xs bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded-full ml-1">
                {domainCounts[tab.key]}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Search + sort bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 mb-6">
        <div className="relative flex-1 sm:max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search approvals..."
            className="pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm w-full focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none"
          />
        </div>
        <select
          value={sortOrder}
          onChange={(e) => setSortOrder(e.target.value as SortOrder)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
        >
          <option value="newest">Newest first</option>
          <option value="oldest">Oldest first</option>
        </select>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin h-8 w-8 border-4 border-brand-500 border-t-transparent rounded-full" />
        </div>
      )}

      {/* Empty state */}
      {!isLoading && displayItems.length === 0 && (
        <div className="text-center py-16">
          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">
            {searchQuery ? 'No approvals match your search' : 'No pending approvals'}
          </p>
        </div>
      )}

      {/* Approval cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {displayItems.map((item: any) => (
          <button
            key={item.id}
            onClick={() => handleCardClick(item)}
            disabled={loadingItem === item.id}
            className={`text-left bg-white rounded-xl shadow-sm border border-gray-100 border-l-4 ${
              domainColors[item.domain] || domainColors.general
            } p-5 hover:shadow-md transition cursor-pointer disabled:opacity-60`}
          >
            <div className="flex items-start justify-between mb-2">
              <h3 className="font-medium text-gray-900 truncate flex-1">{item.filename}</h3>
              <span className="text-xs text-gray-400 ml-2 flex-shrink-0">
                {item.modified
                  ? formatDistanceToNow(new Date(item.modified * 1000), { addSuffix: true })
                  : ''}
              </span>
            </div>
            <p className="text-sm text-gray-500 line-clamp-3">{item.preview}</p>
            <div className="mt-3 flex items-center gap-2">
              <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                {item.domain}
              </span>
              {item.metadata?.type && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-600">
                  {item.metadata.type}
                </span>
              )}
            </div>
            {loadingItem === item.id && (
              <div className="mt-2 flex justify-center">
                <div className="animate-spin h-4 w-4 border-2 border-brand-500 border-t-transparent rounded-full" />
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Editor modal */}
      {selectedItem && (
        <ApprovalEditor
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
          onAction={handleAction}
        />
      )}
    </div>
  );
}
