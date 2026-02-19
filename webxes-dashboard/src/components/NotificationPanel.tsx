'use client';

import { useNotificationStore } from '@/lib/useWebSocket';
import { X, Bell, Trash2, FileText, Mail, Share2, CreditCard, Zap } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

const typeIcons: Record<string, any> = {
  approval: FileText,
  email: Mail,
  social: Share2,
  payment: CreditCard,
};

function getEventIcon(event: any) {
  const t = event.type?.toLowerCase() || '';
  if (t.includes('email') || t.includes('mail')) return Mail;
  if (t.includes('social')) return Share2;
  if (t.includes('approval')) return FileText;
  if (t.includes('payment')) return CreditCard;
  return Zap;
}

function getEventMessage(event: any): string {
  const file = event.file || event.path || '';
  const action = event.action || event.type || 'Event';
  if (file) return `${action}: ${file.split('/').pop()}`;
  return action;
}

interface NotificationPanelProps {
  open: boolean;
  onClose: () => void;
}

export default function NotificationPanel({ open, onClose }: NotificationPanelProps) {
  const { events, clearUnread, clearAll, removeEvent } = useNotificationStore();

  if (!open) return null;

  const handleClearAll = () => {
    clearAll();
    clearUnread();
  };

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-[60]" onClick={onClose} />

      {/* Panel */}
      <div className="fixed z-[70] max-h-[28rem] bg-white rounded-xl shadow-2xl border border-gray-200 flex flex-col animate-slide-in bottom-4 left-4 right-4 sm:right-auto sm:left-4 sm:w-80 lg:left-64 lg:bottom-16">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <Bell className="w-4 h-4 text-gray-500" />
            <span className="font-semibold text-sm">Notifications</span>
            {events.length > 0 && (
              <span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-full">
                {events.length}
              </span>
            )}
          </div>
          <div className="flex items-center gap-1">
            {events.length > 0 && (
              <button
                onClick={handleClearAll}
                className="text-xs text-gray-400 hover:text-red-500 px-2 py-1 rounded transition"
              >
                Clear All
              </button>
            )}
            <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded transition">
              <X className="w-4 h-4 text-gray-400" />
            </button>
          </div>
        </div>

        {/* Events list */}
        <div className="flex-1 overflow-y-auto">
          {events.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-gray-400">
              <Bell className="w-8 h-8 mb-2 opacity-50" />
              <p className="text-sm">No notifications yet</p>
            </div>
          )}

          {events.slice(0, 20).map((event, i) => {
            const Icon = getEventIcon(event);
            return (
              <div
                key={i}
                className="flex items-start gap-3 px-4 py-3 hover:bg-gray-50 transition border-b border-gray-50 last:border-0 group"
              >
                <div className="p-1.5 bg-brand-50 rounded-lg mt-0.5">
                  <Icon className="w-3.5 h-3.5 text-brand-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-800 truncate">{getEventMessage(event)}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {(event as any).timestamp
                      ? formatDistanceToNow(new Date((event as any).timestamp), { addSuffix: true })
                      : 'Just now'}
                  </p>
                </div>
                <button
                  onClick={() => removeEvent(i)}
                  className="p-1 opacity-0 group-hover:opacity-100 hover:bg-gray-200 rounded transition"
                >
                  <X className="w-3 h-3 text-gray-400" />
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}
