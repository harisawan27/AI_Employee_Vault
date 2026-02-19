'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  CheckCircle,
  Inbox,
  ScrollText,
  Settings,
  LogOut,
  Bell,
  Share2,
  X,
} from 'lucide-react';
import { useNotificationStore } from '@/lib/useWebSocket';
import NotificationPanel from './NotificationPanel';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/dashboard/approvals', label: 'Approvals', icon: CheckCircle },
  { href: '/dashboard/social', label: 'Social Media', icon: Share2 },
  { href: '/dashboard/inbox', label: 'Inbox', icon: Inbox },
  { href: '/dashboard/audit', label: 'Audit Log', icon: ScrollText },
  { href: '/dashboard/settings', label: 'Settings', icon: Settings },
];

interface SidebarProps {
  approvalCount?: number;
  inboxCount?: number;
  mobileOpen?: boolean;
  onMobileClose?: () => void;
  onLogout: () => void;
}

export default function Sidebar({
  approvalCount = 0,
  inboxCount = 0,
  mobileOpen = false,
  onMobileClose,
  onLogout,
}: SidebarProps) {
  const pathname = usePathname();
  const { unreadCount, clearUnread, connected } = useNotificationStore();
  const [notifOpen, setNotifOpen] = useState(false);

  const getBadge = (href: string) => {
    if (href === '/dashboard/approvals' && approvalCount > 0) return approvalCount;
    if (href === '/dashboard/inbox' && inboxCount > 0) return inboxCount;
    return null;
  };

  const handleBellClick = () => {
    if (!notifOpen) clearUnread();
    setNotifOpen(!notifOpen);
  };

  const handleNavClick = () => {
    if (mobileOpen && onMobileClose) onMobileClose();
  };

  return (
    <>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onMobileClose}
        />
      )}

      <aside
        className={`fixed left-0 top-0 h-full bg-brand-900 text-white flex flex-col z-50 transition-all duration-300 ${
          mobileOpen
            ? 'w-64 translate-x-0'
            : 'lg:w-64 w-0 -translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Logo */}
        <div className="p-6 border-b border-white/10 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">WEBXES Tech</h1>
            <p className="text-xs text-blue-300 mt-1">AI Employee Dashboard</p>
          </div>
          {mobileOpen && (
            <button
              onClick={onMobileClose}
              className="p-1 hover:bg-white/10 rounded lg:hidden"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            const badge = getBadge(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={handleNavClick}
                className={`flex items-center gap-3 px-6 py-3 text-sm transition-colors relative ${
                  isActive
                    ? 'bg-white/10 text-white border-r-2 border-blue-400'
                    : 'text-blue-200 hover:bg-white/5 hover:text-white'
                }`}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                <span>{item.label}</span>
                {badge && (
                  <span className="ml-auto bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                    {badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Connection status */}
        <div className="px-6 py-2">
          <div className="flex items-center gap-2 text-xs text-blue-300">
            <span
              className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400' : 'bg-red-400'}`}
              title={connected ? 'Real-time connected' : 'Disconnected — retrying'}
            />
            <span>{connected ? 'Real-time connected' : 'Disconnected'}</span>
          </div>
        </div>

        {/* Notification bell */}
        <div className="px-6 py-3 border-t border-white/10">
          <button
            onClick={handleBellClick}
            className="flex items-center gap-3 text-blue-200 hover:text-white transition-colors w-full text-sm"
          >
            <div className="relative">
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </div>
            <span>Notifications</span>
          </button>
        </div>

        {/* Notification panel */}
        <NotificationPanel open={notifOpen} onClose={() => setNotifOpen(false)} />

        {/* Logout */}
        <div className="px-6 py-4 border-t border-white/10">
          <button
            onClick={onLogout}
            className="flex items-center gap-3 text-blue-200 hover:text-white transition-colors w-full text-sm"
          >
            <LogOut className="w-5 h-5" />
            <span>Logout</span>
          </button>
        </div>
      </aside>
    </>
  );
}
