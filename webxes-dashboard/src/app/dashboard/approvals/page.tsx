'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getApprovals, getApproval } from '@/lib/api';
import { FileText, Mail, Share2, CreditCard } from 'lucide-react';
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

export default function ApprovalsPage() {
  const [activeDomain, setActiveDomain] = useState('all');
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const [loadingItem, setLoadingItem] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['approvals', activeDomain],
    queryFn: () =>
      getApprovals(activeDomain !== 'all' ? { domain: activeDomain } : {}).then(
        (r) => r.data
      ),
    refetchInterval: 15_000,
  });

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
      <div className="flex gap-1 mb-6 bg-gray-100 rounded-lg p-1 w-fit">
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
          </button>
        ))}
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin h-8 w-8 border-4 border-brand-500 border-t-transparent rounded-full" />
        </div>
      )}

      {/* Empty state */}
      {!isLoading && data?.items?.length === 0 && (
        <div className="text-center py-16">
          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No pending approvals</p>
        </div>
      )}

      {/* Approval cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {data?.items?.map((item: any) => (
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
