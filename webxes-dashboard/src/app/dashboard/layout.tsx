'use client';

import { useAuth } from '@/lib/useAuth';
import { useWebSocket } from '@/lib/useWebSocket';
import { useQuery } from '@tanstack/react-query';
import { getDashboardStats } from '@/lib/api';
import Sidebar from '@/components/Sidebar';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { authenticated, loading, logout } = useAuth();
  useWebSocket();

  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => getDashboardStats().then((r) => r.data),
    enabled: authenticated,
    refetchInterval: 30_000,
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin h-8 w-8 border-4 border-brand-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!authenticated) return null;

  return (
    <div className="flex min-h-screen">
      <Sidebar
        approvalCount={stats?.approvals_waiting || 0}
        inboxCount={stats?.pending_tasks || 0}
        onLogout={logout}
      />
      <main className="flex-1 lg:ml-64 ml-16 p-6 transition-all">
        {children}
      </main>
    </div>
  );
}
