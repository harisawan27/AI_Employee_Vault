'use client';

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
} from 'lucide-react';
import { useNotificationStore } from '@/lib/useWebSocket';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/dashboard/approvals', label: 'Approvals', icon: CheckCircle },
  { href: '/dashboard/inbox', label: 'Inbox', icon: Inbox },
  { href: '/dashboard/audit', label: 'Audit Log', icon: ScrollText },
  { href: '/dashboard/settings', label: 'Settings', icon: Settings },
];

interface SidebarProps {
  approvalCount?: number;
  inboxCount?: number;
  onLogout: () => void;
}

export default function Sidebar({ approvalCount = 0, inboxCount = 0, onLogout }: SidebarProps) {
  const pathname = usePathname();
  const { unreadCount, clearUnread } = useNotificationStore();

  const getBadge = (href: string) => {
    if (href === '/dashboard/approvals' && approvalCount > 0) return approvalCount;
    if (href === '/dashboard/inbox' && inboxCount > 0) return inboxCount;
    return null;
  };

  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-brand-900 text-white flex flex-col z-50 lg:w-64 w-16 transition-all">
      {/* Logo */}
      <div className="p-6 border-b border-white/10">
        <h1 className="text-xl font-bold hidden lg:block">WEBXES Tech</h1>
        <p className="text-xs text-blue-300 mt-1 hidden lg:block">AI Employee Dashboard</p>
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
              className={`flex items-center gap-3 px-6 py-3 text-sm transition-colors relative ${
                isActive
                  ? 'bg-white/10 text-white border-r-2 border-blue-400'
                  : 'text-blue-200 hover:bg-white/5 hover:text-white'
              }`}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              <span className="hidden lg:inline">{item.label}</span>
              {badge && (
                <span className="ml-auto bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center hidden lg:flex">
                  {badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Notification bell */}
      <div className="px-6 py-3 border-t border-white/10">
        <button
          onClick={clearUnread}
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
          <span className="hidden lg:inline">Notifications</span>
        </button>
      </div>

      {/* Logout */}
      <div className="px-6 py-4 border-t border-white/10">
        <button
          onClick={onLogout}
          className="flex items-center gap-3 text-blue-200 hover:text-white transition-colors w-full text-sm"
        >
          <LogOut className="w-5 h-5" />
          <span className="hidden lg:inline">Logout</span>
        </button>
      </div>
    </aside>
  );
}
