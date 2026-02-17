'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getInbox, getInboxItem } from '@/lib/api';
import { Inbox, Mail, FileText, Briefcase, ChevronDown, ChevronUp } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

const typeIcons: Record<string, any> = {
  email: Mail,
  task: FileText,
  briefing: Briefcase,
};

const typeBadgeColors: Record<string, string> = {
  email: 'bg-blue-100 text-blue-700',
  task: 'bg-orange-100 text-orange-700',
  briefing: 'bg-purple-100 text-purple-700',
};

export default function InboxPage() {
  const [typeFilter, setTypeFilter] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [expandedContent, setExpandedContent] = useState<string>('');

  const { data, isLoading } = useQuery({
    queryKey: ['inbox', typeFilter],
    queryFn: () =>
      getInbox({ ...(typeFilter ? { type: typeFilter } : {}) }).then((r) => r.data),
    refetchInterval: 30_000,
  });

  const handleExpand = async (id: string) => {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }
    try {
      const res = await getInboxItem(id);
      setExpandedContent(res.data.content);
      setExpandedId(id);
    } catch {
      // ignore
    }
  };

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Inbox</h1>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm"
        >
          <option value="">All types</option>
          <option value="email">Email</option>
          <option value="task">Task</option>
          <option value="briefing">Briefing</option>
        </select>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin h-8 w-8 border-4 border-brand-500 border-t-transparent rounded-full" />
        </div>
      )}

      {!isLoading && data?.items?.length === 0 && (
        <div className="text-center py-16">
          <Inbox className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No items in inbox</p>
        </div>
      )}

      <div className="space-y-2">
        {data?.items?.map((item: any) => {
          const Icon = typeIcons[item.metadata?.type] || FileText;
          const badgeColor = typeBadgeColors[item.metadata?.type] || 'bg-gray-100 text-gray-600';
          const isExpanded = expandedId === item.id;

          return (
            <div key={item.id} className="bg-white rounded-xl shadow-sm border border-gray-100">
              <button
                onClick={() => handleExpand(item.id)}
                className="w-full flex items-center gap-4 p-4 text-left hover:bg-gray-50 transition"
              >
                <Icon className="w-5 h-5 text-gray-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">{item.filename}</p>
                  <p className="text-sm text-gray-500 truncate">{item.preview}</p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badgeColor}`}>
                  {item.metadata?.type || item.domain}
                </span>
                <span className="text-xs text-gray-400 flex-shrink-0">
                  {item.modified
                    ? formatDistanceToNow(new Date(item.modified * 1000), { addSuffix: true })
                    : ''}
                </span>
                {isExpanded ? (
                  <ChevronUp className="w-4 h-4 text-gray-400" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-gray-400" />
                )}
              </button>
              {isExpanded && (
                <div className="px-4 pb-4 border-t border-gray-100 pt-4">
                  <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
                    {expandedContent}
                  </pre>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
